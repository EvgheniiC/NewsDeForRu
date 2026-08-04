"""Fail-closed GovData (CKAN) ingestion with per-resource license checks."""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import Settings, settings
from app.core.http_tls import httpx_verify_arg
from app.repositories.news_repository import NewsRepository
from app.services.http_fetch_limits import ResponseTooLargeError, read_http_body_with_limit
from app.services.official_data_ingestion import parse_dataset_codes
from app.services.open_license_gate import LicenseClassification, LicenseVerdict, classify_license
from app.services.rss_ingestion_service import IngestionStats
from app.services.tabular_digest import build_open_dataset_summary

logger: logging.Logger = logging.getLogger(__name__)

_TEXT_FORMATS: frozenset[str] = frozenset(
    {
        "csv",
        "json",
        "tsv",
        "txt",
        "text/csv",
        "text/plain",
        "text/json",
        "application/json",
        "text/csv+extended",
    }
)

_BLOCKED_FORMAT_MARKERS: frozenset[str] = frozenset(
    {
        "pdf",
        "zip",
        "rar",
        "7z",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "svg",
        "mp4",
        "mp3",
        "avi",
        "mov",
        "html",
        "htm",
        "xlsx",
        "xls",
        "doc",
        "docx",
        "ppt",
        "pptx",
        "geojson",  # often large; keep MVP to tabular text
        "wms",
        "wfs",
        "api",
        "app",
    }
)


def is_text_resource(format_value: str | None, url: str) -> bool:
    fmt: str = (format_value or "").strip().lower()
    if fmt in _TEXT_FORMATS:
        return True
    if any(marker in fmt for marker in _BLOCKED_FORMAT_MARKERS):
        return False
    path: str = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in (".csv", ".json", ".tsv", ".txt"))


def govdata_content_revision(package_id: str, resource_id: str, body: bytes) -> str:
    digest: str = hashlib.sha256(body).hexdigest()
    return f"govdata:{package_id}:{resource_id}:{digest}"


