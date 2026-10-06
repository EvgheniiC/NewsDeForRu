"""GET /moderation/queue age filter and daily stats."""

from __future__ import annotations

from datetime import date, datetime, timedelta
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
from app.utils.feed_period import berlin_calendar_day_bounds_utc_naive, berlin_today


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


def test_approve_publishes_item_without_licence(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _skip_notice(**_kwargs: object) -> bool:
        return False

    monkeypatch.setattr("app.api.routes.moderation.send_moderation_approved_notice", _skip_notice)
    news_id: int = _create_needs_review_item(
        guid="queue-approve-unlicensed",
        created_at=datetime.utcnow(),
    )

    response = api_client.post(
        f"/moderation/{news_id}/action",
        headers=bearer_ops_headers,
        json={"action": "approve"},
    )
    assert response.status_code == 200
    assert response.json()["publication_status"] == "published"


def test_reject_still_filters_item(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
) -> None:
    news_id: int = _create_needs_review_item(
        guid="queue-reject-unlicensed",
        created_at=datetime.utcnow(),
    )

    response = api_client.post(
        f"/moderation/{news_id}/action",
        headers=bearer_ops_headers,
        json={"action": "reject"},
    )
    assert response.status_code == 200
    assert response.json()["publication_status"] == "filtered_out"


def _create_processed_item(
    *,
    guid: str,
    created_at: datetime,
    published_at: datetime,
    status: PipelineStatus,
    rights_verified: bool,
) -> int:
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        src = repo.upsert_source(f"src-{guid}", f"Source {guid}", f"http://example.com/{guid}/rss")
        raw = repo.create_raw_item(
            source_id=src.id,
            guid=guid,
            title=f"Title {guid}",
            summary="Summary",
            url=f"http://example.com/{guid}",
            published_at=published_at,
            rights_verified=rights_verified,
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
            publication_status=status,
            topic=NewsTopic.LIFE,
            is_urgent=False,
            is_positive=False,
            rights_verified=rights_verified,
            created_at=created_at,
        )
        saved: ProcessedNews = repo.create_processed_news(processed)
        return saved.id


def test_daily_stats_counts_feed_and_moderation_for_selected_day(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _skip_notice(**_kwargs: object) -> bool:
        return False

    monkeypatch.setattr("app.api.routes.moderation.send_moderation_approved_notice", _skip_notice)

    selected_day: date = date(2020, 1, 15)
    day_start, _day_end = berlin_calendar_day_bounds_utc_naive(selected_day)
    on_day: datetime = day_start + timedelta(hours=3)
    other_day: datetime = day_start - timedelta(hours=3)

    _create_processed_item(
        guid="stats-published-visible",
        created_at=on_day,
        published_at=on_day,
        status=PipelineStatus.PUBLISHED,
        rights_verified=True,
    )
    _create_processed_item(
        guid="stats-published-hidden",
        created_at=on_day,
        published_at=on_day,
        status=PipelineStatus.PUBLISHED,
        rights_verified=False,
    )
    _create_processed_item(
        guid="stats-published-other-day",
        created_at=other_day,
        published_at=other_day,
        status=PipelineStatus.PUBLISHED,
        rights_verified=True,
    )
    waiting_id: int = _create_processed_item(
        guid="stats-waiting",
        created_at=on_day,
        published_at=on_day,
        status=PipelineStatus.NEEDS_REVIEW,
        rights_verified=True,
    )
    approved_id: int = _create_processed_item(
        guid="stats-later-approved",
        created_at=on_day,
        published_at=on_day,
        status=PipelineStatus.NEEDS_REVIEW,
        rights_verified=True,
    )
    _create_processed_item(
        guid="stats-waiting-other-day",
        created_at=other_day,
        published_at=other_day,
        status=PipelineStatus.NEEDS_REVIEW,
        rights_verified=True,
    )

    before = api_client.get(
        "/moderation/daily-stats",
        headers=bearer_ops_headers,
        params={"date": "2020-01-15"},
    )
    assert before.status_code == 200
    before_body: dict[str, object] = before.json()
    assert before_body["date"] == "2020-01-15"
    assert before_body["published_count"] == 2
    assert before_body["moderation_count"] == 2
    assert before_body["visit_count"] == 0
    assert waiting_id > 0

    approved = api_client.post(
        f"/moderation/{approved_id}/action",
        headers=bearer_ops_headers,
        json={"action": "approve"},
    )
    assert approved.status_code == 200

    after = api_client.get(
        "/moderation/daily-stats",
        headers=bearer_ops_headers,
        params={"date": "2020-01-15"},
    )
    assert after.status_code == 200
    after_body: dict[str, object] = after.json()
    assert after_body["published_count"] == 2
    assert after_body["moderation_count"] == 2

    invalid = api_client.get(
        "/moderation/daily-stats",
        headers=bearer_ops_headers,
        params={"date": "not-a-date"},
    )
    assert invalid.status_code == 422


def test_app_visit_is_counted_once_per_session_and_day(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
) -> None:
    today: str = berlin_today().isoformat()
    session_id: str = "11111111-1111-4111-8111-111111111111"
    other_session_id: str = "22222222-2222-4222-8222-222222222222"

    before = api_client.get(
        "/moderation/daily-stats",
        headers=bearer_ops_headers,
        params={"date": today},
    )
    assert before.status_code == 200
    before_visits: int = int(before.json()["visit_count"])

    first = api_client.post("/engagement/visits", json={"session_id": session_id})
    assert first.status_code == 200
    assert first.json()["recorded"] is True

    duplicate = api_client.post("/engagement/visits", json={"session_id": session_id})
    assert duplicate.status_code == 200
    assert duplicate.json()["recorded"] is False

    second = api_client.post("/engagement/visits", json={"session_id": other_session_id})
    assert second.status_code == 200
    assert second.json()["recorded"] is True

    invalid = api_client.post("/engagement/visits", json={"session_id": "not-a-uuid"})
    assert invalid.status_code == 422

    after = api_client.get(
        "/moderation/daily-stats",
        headers=bearer_ops_headers,
        params={"date": today},
    )
    assert after.status_code == 200
    assert int(after.json()["visit_count"]) == before_visits + 2


def test_daily_stats_requires_moderator(api_client: TestClient) -> None:
    anonymous = api_client.get("/moderation/daily-stats", params={"date": "2020-01-15"})
    assert anonymous.status_code == 401
