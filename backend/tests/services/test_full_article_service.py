from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, init_database
from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews, RawNewsItem, Source
from app.services.full_article_service import FullArticleService, FullArticleUnavailableError


def _seed_published(session: Session) -> int:
    key: str = f"t_{uuid.uuid4().hex[:8]}"
    source: Source = Source(source_key=key, name=f"Test {key}", rss_url=f"https://example.com/rss/{key}")
    session.add(source)
    session.commit()
    session.refresh(source)
    raw: RawNewsItem = RawNewsItem(
        source_id=source.id,
        guid=f"g_{uuid.uuid4().hex}",
        title="Titel",
        summary="Kurz.",
        url="https://example.com/a",
        published_at=datetime.utcnow(),
    )
    session.add(raw)
    session.commit()
    session.refresh(raw)
    processed: ProcessedNews = ProcessedNews(
        raw_item_id=raw.id,
        title="Заголовок",
        one_sentence_summary="Суть.",
        plain_language="Простым языком.",
        impact_presentation=ImpactPresentation.NONE,
        impact_unified="",
        impact_owner="",
        impact_tenant="",
        impact_buyer="",
        action_items="",
        source_url="https://example.com/a",
        confidence_score=0.9,
        publication_status=PipelineStatus.PUBLISHED,
        topic=NewsTopic.LIFE,
    )
    session.add(processed)
    session.commit()
    session.refresh(processed)
    return processed.id


def test_get_or_create_returns_cached_without_fetch() -> None:
    init_database()
    session: Session = SessionLocal()
    try:
        news_id: int = _seed_published(session)
        row: ProcessedNews | None = session.get(ProcessedNews, news_id)
        assert row is not None
        row.full_article_ru = "Уже переведённый текст."
        session.add(row)
        session.commit()
        service: FullArticleService = FullArticleService(session)
        with patch.object(service, "_build_source_text") as build_mock:
            text, cached = service.get_or_create_full_article_ru(news_id)
        assert cached is True
        assert text == "Уже переведённый текст."
        build_mock.assert_not_called()
    finally:
        session.close()


def test_get_or_create_generates_and_stores() -> None:
    init_database()
    session: Session = SessionLocal()
    try:
        news_id: int = _seed_published(session)
        service: FullArticleService = FullArticleService(session)
        with (
            patch.object(service, "_build_source_text", return_value="Deutscher Artikel."),
            patch.object(service, "_translate_to_russian", return_value="Русская статья целиком."),
        ):
            text, cached = service.get_or_create_full_article_ru(news_id)
        assert cached is False
        assert text == "Русская статья целиком."
        row: ProcessedNews | None = session.get(ProcessedNews, news_id)
        assert row is not None
        assert row.full_article_ru == "Русская статья целиком."
    finally:
        session.close()


def test_get_or_create_not_found_for_missing_id() -> None:
    init_database()
    session: Session = SessionLocal()
    try:
        service: FullArticleService = FullArticleService(session)
        with pytest.raises(FullArticleUnavailableError, match="not found"):
            service.get_or_create_full_article_ru(999_999)
    finally:
        session.close()
