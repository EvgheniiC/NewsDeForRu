"""PATCH /moderation/{news_id}/metadata for queue items."""

from __future__ import annotations

from datetime import datetime
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.app_user import AppUser
from app.models.news import ImpactPresentation, ModerationEvent, NewsTopic, PipelineStatus, ProcessedNews
from app.repositories.news_repository import NewsRepository
from app.repositories.user_repository import UserRepository
from app.services.passwords import hash_password


@pytest.fixture()
def api_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def bearer_ops_headers(api_client: TestClient) -> dict[str, str]:
    password: str = "correct horse battery staple"
    with SessionLocal() as db:
        repo: UserRepository = UserRepository(db)
        existing: AppUser | None = repo.get_by_email("ops-meta-test@example.com")
        if existing is None:
            repo.create_staff_user(
                email="ops-meta-test@example.com",
                password_hash=hash_password(password),
                can_moderate=True,
                can_run_pipeline=False,
            )
        else:
            repo.grant_staff_privileges(existing, can_moderate=True, can_run_pipeline=False)

    tokens = api_client.post(
        "/auth/login",
        json={"email": "ops-meta-test@example.com", "password": password},
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create_needs_review_item(*, guid: str, topic: NewsTopic = NewsTopic.LIFE) -> int:
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        src = repo.upsert_source(f"src-{guid}", f"Source {guid}", f"http://example.com/{guid}/rss")
        raw = repo.create_raw_item(
            source_id=src.id,
            guid=guid,
            title=f"Title {guid}",
            summary="Summary",
            url=f"http://example.com/{guid}",
            published_at=datetime.utcnow(),
        )
        processed: ProcessedNews = ProcessedNews(
            raw_item_id=raw.id,
            title=f"Title {guid}",
            one_sentence_summary="One line",
            plain_language="Plain",
            impact_presentation=ImpactPresentation.MULTI,
            impact_owner="",
            impact_tenant="",
            impact_buyer="",
            action_items="",
            spoiler="",
            source_url=f"http://example.com/{guid}",
            publication_status=PipelineStatus.NEEDS_REVIEW,
            topic=topic,
            is_urgent=False,
            is_positive=False,
        )
        saved: ProcessedNews = repo.create_processed_news(processed)
        return saved.id


def test_patch_metadata_updates_topic_in_queue(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
) -> None:
    news_id: int = _create_needs_review_item(guid="meta-topic-1", topic=NewsTopic.LIFE)

    response = api_client.patch(
        f"/moderation/{news_id}/metadata",
        headers=bearer_ops_headers,
        json={"topic": "politics"},
    )
    assert response.status_code == 200
    body: dict[str, object] = response.json()
    assert body["topic"] == "politics"
    assert body["is_urgent"] is False
    assert body["is_positive"] is False


def test_patch_metadata_records_audit_event(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
) -> None:
    news_id: int = _create_needs_review_item(guid="meta-audit-1")

    response = api_client.patch(
        f"/moderation/{news_id}/metadata",
        headers=bearer_ops_headers,
        json={"is_urgent": True, "is_positive": True},
    )
    assert response.status_code == 200
    assert response.json()["is_urgent"] is True
    assert response.json()["is_positive"] is True

    with SessionLocal() as db:
        events: list[ModerationEvent] = list(
            db.execute(
                select(ModerationEvent).where(
                    ModerationEvent.processed_news_id == news_id,
                    ModerationEvent.action == "metadata_update",
                )
            ).scalars()
        )
        assert len(events) == 1


def test_patch_metadata_rejects_published_item(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
) -> None:
    news_id: int = _create_needs_review_item(guid="meta-published-1")
    with SessionLocal() as db:
        row: ProcessedNews | None = db.get(ProcessedNews, news_id)
        assert row is not None
        row.publication_status = PipelineStatus.PUBLISHED
        db.add(row)
        db.commit()

    response = api_client.patch(
        f"/moderation/{news_id}/metadata",
        headers=bearer_ops_headers,
        json={"topic": "economy"},
    )
    assert response.status_code == 409


def test_patch_metadata_requires_moderator(api_client: TestClient) -> None:
    email: str = "reader-meta-test@example.com"
    password: str = "reader-secret-pass-1"
    with SessionLocal() as db:
        repo: UserRepository = UserRepository(db)
        existing: AppUser | None = repo.get_by_email(email)
        if existing is not None:
            db.delete(existing)
            db.commit()

    reg = api_client.post("/auth/register", json={"email": email, "password": password}).json()
    news_id: int = _create_needs_review_item(guid="meta-reader-1")

    response = api_client.patch(
        f"/moderation/{news_id}/metadata",
        headers={"Authorization": f"Bearer {reg['access_token']}"},
        json={"topic": "economy"},
    )
    assert response.status_code == 403


def test_patch_metadata_empty_body_422(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
) -> None:
    news_id: int = _create_needs_review_item(guid="meta-empty-1")

    response = api_client.patch(
        f"/moderation/{news_id}/metadata",
        headers=bearer_ops_headers,
        json={},
    )
    assert response.status_code == 422
