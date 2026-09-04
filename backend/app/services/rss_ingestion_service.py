import logging
import time
from dataclasses import dataclass

import feedparser  # type: ignore[import-untyped]
import httpx

from app.core.config import settings
from app.core.http_tls import httpx_verify_arg
from app.repositories.news_repository import NewsRepository
from app.services.rss_entry_normalization import normalize_feedparser_entry
from app.services.rss_sources import RSSSource, enabled_rss_sources

logger: logging.Logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionStats:
    fetched: int
    feeds_failed: int


class RSSIngestionService:
    def __init__(self, repository: NewsRepository) -> None:
        self.repository: NewsRepository = repository

    @staticmethod
    def _fetch_feed_body(client: httpx.Client, url: str) -> bytes | None:
        max_attempts: int = max(1, settings.rss_feed_max_attempts)
        base_delay: float = max(0.0, settings.rss_feed_retry_base_delay_seconds)
        last_reason: str = ""
        for attempt in range(max_attempts):
            try:
                response: httpx.Response = client.get(url)
                response.raise_for_status()
                body: bytes = response.content
                if len(body) > settings.rss_max_response_bytes:
                    logger.warning(
                        "RSS response too large (url=%s, bytes=%s max=%s)",
                        url,
                        len(body),
                        settings.rss_max_response_bytes,
                    )
                    return None
                return body
            except httpx.HTTPError as e:
                last_reason = repr(e)
                if attempt < max_attempts - 1 and base_delay > 0:
                    time.sleep(base_delay * (2**attempt))
        logger.warning("RSS fetch failed after %s attempts (url=%s): %s", max_attempts, url, last_reason)
        return None

    def run(self) -> IngestionStats:
        fetched: int = 0
        feeds_failed: int = 0
        sources: tuple[RSSSource, ...] = enabled_rss_sources(
            settings.rss_enabled_source_keys,
            allow_unverified=settings.rss_allow_unverified_catalog_sources,
        )
        if not sources:
            logger.warning(
                "RSS ingestion skipped: RSS_ENABLED_SOURCE_KEYS has no approved source keys"
            )
            return IngestionStats(fetched=0, feeds_failed=0)
        timeout: httpx.Timeout = httpx.Timeout(settings.rss_fetch_timeout_seconds)
        headers: dict[str, str] = {"User-Agent": settings.rss_user_agent}

        with httpx.Client(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            verify=httpx_verify_arg(settings),
        ) as client:
            for source in sources:
                body: bytes | None = self._fetch_feed_body(client, source.url)
                if body is None:
                    feeds_failed += 1
                    continue

                parsed = feedparser.parse(body)
                if not parsed.entries:
                    feeds_failed += 1
                    continue

                source_record = self.repository.upsert_source(
                    source_key=source.key,
                    name=source.name,
                    rss_url=source.url,
                    default_licence=source.licence,
                    default_licence_url=source.licence_url,
                    copyright_holder=source.copyright_holder,
                    original_language=source.original_language,
                    changes_notice=source.changes_notice,
                    rights_verified=source.rights_verified,
                    text_only=source.text_only,
                )
                for entry in parsed.entries[: settings.rss_fetch_limit]:
                    normalized = normalize_feedparser_entry(entry)
                    if normalized is None:
                        continue
                    if self.repository.has_raw_item(source_id=source_record.id, guid=normalized.guid):
                        continue
                    self.repository.create_raw_item(
                        source_id=source_record.id,
                        guid=normalized.guid,
                        title=normalized.title,
                        summary=normalized.summary,
                        url=normalized.url,
                        published_at=normalized.published_at,
                        image_url=None if source.text_only else normalized.image_url,
                        original_language=source.original_language,
                        licence=source.licence,
                        licence_url=source.licence_url,
                        copyright_holder=source.copyright_holder,
                        changes_notice=source.changes_notice,
                        source_revision=normalized.guid,
                        rights_verified=source.rights_verified,
                    )
                    fetched += 1

        return IngestionStats(fetched=fetched, feeds_failed=feeds_failed)
