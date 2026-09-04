from __future__ import annotations

from datetime import datetime

import pytest

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, init_database
from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews
from app.repositories.news_repository import NewsRepository


@pytest.fixture(autouse=True)
def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    init_database()


def _make_published(
    repo: NewsRepository,
    *,
    source_key: str,
    name: str,
    guid: str,
    title: str,
    rights_verified: bool,
) -> ProcessedNews:
    src = repo.upsert_source(source_key, name, f"http://example.com/{source_key}/rss")
    raw = repo.create_raw_item(
        source_id=src.id,
        guid=guid,
        title=title,
        summary="summary",
        url=f"http://example.com/{guid}",
        published_at=datetime.utcnow(),
        rights_verified=rights_verified,
    )
    processed: ProcessedNews = ProcessedNews(
        raw_item_id=raw.id,
        title=title,
        one_sentence_summary="one",
        plain_language="plain",
        impact_presentation=ImpactPresentation.MULTI,
        impact_owner="",
        impact_tenant="",
        impact_buyer="",
        action_items="",
        spoiler="",
        source_url=f"http://example.com/{guid}",
        publication_status=PipelineStatus.PUBLISHED,
        topic=NewsTopic.LIFE,
        importance_ai_score=8,
        is_urgent=False,
        rights_verified=rights_verified,
    )
    return repo.create_processed_news(processed)


def test_list_published_hides_disabled_catalog_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "rss_enabled_source_keys", "destatis")
    monkeypatch.setattr(settings, "rss_allow_unverified_catalog_sources", False)
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        _make_published(
            repo,
            source_key="welt",
            name="WELT",
            guid="welt-1",
            title="Welt story",
            rights_verified=False,
        )
        _make_published(
            repo,
            source_key="destatis",
            name="Destatis",
            guid="destatis-1",
            title="Destatis story",
            rights_verified=True,
        )
        rows, _has_more = repo.list_published(limit=20)
        titles: set[str] = {row.title for row in rows}
        assert titles == {"Destatis story"}


def test_list_telegram_digest_hides_disabled_catalog_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "rss_enabled_source_keys", "")
    monkeypatch.setattr(settings, "rss_allow_unverified_catalog_sources", False)
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        _make_published(
            repo,
            source_key="die_zeit",
            name="Die Zeit",
            guid="zeit-1",
            title="Zeit story",
            rights_verified=False,
        )
        _make_published(
            repo,
            source_key="custom_ok",
            name="Custom",
            guid="custom-1",
            title="Custom story",
            rights_verified=True,
        )
        picked: list[ProcessedNews] = repo.list_telegram_digest_candidates(
            min_importance=6,
            limit=10,
            max_scan=100,
        )
        titles: set[str] = {row.title for row in picked}
        assert titles == {"Custom story"}
