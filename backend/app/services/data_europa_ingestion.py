"""Fail-closed data.europa.eu Search API ingestion with distribution license checks."""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from app.core.config import Settings, settings
from app.core.http_tls import httpx_verify_arg
from app.repositories.news_repository import NewsRepository
from app.services.govdata_ingestion import is_text_resource
from app.services.http_fetch_limits import ResponseTooLargeError, read_http_body_with_limit
from app.services.official_data_ingestion import parse_dataset_codes
from app.services.open_license_gate import LicenseClassification, LicenseVerdict, classify_license
from app.services.rss_ingestion_service import IngestionStats

logger: logging.Logger = logging.getLogger(__name__)

# Volatile REST/API endpoints change on every fetch and must not create news revisions.
_API_URL_MARKERS: tuple[str, ...] = (
    "/rest/",
    "/api/",
    "gojsonapi",
    "jsonapi",
    "/wfs",
    "/wms",
    "service=wfs",
    "service=wms",
)


def data_europa_content_revision(dataset_id: str, distribution_id: str, body: bytes) -> str:
    digest: str = hashlib.sha256(body).hexdigest()
    return f"data_europa:{dataset_id}:{distribution_id}:{digest}"


def _as_mapping(value: object) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _localized_text(value: object, preferred: tuple[str, ...] = ("en", "de")) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, Mapping):
        for lang in preferred:
            raw: object = value.get(lang)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        for raw in value.values():
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, Mapping):
                label: object = item.get("label") or item.get("title")
                if isinstance(label, str) and label.strip():
                    lang: object = item.get("language") or item.get("lang")
                    if lang in preferred or not preferred:
                        return label.strip()
        for item in value:
            text: str = _localized_text(item, preferred=())
            if text:
                return text
    return ""


def _first_url(value: object) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return ""


def _format_id(value: object) -> str:
    if isinstance(value, Mapping):
        return str(value.get("id") or value.get("label") or "").strip()
    return str(value or "").strip()


def classify_distribution_license(
    dataset: Mapping[str, Any],
    distribution: Mapping[str, Any],
) -> LicenseClassification:
    """Prefer distribution licence/rights; fall back to dataset-level fields."""
    dist_license: object = distribution.get("license") or distribution.get("licence")
    dist_rights: object = distribution.get("rights")
    if isinstance(dist_license, Mapping):
        return classify_license(
            license_id=str(dist_license.get("id") or ""),
            license_title=str(dist_license.get("label") or dist_license.get("title") or ""),
            license_url=str(
                dist_license.get("resource") or dist_license.get("id") or ""
            ),
        )
    if isinstance(dist_license, str) and dist_license.strip():
        rights_title: str = _localized_text(dist_rights) if dist_rights else ""
        return classify_license(license_url=dist_license, license_title=rights_title or None)

    if dist_rights:
        return classify_license(license_title=_localized_text(dist_rights) or str(dist_rights))

    ds_license: object = dataset.get("license") or dataset.get("licence")
    ds_rights: object = dataset.get("rights")
    if isinstance(ds_license, Mapping):
        return classify_license(
            license_id=str(ds_license.get("id") or ""),
            license_title=str(ds_license.get("label") or ""),
            license_url=str(ds_license.get("resource") or ds_license.get("id") or ""),
        )
    if isinstance(ds_license, str) and ds_license.strip():
        return classify_license(license_url=ds_license)
    if ds_rights:
        return classify_license(license_title=_localized_text(ds_rights) or str(ds_rights))
    return classify_license()


def _looks_like_html(content_type: str, body: bytes) -> bool:
    ctype: str = content_type.lower()
    if "text/html" in ctype or "application/xhtml" in ctype:
        return True
    head: str = body[:200].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def is_stable_tabular_distribution(format_value: str | None, url: str) -> bool:
    """Accept static CSV/TSV/TXT tables; reject JSON APIs and catalogue service endpoints."""
    lower_url: str = url.strip().lower()
    if any(marker in lower_url for marker in _API_URL_MARKERS):
        return False
    path: str = urlparse(lower_url).path
    if path.endswith((".json", ".jsonld", ".geojson")):
        return False
    fmt: str = (format_value or "").strip().lower()
    if "json" in fmt and "csv" not in fmt:
        return False
    return is_text_resource(format_value, url)


def _distribution_access_url(distribution: Mapping[str, Any]) -> str:
    return _first_url(distribution.get("download_url") or distribution.get("access_url"))


