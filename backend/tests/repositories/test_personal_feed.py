"""Personal feed puts chosen cover tags ahead of the rest, including across pages."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, init_database
from app.models.news import CoverTag, ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews
from app.repositories.news_repository import NewsRepository


@pytest.fixture(autouse=True)
def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    init_database()


def _publish(
    repo: NewsRepository,
    *,
    guid: str,
    published_at: datetime,
    cover_tag: CoverTag,
) -> ProcessedNews:
    src = repo.upsert_source("custom_desk", "Desk", "https://example.test/custom_desk")
    raw = repo.create_raw_item(
        source_id=src.id,
        guid=guid,
        title=guid,
        summary="summary",
        url=f"https://example.test/{guid}",
        published_at=published_at,
        rights_verified=True,
    )
    processed: ProcessedNews = ProcessedNews(
        raw_item_id=raw.id,
        title=guid,
        one_sentence_summary="Суть",
        plain_language="Просто",
        impact_presentation=ImpactPresentation.SINGLE,
        impact_unified="",
        impact_owner="",
        impact_tenant="",
        impact_buyer="",
        action_items="",
        source_url=f"https://example.test/{guid}",
        publication_status=PipelineStatus.PUBLISHED,
        topic=NewsTopic.LIFE,
        cover_tag=cover_tag,
        rights_verified=True,
    )
    return repo.create_processed_news(processed)


def test_preferred_cover_tags_lead_and_cursor_keeps_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "rss_enabled_source_keys", "")
    monkeypatch.setattr(settings, "rss_allow_unverified_catalog_sources", False)
    now: datetime = datetime.utcnow()
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        newest_other: ProcessedNews = _publish(
            repo,
            guid="money-new",
            published_at=now,
            cover_tag=CoverTag.MONEY,
        )
        older_health: ProcessedNews = _publish(
            repo,
            guid="health-old",
            published_at=now - timedelta(hours=2),
            cover_tag=CoverTag.HEALTH,
        )
        mid_health: ProcessedNews = _publish(
            repo,
            guid="health-mid",
            published_at=now - timedelta(hours=1),
            cover_tag=CoverTag.HEALTH,
        )

        interests: frozenset[CoverTag] = frozenset({CoverTag.HEALTH})
        first, has_more = repo.list_published(limit=1, preferred_cover_tags=interests)
        assert has_more is True
        assert [row.id for row in first] == [mid_health.id]

        second, second_more = repo.list_published(
            limit=1,
            preferred_cover_tags=interests,
            cursor_id=first[0].id,
        )
        assert second_more is True
        assert [row.id for row in second] == [older_health.id]

        third, third_more = repo.list_published(
            limit=1,
            preferred_cover_tags=interests,
            cursor_id=second[0].id,
        )
        assert third_more is False
        assert [row.id for row in third] == [newest_other.id]
