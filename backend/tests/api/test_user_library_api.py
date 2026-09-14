"""Authenticated library sync for useful/saved and read news."""

from __future__ import annotations

from datetime import datetime
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.app_user import AppUser
from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews
from app.models.user_library import UserReadNews, UserSavedNews
from app.repositories.news_repository import NewsRepository
from app.repositories.user_repository import UserRepository


def _token_from_dev_link(link: str) -> str:
    parsed = urlparse(link)
    query: dict[str, list[str]] = parse_qs(parsed.query)
    token_values: list[str] = query.get("token", [])
    assert token_values, f"token missing in dev link: {link}"
    return token_values[0]


def _ensure_no_reader(email: str) -> None:
    db = SessionLocal()
    try:
        repo = UserRepository(db)
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


def _create_news(guid: str) -> int:
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
            publication_status=PipelineStatus.PUBLISHED,
            topic=NewsTopic.LIFE,
            is_urgent=False,
            is_positive=False,
        )
        saved: ProcessedNews = repo.create_processed_news(processed)
        return saved.id


def test_library_requires_auth(api_client: TestClient) -> None:
    assert api_client.get("/users/me/library").status_code == 401
    assert api_client.put("/users/me/library", json={"saved": [], "read": []}).status_code == 401


def test_library_put_get_and_unmark(api_client: TestClient) -> None:
    email: str = "library-sync@example.com"
    password: str = "library-secret-pass-1"
    _ensure_no_reader(email)
    tokens: dict[str, Any] = _verify_reader(api_client, email, password)
    headers: dict[str, str] = {"Authorization": f"Bearer {tokens['access_token']}"}
    news_id: int = _create_news("library-useful-1")
    marked_at: int = int(time.time() * 1000)

    empty = api_client.get("/users/me/library", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == {"saved": [], "read": []}

    put = api_client.put(
        "/users/me/library",
        headers=headers,
        json={
            "saved": [{"news_id": news_id, "marked_at": marked_at, "removed": False}],
            "read": [{"news_id": news_id, "read_at": marked_at + 1}],
        },
    )
    assert put.status_code == 200
    body: dict[str, Any] = put.json()
    assert body["saved_count"] == 1
    assert body["read_count"] == 1
    assert body["skipped_news_ids"] == []

    got = api_client.get("/users/me/library", headers=headers)
    assert got.status_code == 200
    snapshot: dict[str, Any] = got.json()
    assert snapshot["saved"] == [{"news_id": news_id, "marked_at": marked_at}]
    assert snapshot["read"] == [{"news_id": news_id, "read_at": marked_at + 1}]

    unmark = api_client.put(
        "/users/me/library",
        headers=headers,
        json={
            "saved": [{"news_id": news_id, "marked_at": marked_at + 10, "removed": True}],
            "read": [],
        },
    )
    assert unmark.status_code == 200
    assert unmark.json()["saved_count"] == 0

    after = api_client.get("/users/me/library", headers=headers)
    assert after.json()["saved"] == []
    assert after.json()["read"] == [{"news_id": news_id, "read_at": marked_at + 1}]


def test_library_last_write_wins(api_client: TestClient) -> None:
    email: str = "library-lww@example.com"
    password: str = "library-secret-pass-1"
    _ensure_no_reader(email)
    tokens: dict[str, Any] = _verify_reader(api_client, email, password)
    headers: dict[str, str] = {"Authorization": f"Bearer {tokens['access_token']}"}
    news_id: int = _create_news("library-lww-1")
    base: int = int(time.time() * 1000)

    first = api_client.put(
        "/users/me/library",
        headers=headers,
        json={"saved": [{"news_id": news_id, "marked_at": base + 2_000, "removed": False}], "read": []},
    )
    assert first.status_code == 200

    stale_remove = api_client.put(
        "/users/me/library",
        headers=headers,
        json={"saved": [{"news_id": news_id, "marked_at": base + 1_000, "removed": True}], "read": []},
    )
    assert stale_remove.status_code == 200
    assert stale_remove.json()["saved_count"] == 1

    stale_upsert = api_client.put(
        "/users/me/library",
        headers=headers,
        json={"saved": [{"news_id": news_id, "marked_at": base + 1_500, "removed": False}], "read": []},
    )
    assert stale_upsert.status_code == 200
    got = api_client.get("/users/me/library", headers=headers)
    assert got.json()["saved"] == [{"news_id": news_id, "marked_at": base + 2_000}]


def test_library_skips_unknown_news_id(api_client: TestClient) -> None:
    email: str = "library-skip@example.com"
    password: str = "library-secret-pass-1"
    _ensure_no_reader(email)
    tokens: dict[str, Any] = _verify_reader(api_client, email, password)
    headers: dict[str, str] = {"Authorization": f"Bearer {tokens['access_token']}"}

    put = api_client.put(
        "/users/me/library",
        headers=headers,
        json={
            "saved": [{"news_id": 9_999_999, "marked_at": int(time.time() * 1000), "removed": False}],
            "read": [{"news_id": 9_999_998, "read_at": int(time.time() * 1000)}],
        },
    )
    assert put.status_code == 200
    body: dict[str, Any] = put.json()
    assert body["saved_count"] == 0
    assert body["read_count"] == 0
    assert sorted(body["skipped_news_ids"]) == [9_999_998, 9_999_999]


def test_delete_account_removes_library_rows(api_client: TestClient) -> None:
    email: str = "library-delete@example.com"
    password: str = "library-secret-pass-1"
    _ensure_no_reader(email)
    tokens: dict[str, Any] = _verify_reader(api_client, email, password)
    headers: dict[str, str] = {"Authorization": f"Bearer {tokens['access_token']}"}
    news_id: int = _create_news("library-delete-1")
    marked_at: int = int(time.time() * 1000)
    put = api_client.put(
        "/users/me/library",
        headers=headers,
        json={
            "saved": [{"news_id": news_id, "marked_at": marked_at, "removed": False}],
            "read": [{"news_id": news_id, "read_at": marked_at}],
        },
    )
    assert put.status_code == 200

    deleted = api_client.post("/auth/delete-account", json={"password": password}, headers=headers)
    assert deleted.status_code == 200

    db = SessionLocal()
    try:
        saved_rows = db.scalars(select(UserSavedNews).where(UserSavedNews.processed_news_id == news_id)).all()
        read_rows = db.scalars(select(UserReadNews).where(UserReadNews.processed_news_id == news_id)).all()
        assert saved_rows == []
        assert read_rows == []
    finally:
        db.close()
