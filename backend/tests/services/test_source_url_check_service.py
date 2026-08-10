"""Unit tests for publisher URL health classification and probing."""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import SessionLocal, init_database
from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews, RawNewsItem, Source, SourceUrlStatus
from app.services.source_url_check_service import (
    classify_http_status,
    probe_source_url,
    resolve_next_status,
    run_source_url_checks,
)


def test_classify_http_status() -> None:
    assert classify_http_status(200) is SourceUrlStatus.ALIVE
    assert classify_http_status(301) is SourceUrlStatus.ALIVE
    assert classify_http_status(404) is SourceUrlStatus.UNAVAILABLE
    assert classify_http_status(410) is SourceUrlStatus.UNAVAILABLE
    assert classify_http_status(403) is SourceUrlStatus.UNKNOWN
    assert classify_http_status(500) is SourceUrlStatus.UNKNOWN


def test_resolve_next_status_keeps_previous_on_inconclusive() -> None:
    probe_unknown = MagicMock(status=SourceUrlStatus.UNKNOWN, http_status=403)
    assert (
        resolve_next_status(SourceUrlStatus.ALIVE, probe_unknown) is SourceUrlStatus.ALIVE
    )
    assert (
        resolve_next_status(SourceUrlStatus.UNAVAILABLE, probe_unknown)
        is SourceUrlStatus.UNAVAILABLE
    )


def test_resolve_next_status_flips_on_confirmed() -> None:
    dead = MagicMock(status=SourceUrlStatus.UNAVAILABLE, http_status=404)
    alive = MagicMock(status=SourceUrlStatus.ALIVE, http_status=200)
    assert resolve_next_status(SourceUrlStatus.ALIVE, dead) is SourceUrlStatus.UNAVAILABLE
    assert resolve_next_status(SourceUrlStatus.UNAVAILABLE, alive) is SourceUrlStatus.ALIVE


def test_probe_source_url_head_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "HEAD"
        return httpx.Response(404, request=request)

    transport: httpx.MockTransport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = probe_source_url(client, "https://example.com/gone")
    assert result.status is SourceUrlStatus.UNAVAILABLE
    assert result.http_status == 404


def test_probe_source_url_falls_back_to_get_on_405() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(405, request=request)
        assert request.method == "GET"
        return httpx.Response(200, request=request)

    transport: httpx.MockTransport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = probe_source_url(client, "https://example.com/ok")
    assert result.status is SourceUrlStatus.ALIVE
    assert result.http_status == 200


def _seed_published(session: Session, url: str) -> int:
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
        url=url,
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
        source_url=url,
        confidence_score=0.9,
        publication_status=PipelineStatus.PUBLISHED,
        topic=NewsTopic.LIFE,
        rights_verified=True,
    )
    session.add(processed)
    session.commit()
    session.refresh(processed)
    return processed.id


def test_run_source_url_checks_marks_unavailable(monkeypatch) -> None:
    init_database()
    session: Session = SessionLocal()
    try:
        news_id: int = _seed_published(session, "https://example.com/dead-article")

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, request=request)

        transport: httpx.MockTransport = httpx.MockTransport(handler)
        real_client = httpx.Client

        def client_factory(*args, **kwargs):
            kwargs["transport"] = transport
            return real_client(*args, **kwargs)

        monkeypatch.setattr(
            "app.services.source_url_check_service.httpx.Client",
            client_factory,
        )
        cfg: Settings = Settings(
            source_url_check_lookback_days=3,
            source_url_check_max_items=50,
            source_url_check_timeout_seconds=5.0,
        )
        result = run_source_url_checks(session, cfg)
        assert result.checked >= 1
        assert result.marked_unavailable >= 1
        row: ProcessedNews | None = session.get(ProcessedNews, news_id)
        assert row is not None
        assert row.source_url_status is SourceUrlStatus.UNAVAILABLE
        assert row.source_url_http_status == 404
        assert row.source_url_checked_at is not None
    finally:
        session.close()
