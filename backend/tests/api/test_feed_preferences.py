"""Account feed interests and the personal news order."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.app_user import AppUser
from app.models.news import CoverTag, ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews
from app.repositories.news_repository import NewsRepository
from app.repositories.user_repository import UserRepository


def _token_from_dev_link(link: str) -> str:
    parsed = urlparse(link)
    query: dict[str, list[str]] = parse_qs(parsed.query)
    token_values: list[str] = query.get("token", [])
    assert token_values, f"token missing in dev link: {link}"
    return token_values[0]


def _ensure_no_reader(email: str) -> None:
    db: Session = SessionLocal()
    try:
        repo: UserRepository = UserRepository(db)
        user: AppUser | None = repo.get_by_email(email)
        if user is not None:
            repo.delete_user(user)
    finally:
        db.close()


def _verify_reader(api_client: TestClient, email: str, password: str) -> dict[str, Any]:
    reg = api_client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    token: str = _token_from_dev_link(reg.json()["dev_verification_link"])
    verified = api_client.post("/auth/verify-email", json={"token": token})
    assert verified.status_code == 200
    return verified.json()


def _publish(guid: str, cover_tag: CoverTag, published_at: datetime) -> int:
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
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
        saved: ProcessedNews = repo.create_processed_news(processed)
        return saved.id


def test_feed_preferences_require_auth(api_client: TestClient) -> None:
    assert api_client.get("/users/me/feed-preferences").status_code == 401
    assert api_client.put("/users/me/feed-preferences", json={"interests": ["health"]}).status_code == 401
    assert api_client.get("/news?for_me=true").status_code == 401


def test_feed_preferences_roundtrip_and_personal_order(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "rss_enabled_source_keys", "")
    monkeypatch.setattr(settings, "rss_allow_unverified_catalog_sources", False)

    email: str = "feed-prefs@example.com"
    password: str = "feed-secret-pass-1"
    _ensure_no_reader(email)
    tokens: dict[str, Any] = _verify_reader(api_client, email, password)
    headers: dict[str, str] = {"Authorization": f"Bearer {tokens['access_token']}"}

    empty = api_client.get("/users/me/feed-preferences", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == {"interests": []}

    rejected = api_client.put(
        "/users/me/feed-preferences",
        headers=headers,
        json={"interests": ["not-a-topic"]},
    )
    assert rejected.status_code == 422

    saved = api_client.put(
        "/users/me/feed-preferences",
        headers=headers,
        json={"interests": ["health", "health", "jobs"]},
    )
    assert saved.status_code == 200
    assert saved.json()["interests"] == ["health", "jobs"]

    now: datetime = datetime.utcnow()
    money_id: int = _publish("pref-money", CoverTag.MONEY, now)
    health_id: int = _publish("pref-health", CoverTag.HEALTH, now - timedelta(hours=3))

    page = api_client.get("/news?for_me=true&limit=10", headers=headers)
    assert page.status_code == 200
    ids: list[int] = [item["id"] for item in page.json()["items"]]
    assert ids.index(health_id) < ids.index(money_id)
