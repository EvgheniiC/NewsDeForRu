"""Fail-closed ingestion for official Destatis GENESIS and Eurostat datasets."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

import httpx

from app.core.config import Settings, settings
from app.core.http_tls import httpx_verify_arg
from app.repositories.news_repository import NewsRepository
from app.services.rss_ingestion_service import IngestionStats

logger: logging.Logger = logging.getLogger(__name__)

# Known table codes → short German labels for titles / LLM context.
GENESIS_DATASET_LABELS: dict[str, str] = {
    "61111-0002": "Verbraucherpreisindex Deutschland (Monate)",
    "12411-0001": "Bevölkerung Deutschland",
}

# Envelope keys that change between identical GENESIS data responses.
_GENESIS_VOLATILE_KEYS: frozenset[str] = frozenset(
    {"Ident", "Status", "Parameter", "Copyright"}
)

_GENESIS_VOLATILE_LINE_MARKERS: tuple[str, ...] = (
    "erstellt am",
    "erstellungszeit",
    "copyright",
    "©",
    "stand:",
    "retrieved",
    "abrufdatum",
    "generiert",
    "www.destatis.de",
    "genesis-online",
)

# Prefer hashing only statistical rows; header/meta lines often include fetch time.
_GENESIS_DATA_LINE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    r"\d{4}"
    r"|"
    r"\d{1,2}\.\d{1,2}\.\d{4}"
    r"|"
    r"\d{4}-\d{2}"
    r")"
)

_GENESIS_UPDATE_KEYS: tuple[str, ...] = ("Updated", "LastUpdate", "LatestUpdate")


class IngestionProvider(Protocol):
    def run(self) -> IngestionStats: ...


def parse_dataset_codes(raw: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(code.strip() for code in raw.split(",") if code.strip()))


def _payload_text(payload: object, max_chars: int) -> str:
    text: str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return text if len(text) <= max_chars else f"{text[:max_chars]}…"


def normalize_genesis_content(content: object) -> object:
    """Strip fetch-time metadata so identical tables hash identically."""
    if isinstance(content, Mapping):
        return {
            key: normalize_genesis_content(value) if key == "Content" else value
            for key, value in content.items()
            if key not in _GENESIS_VOLATILE_KEYS
        }
    if not isinstance(content, str):
        return content

    text: str = content.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = [line.strip() for line in text.split("\n") if line.strip()]
    data_lines: list[str] = [line for line in lines if _GENESIS_DATA_LINE_RE.match(line)]
    if data_lines:
        return "\n".join(data_lines)

    filtered: list[str] = []
    for line in lines:
        lower: str = line.lower()
        if any(marker in lower for marker in _GENESIS_VOLATILE_LINE_MARKERS):
            continue
        filtered.append(line)
    return "\n".join(filtered)


def genesis_stable_content(payload: object) -> object:
    """Return only the data-bearing part of a GENESIS envelope for revision hashing."""
    if not isinstance(payload, Mapping):
        return normalize_genesis_content(payload)
    obj: object = payload.get("Object")
    if isinstance(obj, Mapping):
        content: object = obj.get("Content")
        if content is not None:
            return normalize_genesis_content(content)
        return normalize_genesis_content(dict(obj))
    stable: dict[str, object] = {
        key: value for key, value in payload.items() if key not in _GENESIS_VOLATILE_KEYS
    }
    return normalize_genesis_content(stable if stable else payload)


def _payload_revision(code: str, payload: object) -> str:
    body: str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest: str = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"{code}:{digest}"


def genesis_payload_revision(code: str, payload: object) -> str:
    return _payload_revision(code, genesis_stable_content(payload))


def genesis_item_revision(code: str, payload: object, update_token: str | None) -> str:
    """Prefer official table update stamp; fall back to normalized content hash."""
    if update_token:
        return f"{code}:upd:{update_token}"
    return genesis_payload_revision(code, payload)


def extract_genesis_update_token(payload: object) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    obj: object = payload.get("Object")
    if not isinstance(obj, Mapping):
        return None
    for key in _GENESIS_UPDATE_KEYS:
        value: object = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _genesis_item_title(code: str) -> str:
    label: str = GENESIS_DATASET_LABELS.get(code, f"Datensatz {code}")
    return f"Destatis GENESIS: {label}"


def _genesis_item_summary(code: str, payload: object, max_chars: int) -> str:
    label: str = GENESIS_DATASET_LABELS.get(code, code)
    raw_content: object | None = None
    if isinstance(payload, Mapping):
        obj: object = payload.get("Object")
        if isinstance(obj, Mapping):
            raw_content = obj.get("Content")
    if isinstance(raw_content, str) and raw_content.strip():
        body: str = raw_content if len(raw_content) <= max_chars else f"{raw_content[:max_chars]}…"
    else:
        body = _payload_text(genesis_stable_content(payload), max_chars)
    return f"{label} ({code})\n{body}"


class GenesisIngestionService:
    def __init__(self, repository: NewsRepository, app_settings: Settings | None = None) -> None:
        self._repository: NewsRepository = repository
        self._settings: Settings = app_settings if app_settings is not None else settings

    def run(self) -> IngestionStats:
        codes: tuple[str, ...] = parse_dataset_codes(self._settings.genesis_dataset_codes)
        token: str = self._settings.genesis_api_token.strip()
        if not codes:
            return IngestionStats(fetched=0, feeds_failed=0)
        if not token:
            logger.warning("GENESIS ingestion skipped: GENESIS_API_TOKEN is empty")
            return IngestionStats(fetched=0, feeds_failed=len(codes))

        source = self._repository.upsert_source(
            source_key="destatis_genesis",
            name="Destatis GENESIS-Online",
            rss_url=self._settings.genesis_base_url,
            default_licence="Datenlizenz Deutschland – Namensnennung – Version 2.0",
            default_licence_url=(
                "https://www.destatis.de/DE/Service/Impressum/copyright-genesis-online.html"
            ),
            copyright_holder="Statistisches Bundesamt (Destatis)",
            original_language="de",
            changes_notice=(
                "Неофициальная русская интерпретация и AI-суммаризация; "
                "данные обработаны и изменены."
            ),
            rights_verified=True,
            text_only=True,
        )
        fetched: int = 0
        failed: int = 0
        headers: dict[str, str] = {"username": token, "password": ""}
        base_url: str = self._settings.genesis_base_url.rstrip("/")
        data_endpoint: str = f"{base_url}/data/table"
        meta_endpoint: str = f"{base_url}/metadata/table"
        with httpx.Client(
            timeout=self._settings.official_data_fetch_timeout_seconds,
            verify=httpx_verify_arg(self._settings),
            headers=headers,
            follow_redirects=True,
        ) as client:
            for code in codes:
                update_token: str | None = None
                try:
                    meta_response: httpx.Response = client.post(
                        meta_endpoint,
                        data={"name": code, "area": "all"},
                    )
                    meta_response.raise_for_status()
                    update_token = extract_genesis_update_token(meta_response.json())
                except (httpx.HTTPError, ValueError):
                    logger.info(
                        "GENESIS metadata unavailable code=%s; falling back to content hash",
                        code,
                    )

                try:
                    response: httpx.Response = client.post(
                        data_endpoint,
                        data={"name": code, "area": "all", "compress": "false"},
                    )
                    response.raise_for_status()
                    payload: object = response.json()
                except (httpx.HTTPError, ValueError):
                    logger.warning("GENESIS dataset fetch failed code=%s", code, exc_info=True)
                    failed += 1
                    continue

                content_revision: str = genesis_payload_revision(code, payload)
                revision: str = genesis_item_revision(code, payload, update_token)
                if self._should_skip_genesis_item(
                    source_id=source.id,
                    code=code,
                    revision=revision,
                    content_revision=content_revision,
                ):
                    continue
                self._repository.create_raw_item(
                    source_id=source.id,
                    guid=revision,
                    title=_genesis_item_title(code),
                    summary=_genesis_item_summary(
                        code,
                        payload,
                        self._settings.official_data_max_summary_chars,
                    ),
                    url=f"https://genesis.destatis.de/datenbank/online/statistic/{code}",
                    published_at=datetime.utcnow(),
                    original_language="de",
                    licence=source.default_licence,
                    licence_url=source.default_licence_url,
                    copyright_holder=source.copyright_holder,
                    changes_notice=source.changes_notice,
                    source_revision=content_revision,
                    rights_verified=source.rights_verified,
                )
                fetched += 1
        return IngestionStats(fetched=fetched, feeds_failed=failed)

    def _should_skip_genesis_item(
        self,
        *,
        source_id: int,
        code: str,
        revision: str,
        content_revision: str,
    ) -> bool:
        candidates: set[str] = {revision, content_revision}
        for key in candidates:
            if self._repository.has_raw_item(source_id, key):
                return True
        latest = self._repository.find_latest_raw_item_for_guid_prefix(
            source_id,
            f"{code}:",
        )
        if latest is None:
            return False
        if latest.guid in candidates:
            return True
        if latest.source_revision and latest.source_revision in candidates:
            return True
        return False


class EurostatIngestionService:
    def __init__(self, repository: NewsRepository, app_settings: Settings | None = None) -> None:
        self._repository: NewsRepository = repository
        self._settings: Settings = app_settings if app_settings is not None else settings

    def run(self) -> IngestionStats:
        codes: tuple[str, ...] = parse_dataset_codes(self._settings.eurostat_dataset_codes)
        if not codes:
            return IngestionStats(fetched=0, feeds_failed=0)

        source = self._repository.upsert_source(
            source_key="eurostat",
            name="Eurostat",
            rss_url=self._settings.eurostat_base_url,
            default_licence="Eurostat reuse policy",
            default_licence_url="https://ec.europa.eu/eurostat/en/help/copyright-notice",
            copyright_holder="European Union",
            original_language="en",
            changes_notice=(
                "Неофициальная русская интерпретация и AI-суммаризация; "
                "за перевод отвечает приложение, при расхождениях действует оригинал."
            ),
            rights_verified=True,
            text_only=True,
        )
        fetched: int = 0
        failed: int = 0
        with httpx.Client(
            timeout=self._settings.official_data_fetch_timeout_seconds,
            verify=httpx_verify_arg(self._settings),
            follow_redirects=True,
        ) as client:
            # Eurostat asks clients to perform extraction calls sequentially.
            for code in codes:
                endpoint: str = f"{self._settings.eurostat_base_url.rstrip('/')}/{code}"
                try:
                    response: httpx.Response = client.get(endpoint)
                    response.raise_for_status()
                    payload: object = response.json()
                except (httpx.HTTPError, ValueError):
                    logger.warning("Eurostat dataset fetch failed code=%s", code, exc_info=True)
                    failed += 1
                    continue
                revision: str = _payload_revision(code, payload)
                if self._repository.has_raw_item(source.id, revision):
                    continue
                label: str = code
                if isinstance(payload, Mapping):
                    raw_label: object = payload.get("label")
                    if isinstance(raw_label, str) and raw_label.strip():
                        label = raw_label.strip()
                self._repository.create_raw_item(
                    source_id=source.id,
                    guid=revision,
                    title=f"Eurostat: {label}",
                    summary=_payload_text(payload, self._settings.official_data_max_summary_chars),
                    url=f"https://ec.europa.eu/eurostat/databrowser/view/{code}/default/table",
                    published_at=datetime.utcnow(),
                    original_language="en",
                    licence=source.default_licence,
                    licence_url=source.default_licence_url,
                    copyright_holder=source.copyright_holder,
                    changes_notice=source.changes_notice,
                    source_revision=revision,
                    rights_verified=source.rights_verified,
                )
                fetched += 1
        return IngestionStats(fetched=fetched, feeds_failed=failed)