def select_stable_distributions(
    distributions: list[Mapping[str, Any]],
    max_dists: int,
) -> list[Mapping[str, Any]]:
    """Prefer CSV downloaders; within the same tier prefer newer-looking filenames."""
    csv_tier: list[tuple[str, Mapping[str, Any]]] = []
    other_tier: list[tuple[str, Mapping[str, Any]]] = []
    for distribution in distributions:
        dist_id: str = str(distribution.get("id") or "").strip()
        access_url: str = _distribution_access_url(distribution)
        if not dist_id or not access_url:
            continue
        format_id: str = _format_id(distribution.get("format"))
        if not is_stable_tabular_distribution(format_id, access_url):
            continue
        path: str = urlparse(access_url).path.lower()
        fmt: str = format_id.lower()
        entry: tuple[str, Mapping[str, Any]] = (path, distribution)
        if path.endswith(".csv") or "csv" in fmt:
            csv_tier.append(entry)
        else:
            other_tier.append(entry)

    csv_tier.sort(key=lambda item: item[0], reverse=True)
    other_tier.sort(key=lambda item: item[0], reverse=True)

    selected: list[Mapping[str, Any]] = []
    seen_urls: set[str] = set()
    for _path, distribution in csv_tier + other_tier:
        if len(selected) >= max_dists:
            break
        access_url = _distribution_access_url(distribution)
        if access_url in seen_urls:
            continue
        seen_urls.add(access_url)
        selected.append(distribution)
    return selected


