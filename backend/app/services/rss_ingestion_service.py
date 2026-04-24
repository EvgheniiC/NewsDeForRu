from dataclasses import dataclass

import feedparser  # type: ignore[import-untyped]
import httpx

from app.core.config import settings
from app.repositories.news_repository import NewsRepository
from app.services.rss_entry_normalization import normalize_feedparser_entry
from app.services.rss_sources import DEFAULT_RSS_SOURCES


@dataclass(frozen=True)
class IngestionStats:
    fetched: int
    feeds_failed: int


class RSSIngestionService:
    def __init__(self, repository: NewsRepository) -> None:
        self.repository: NewsRepository = repository

    @staticmethod
    def _fetch_feed_body(client: httpx.Client, url: str) -> bytes | None:
        try:
            response: httpx.Response = client.get(url)
            response.raise_for_status()
            body: bytes = response.content
            if len(body) > settings.rss_max_response_bytes:
                return None
            return body
        except httpx.HTTPError:
            return None

    def run(self) -> IngestionStats:
        fetched: int = 0
        feeds_failed: int = 0
        timeout: httpx.Timeout = httpx.Timeout(settings.rss_fetch_timeout_seconds)
        headers: dict[str, str] = {"User-Agent": settings.rss_user_agent}

        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            for source in DEFAULT_RSS_SOURCES:
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
                    )
                    fetched += 1

        return IngestionStats(fetched=fetched, feeds_failed=feeds_failed)
