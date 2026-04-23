from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser  # type: ignore[import-untyped]

from app.core.config import settings
from app.repositories.news_repository import NewsRepository
from app.services.rss_sources import DEFAULT_RSS_SOURCES


@dataclass(frozen=True)
class IngestionStats:
    fetched: int


class RSSIngestionService:
    def __init__(self, repository: NewsRepository) -> None:
        self.repository: NewsRepository = repository

    @staticmethod
    def _parse_published(raw_value: str | None) -> datetime:
        if not raw_value:
            return datetime.now(timezone.utc)
        try:
            return parsedate_to_datetime(raw_value)
        except (TypeError, ValueError):
            return datetime.now(timezone.utc)

    def run(self) -> IngestionStats:
        fetched: int = 0
        for source in DEFAULT_RSS_SOURCES:
            source_record = self.repository.get_or_create_source(name=source.name, rss_url=source.url)
            parsed_feed = feedparser.parse(source.url)
            entries: list[dict[str, str]] = list(parsed_feed.entries[: settings.rss_fetch_limit])
            for entry in entries:
                guid: str = str(entry.get("id") or entry.get("link") or entry.get("title") or "")
                if not guid:
                    continue
                if self.repository.has_raw_item(source_id=source_record.id, guid=guid):
                    continue
                title: str = str(entry.get("title") or "Untitled")
                summary: str = str(entry.get("summary") or "")
                url: str = str(entry.get("link") or "")
                published_at: datetime = self._parse_published(entry.get("published"))
                self.repository.create_raw_item(
                    source_id=source_record.id,
                    guid=guid,
                    title=title,
                    summary=summary,
                    url=url,
                    published_at=published_at,
                )
                fetched += 1
        return IngestionStats(fetched=fetched)