class DataEuropaIngestionService:
    def __init__(self, repository: NewsRepository, app_settings: Settings | None = None) -> None:
        self._repository: NewsRepository = repository
        self._settings: Settings = app_settings if app_settings is not None else settings

    def run(self) -> IngestionStats:
        dataset_ids: tuple[str, ...] = parse_dataset_codes(self._settings.data_europa_dataset_ids)
        if not dataset_ids:
            return IngestionStats(fetched=0, feeds_failed=0)

        selected: tuple[str, ...] = dataset_ids[: self._settings.data_europa_max_datasets_per_run]
        source = self._repository.upsert_source(
            source_key="data_europa",
            name="data.europa.eu catalogue",
            rss_url=self._settings.data_europa_search_base_url,
            default_licence=None,
            default_licence_url=None,
            copyright_holder=None,
            original_language="en",
            changes_notice=(
                "Неофициальная русская интерпретация и AI-суммаризация; "
                "данные загружены у исходного publisher через каталог data.europa.eu, "
                "портал не является правообладателем."
            ),
            rights_verified=False,
            text_only=True,
        )

        fetched: int = 0
        failed: int = 0
        delay: float = self._settings.data_europa_request_delay_seconds
        max_bytes: int = self._settings.data_europa_max_response_bytes
        max_dists: int = self._settings.data_europa_max_distributions_per_dataset
        base: str = self._settings.data_europa_search_base_url.rstrip("/")

        with httpx.Client(
            timeout=self._settings.official_data_fetch_timeout_seconds,
            verify=httpx_verify_arg(self._settings),
            follow_redirects=True,
            headers={"Accept": "application/json"},
        ) as client:
            for index, dataset_id in enumerate(selected):
                if index > 0 and delay > 0:
                    time.sleep(delay)
                try:
                    dataset = self._fetch_dataset(client, base, dataset_id)
                except (httpx.HTTPError, ValueError, KeyError):
                    logger.warning(
                        "data.europa.eu dataset fetch failed id=%s",
                        dataset_id,
                        exc_info=True,
                    )
                    failed += 1
                    continue

                title: str = _localized_text(dataset.get("title")) or dataset_id
                dataset_uri: str = f"https://data.europa.eu/data/datasets/{dataset_id}"
                publisher: str = self._publisher_name(dataset.get("publisher"))

                distributions_raw: object = dataset.get("distributions")
                distributions: list[Mapping[str, Any]] = (
                    [item for item in distributions_raw if isinstance(item, Mapping)]
                    if isinstance(distributions_raw, list)
                    else []
                )
                if not distributions:
                    logger.warning("data.europa.eu dataset has no distributions id=%s", dataset_id)
                    failed += 1
                    continue

                selected_distributions: list[Mapping[str, Any]] = select_stable_distributions(
                    distributions,
                    max_dists,
                )
                if not selected_distributions:
                    logger.warning(
                        "data.europa.eu dataset has no stable tabular distributions id=%s",
                        dataset_id,
                    )
                    failed += 1
                    continue

                for distribution in selected_distributions:
                    dist_id: str = str(distribution.get("id") or "").strip()
                    access_url: str = _distribution_access_url(distribution)
                    format_id: str = _format_id(distribution.get("format"))

                    classification: LicenseClassification = classify_distribution_license(
                        dataset,
                        distribution,
                    )
                    if classification.verdict == LicenseVerdict.BLOCKED:
                        logger.warning(
                            "data.europa.eu distribution blocked by license dataset=%s dist=%s license=%s",
                            dataset_id,
                            dist_id,
                            classification.canonical_name,
                        )
                        continue

                    if delay > 0:
                        time.sleep(delay)
                    try:
                        with client.stream("GET", access_url) as response:
                            response.raise_for_status()
                            body: bytes = read_http_body_with_limit(response, max_bytes)
                            content_type: str = response.headers.get("Content-Type", "")
                    except ResponseTooLargeError:
                        logger.warning(
                            "data.europa.eu distribution too large dataset=%s dist=%s limit=%s",
                            dataset_id,
                            dist_id,
                            max_bytes,
                        )
                        failed += 1
                        continue
                    except (httpx.HTTPError, ValueError):
                        logger.warning(
                            "data.europa.eu distribution fetch failed dataset=%s dist=%s",
                            dataset_id,
                            dist_id,
                            exc_info=True,
                        )
                        failed += 1
                        continue

                    if _looks_like_html(content_type, body):
                        logger.warning(
                            "data.europa.eu distribution looks like HTML page dataset=%s dist=%s format=%s",
                            dataset_id,
                            dist_id,
                            format_id,
                        )
                        failed += 1
                        continue

                    revision: str = data_europa_content_revision(dataset_id, dist_id, body)
                    if self._repository.has_raw_item(source.id, revision):
                        continue

                    rights_verified: bool = classification.verdict == LicenseVerdict.ALLOWED
                    licence_name: str = (
                        classification.canonical_name
                        if rights_verified
                        else (classification.canonical_name or "unknown")
                    )
                    licence_url: str = classification.licence_url if rights_verified else ""
                    text_body: str = body.decode("utf-8", errors="replace")
                    if len(text_body) > self._settings.official_data_max_summary_chars:
                        text_body = f"{text_body[: self._settings.official_data_max_summary_chars]}…"

                    summary: str = (
                        f"Dataset: {title}\n"
                        f"Dataset URI: {dataset_uri}\n"
                        f"Distribution URI: {access_url}\n"
                        f"Publisher: {publisher}\n"
                        f"License: {licence_name or 'unknown'}\n"
                        f"License URI: {classification.licence_url or 'n/a'}\n"
                        f"Catalogue: data.europa.eu (discovery only)\n\n"
                        f"{text_body}"
                    )
                    self._repository.create_raw_item(
                        source_id=source.id,
                        guid=revision,
                        title=f"data.europa.eu: {title}",
                        summary=summary,
                        url=access_url,
                        published_at=datetime.utcnow(),
                        original_language="en",
                        licence=licence_name or None,
                        licence_url=licence_url or None,
                        copyright_holder=publisher,
                        changes_notice=source.changes_notice,
                        source_revision=revision,
                        rights_verified=rights_verified,
                    )
                    fetched += 1
        return IngestionStats(fetched=fetched, feeds_failed=failed)

    def _fetch_dataset(
        self,
        client: httpx.Client,
        base: str,
        dataset_id: str,
    ) -> Mapping[str, Any]:
        encoded_id: str = quote(dataset_id, safe="")
        response: httpx.Response = client.get(f"{base}/datasets/{encoded_id}")
        response.raise_for_status()
        payload: object = response.json()
        if not isinstance(payload, Mapping):
            raise ValueError(f"dataset response is not an object for {dataset_id}")
        result: object = payload.get("result")
        mapping = _as_mapping(result)
        if mapping is None:
            raise ValueError(f"dataset missing result for {dataset_id}")
        return mapping

    @staticmethod
    def _publisher_name(raw: object) -> str:
        publisher_obj = _as_mapping(raw)
        if publisher_obj is None:
            return "Unknown publisher"
        name: object = publisher_obj.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
        localized: str = _localized_text(name)
        if localized:
            return localized
        resource: object = publisher_obj.get("resource")
        if isinstance(resource, str) and resource.strip():
            return resource.strip()
        return "Unknown publisher"