def _as_mapping(value: object) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _string_field(data: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        raw: object = data.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return ""


class GovDataIngestionService:
    def __init__(self, repository: NewsRepository, app_settings: Settings | None = None) -> None:
        self._repository: NewsRepository = repository
        self._settings: Settings = app_settings if app_settings is not None else settings

    def run(self) -> IngestionStats:
        package_ids: tuple[str, ...] = parse_dataset_codes(self._settings.govdata_package_ids)
        if not package_ids:
            return IngestionStats(fetched=0, feeds_failed=0)

        max_packages: int = self._settings.govdata_max_packages_per_run
        selected: tuple[str, ...] = package_ids[:max_packages]
        source = self._repository.upsert_source(
            source_key="govdata",
            name="GovData catalogue",
            rss_url=self._settings.govdata_ckan_base_url,
            default_licence=None,
            default_licence_url=None,
            copyright_holder=None,
            original_language="de",
            changes_notice=(
                "Неофициальная русская интерпретация и AI-суммаризация; "
                "данные загружены у исходного поставщика через каталог GovData, "
                "GovData не является правообладателем."
            ),
            rights_verified=False,
            text_only=True,
        )

        fetched: int = 0
        failed: int = 0
        delay: float = self._settings.govdata_request_delay_seconds
        max_bytes: int = self._settings.govdata_max_response_bytes
        base: str = self._settings.govdata_ckan_base_url.rstrip("/")

        with httpx.Client(
            timeout=self._settings.official_data_fetch_timeout_seconds,
            verify=httpx_verify_arg(self._settings),
            follow_redirects=True,
        ) as client:
            for index, package_id in enumerate(selected):
                if index > 0 and delay > 0:
                    time.sleep(delay)
                try:
                    package = self._fetch_package(client, base, package_id)
                except (httpx.HTTPError, ValueError, KeyError):
                    logger.warning("GovData package_show failed id=%s", package_id, exc_info=True)
                    failed += 1
                    continue

                pkg_name: str = _string_field(package, "name", "id") or package_id
                pkg_title: str = _string_field(package, "title") or pkg_name
                dataset_uri: str = f"https://www.govdata.de/daten/{pkg_name}"
                organization = _as_mapping(package.get("organization"))
                publisher: str = (
                    _string_field(organization, "title", "name") if organization else ""
                ) or "Unknown publisher"

                resources_raw: object = package.get("resources")
                resources: list[Mapping[str, Any]] = (
                    [item for item in resources_raw if isinstance(item, Mapping)]
                    if isinstance(resources_raw, list)
                    else []
                )
                if not resources:
                    logger.warning("GovData package has no resources id=%s", package_id)
                    failed += 1
                    continue

                for resource in resources:
                    resource_id: str = _string_field(resource, "id")
                    resource_url: str = _string_field(resource, "url")
                    if not resource_id or not resource_url:
                        continue
                    if not is_text_resource(_string_field(resource, "format"), resource_url):
                        logger.info(
                            "GovData resource skipped (non-text) package=%s resource=%s format=%s",
                            pkg_name,
                            resource_id,
                            _string_field(resource, "format"),
                        )
                        continue

                    classification: LicenseClassification = self._classify_resource_license(
                        package,
                        resource,
                    )
                    if classification.verdict == LicenseVerdict.BLOCKED:
                        logger.warning(
                            "GovData resource blocked by license package=%s resource=%s license=%s",
                            pkg_name,
                            resource_id,
                            classification.canonical_name,
                        )
                        continue

                    if delay > 0:
                        time.sleep(delay)
                    try:
                        with client.stream("GET", resource_url) as response:
                            response.raise_for_status()
                            body: bytes = read_http_body_with_limit(response, max_bytes)
                    except ResponseTooLargeError:
                        logger.warning(
                            "GovData resource too large package=%s resource=%s limit=%s",
                            pkg_name,
                            resource_id,
                            max_bytes,
                        )
                        failed += 1
                        continue
                    except (httpx.HTTPError, ValueError):
                        logger.warning(
                            "GovData resource fetch failed package=%s resource=%s",
                            pkg_name,
                            resource_id,
                            exc_info=True,
                        )
                        failed += 1
                        continue

                    revision: str = govdata_content_revision(pkg_name, resource_id, body)
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
                    summary: str = build_open_dataset_summary(
                        title=pkg_title,
                        dataset_uri=dataset_uri,
                        resource_uri=resource_url,
                        publisher=publisher,
                        licence_name=licence_name or "unknown",
                        licence_uri=classification.licence_url or "n/a",
                        body_text=text_body,
                        max_body_chars=self._settings.official_data_max_summary_chars,
                    )
                    self._repository.create_raw_item(
                        source_id=source.id,
                        guid=revision,
                        title=f"GovData: {pkg_title}",
                        summary=summary,
                        url=resource_url,
                        published_at=datetime.utcnow(),
                        original_language="de",
                        licence=licence_name or None,
                        licence_url=licence_url or None,
                        copyright_holder=publisher,
                        changes_notice=source.changes_notice,
                        source_revision=revision,
                        rights_verified=rights_verified,
                    )
                    fetched += 1
        return IngestionStats(fetched=fetched, feeds_failed=failed)

    def _fetch_package(
        self,
        client: httpx.Client,
        base: str,
        package_id: str,
    ) -> Mapping[str, Any]:
        response: httpx.Response = client.get(
            f"{base}/package_show",
            params={"id": package_id},
        )
        response.raise_for_status()
        payload: object = response.json()
        if not isinstance(payload, Mapping) or not payload.get("success"):
            raise ValueError(f"package_show unsuccessful for {package_id}")
        result: object = payload.get("result")
        mapping = _as_mapping(result)
        if mapping is None:
            raise ValueError(f"package_show missing result for {package_id}")
        return mapping

    def _classify_resource_license(
        self,
        package: Mapping[str, Any],
        resource: Mapping[str, Any],
    ) -> LicenseClassification:
        resource_license: str = _string_field(resource, "license", "license_url", "licence")
        package_license_id: str = _string_field(package, "license_id")
        package_license_title: str = _string_field(package, "license_title")
        package_license_url: str = _string_field(package, "license_url")
        # Prefer resource-level licence; fall back to package fields when empty.
        if resource_license:
            return classify_license(license_url=resource_license)
        return classify_license(
            license_id=package_license_id or None,
            license_title=package_license_title or None,
            license_url=package_license_url or None,
        )
