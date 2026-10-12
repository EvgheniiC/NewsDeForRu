"""Authenticated listen-queue sync."""

from __future__ import annotations

from datetime import datetime
import json
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.app_user import AppUser
from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews
from app.models.user_listening import UserListeningState
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


def _state(news_id: int, updated_at: int, chunk_index: int = 0) -> dict[str, Any]:
    return {
        "items": [{"news_id": news_id, "chunk_index": chunk_index, "finished": False}],
        "current_news_id": news_id,
        "auto_next": False,
        "updated_at": updated_at,
    }


def test_listening_requires_auth(api_client: TestClient) -> None:
    assert api_client.get("/users/me/listening").status_code == 401
    assert api_client.put("/users/me/listening", json=_state(1, 1)).status_code == 401


def test_listening_put_get_last_write_wins_and_skips_unknown(api_client: TestClient) -> None:
    email: str = "listen-sync@example.com"
    password: str = "listen-secret-pass-1"
    _ensure_no_reader(email)
    tokens: dict[str, Any] = _verify_reader(api_client, email, password)
    headers: dict[str, str] = {"Authorization": f"Bearer {tokens['access_token']}"}
    news_id: int = _create_news("listen-queue-1")
    updated_at: int = int(time.time() * 1000)

    empty = api_client.get("/users/me/listening", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["updated_at"] == 0

    put = api_client.put("/users/me/listening", headers=headers, json=_state(news_id, updated_at, 2))
    assert put.status_code == 200
    body: dict[str, Any] = put.json()
    assert body["applied"] is True
    assert body["skipped_news_ids"] == []
    assert body["state"]["items"] == [{"news_id": news_id, "chunk_index": 2, "finished": False}]

    got = api_client.get("/users/me/listening", headers=headers)
    assert got.status_code == 200
    assert got.json()["current_news_id"] == news_id
    assert got.json()["items"][0]["chunk_index"] == 2

    stale = api_client.put("/users/me/listening", headers=headers, json=_state(news_id, updated_at - 1, 0))
    assert stale.status_code == 200
    assert stale.json()["applied"] is False
    assert stale.json()["state"]["items"][0]["chunk_index"] == 2

    unknown = api_client.put(
        "/users/me/listening",
        headers=headers,
        json=_state(9_999_999, updated_at + 5),
    )
    assert unknown.status_code == 200
    assert unknown.json()["applied"] is True
    assert unknown.json()["skipped_news_ids"] == [9_999_999]
    assert unknown.json()["state"]["items"] == []
    assert unknown.json()["state"]["current_news_id"] is None


def test_delete_account_removes_listening_state(api_client: TestClient) -> None:
    email: str = "listen-delete@example.com"
    password: str = "listen-secret-pass-1"
    _ensure_no_reader(email)
    tokens: dict[str, Any] = _verify_reader(api_client, email, password)
    headers: dict[str, str] = {"Authorization": f"Bearer {tokens['access_token']}"}
    news_id: int = _create_news("listen-delete-1")
    put = api_client.put(
        "/users/me/listening",
        headers=headers,
        json=_state(news_id, int(time.time() * 1000)),
    )
    assert put.status_code == 200

    deleted = api_client.post("/auth/delete-account", json={"password": password}, headers=headers)
    assert deleted.status_code == 200

    db = SessionLocal()
    try:
        rows = list(db.scalars(select(UserListeningState)).all())
        for row in rows:
            payload: dict[str, Any] = json.loads(row.state_json)
            item_ids: list[int] = [int(item["news_id"]) for item in payload.get("items", [])]
            assert news_id not in item_ids
    finally:
        db.close()
