"""GET /moderation/queue age filter."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.app_user import AppUser
from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews
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
        existing: AppUser | None = repo.get_by_email("ops-queue-test@example.com")
        if existing is None:
            repo.create_staff_user(
                email="ops-queue-test@example.com",
                password_hash=hash_password(password),
                can_moderate=True,
                can_run_pipeline=False,
            )
        else:
            repo.grant_staff_privileges(existing, can_moderate=True, can_run_pipeline=False)

    tokens = api_client.post(
        "/auth/login",
        json={"email": "ops-queue-test@example.com", "password": password},
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create_needs_review_item(*, guid: str, created_at: datetime) -> int:
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        src = repo.upsert_source(f"src-{guid}", f"Source {guid}", f"http://example.com/{guid}/rss")
        raw = repo.create_raw_item(
            source_id=src.id,
            guid=guid,
            title=f"Title {guid}",
            summary="Summary",
            url=f"http://example.com/{guid}",
            published_at=created_at,
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
            topic=NewsTopic.LIFE,
            is_urgent=False,
            is_positive=False,
            created_at=created_at,
        )
        saved: ProcessedNews = repo.create_processed_news(processed)
        return saved.id


def test_moderation_queue_excludes_items_older_than_seven_days(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
) -> None:
    recent_id: int = _create_needs_review_item(
        guid="queue-recent-1",
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    old_id: int = _create_needs_review_item(
        guid="queue-old-1",
        created_at=datetime.utcnow() - timedelta(days=8),
    )

    response = api_client.get("/moderation/queue", headers=bearer_ops_headers)
    assert response.status_code == 200

    ids: set[int] = {item["id"] for item in response.json()}
    assert recent_id in ids
    assert old_id not in ids

    with SessionLocal() as db:
        old_row: ProcessedNews | None = db.execute(
            select(ProcessedNews).where(ProcessedNews.id == old_id)
        ).scalar_one_or_none()
        assert old_row is not None
        assert old_row.publication_status == PipelineStatus.NEEDS_REVIEW
