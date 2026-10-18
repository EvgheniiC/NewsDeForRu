from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, init_database
from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews
from app.repositories.news_repository import NewsRepository


@pytest.fixture(autouse=True)
def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    init_database()


def _publish(
    repo: NewsRepository,
    *,
    source_key: str,
    guid: str,
    title: str,
    action_items: str,
    published_at: datetime,
    is_urgent: bool,
) -> ProcessedNews:
    src = repo.upsert_source(source_key, source_key, f"https://example.test/{source_key}")
    raw = repo.create_raw_item(
        source_id=src.id,
        guid=guid,
        title=title,
        summary="summary",
        url=f"https://example.test/{guid}",
        published_at=published_at,
        rights_verified=True,
    )
    processed: ProcessedNews = ProcessedNews(
        raw_item_id=raw.id,
        title=title,
        one_sentence_summary="Суть",
        plain_language="Просто",
        impact_presentation=ImpactPresentation.SINGLE,
        impact_unified="Кого касается.",
        impact_owner="",
        impact_tenant="",
        impact_buyer="",
        action_items=action_items,
        source_url=f"https://example.test/{guid}",
        publication_status=PipelineStatus.PUBLISHED,
        topic=NewsTopic.LIFE,
        is_urgent=is_urgent,
        rights_verified=True,
    )
    return repo.create_processed_news(processed)


def test_urgent_feed_includes_breaking_and_fresh_official_step(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "rss_enabled_source_keys", "")
    monkeypatch.setattr(settings, "rss_allow_unverified_catalog_sources", False)
    now: datetime = datetime.utcnow()
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        _publish(
            repo,
            source_key="custom_desk",
            guid="break-1",
            title="Инцидент",
            action_items="",
            published_at=now,
            is_urgent=True,
        )
        _publish(
            repo,
            source_key="eurostat",
            guid="official-fresh",
            title="Срок сегодня",
            action_items="- Подать заявление до 18:00",
            published_at=now - timedelta(hours=3),
            is_urgent=False,
        )
        _publish(
            repo,
            source_key="destatis_genesis",
            guid="official-stale",
            title="Старый срок",
            action_items="- Подать заявление",
            published_at=now - timedelta(hours=72),
            is_urgent=False,
        )
        _publish(
            repo,
            source_key="govdata",
            guid="official-empty",
            title="Без шага",
            action_items="",
            published_at=now,
            is_urgent=False,
        )
        _publish(
            repo,
            source_key="custom_desk",
            guid="publisher-step",
            title="Издатель с шагом",
            action_items="- Проверить расписание",
            published_at=now,
            is_urgent=False,
        )
        _publish(
            repo,
            source_key="data_europa",
            guid="official-filler",
            title="Общая отписка",
            action_items="- Уточните детали по официальным источникам и актуальным объявлениям.",
            published_at=now,
            is_urgent=False,
        )

        urgent_rows, _has_more = repo.list_published(limit=20, urgent_only=True)
        urgent_titles: set[str] = {row.title for row in urgent_rows}
        assert urgent_titles == {"Инцидент", "Срок сегодня"}

        regular_rows, _regular_more = repo.list_published(limit=20)
        regular_titles: set[str] = {row.title for row in regular_rows}
        assert "Срок сегодня" in regular_titles
        assert "Без шага" in regular_titles


def test_urgent_feed_cursor_accepts_official_anchor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "rss_enabled_source_keys", "")
    monkeypatch.setattr(settings, "rss_allow_unverified_catalog_sources", False)
    now: datetime = datetime.utcnow()
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        older: ProcessedNews = _publish(
            repo,
            source_key="custom_desk",
            guid="older-break",
            title="Раньше",
            action_items="",
            published_at=now - timedelta(hours=2),
            is_urgent=True,
        )
        newer: ProcessedNews = _publish(
            repo,
            source_key="eurostat",
            guid="newer-official",
            title="Позже",
            action_items="- Сделать сегодня",
            published_at=now,
            is_urgent=False,
        )
        page, has_more = repo.list_published(limit=1, urgent_only=True)
        assert [row.id for row in page] == [newer.id]
        assert has_more is True
        nxt, nxt_more = repo.list_published(limit=1, urgent_only=True, cursor_id=newer.id)
        assert [row.id for row in nxt] == [older.id]
        assert nxt_more is False
