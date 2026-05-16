"""Operator auth protects moderation and manual pipeline endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.staff_user import StaffRefreshToken
from app.repositories.staff_repository import StaffRepository
from app.services.passwords import hash_password
from app.services.staff_tokens import refresh_token_hash_hex


@pytest.fixture()
def api_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def ops_user_plain_password(api_client: TestClient) -> str:
    db = SessionLocal()
    try:
        repo = StaffRepository(db)
        existing = repo.get_by_email("ops-test@example.com")
        if existing is None:
            repo.create_staff_user(
                email="ops-test@example.com",
                password_hash=hash_password("correct horse battery staple"),
                can_moderate=True,
                can_run_pipeline=True,
            )
        return "correct horse battery staple"
    finally:
        db.close()


def test_staff_login_issues_tokens(api_client: TestClient, ops_user_plain_password: str) -> None:
    resp = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    )
    assert resp.status_code == 200
    data: dict[str, Any] = resp.json()
    assert data.get("token_type") == "bearer"
    assert isinstance(data.get("access_token"), str)
    assert isinstance(data.get("refresh_token"), str)


def test_moderation_queue_requires_operator_auth(api_client: TestClient) -> None:
    r = api_client.get("/moderation/queue")
    assert r.status_code == 401


def test_moderation_queue_with_operator_token_returns_list(api_client: TestClient, bearer_ops_headers: dict[str, str]) -> None:
    r = api_client.get("/moderation/queue", headers=bearer_ops_headers)
    assert r.status_code == 200
    body: object = r.json()
    assert isinstance(body, list)


@pytest.fixture()
def bearer_ops_headers(api_client: TestClient, ops_user_plain_password: str) -> dict[str, str]:
    tokens = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_pipeline_requires_operator_auth(api_client: TestClient) -> None:
    r = api_client.post("/pipeline/run")
    assert r.status_code == 401


def test_staff_me_requires_valid_token(api_client: TestClient) -> None:
    assert api_client.get("/auth/me", headers={"Authorization": "Bearer bad"}).status_code == 401


def test_refresh_rotates_opaque_token(api_client: TestClient, ops_user_plain_password: str) -> None:
    first = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    )
    rt1 = first.json()["refresh_token"]

    refreshed = api_client.post("/auth/refresh", json={"refresh_token": rt1})
    assert refreshed.status_code == 200
    rt2 = refreshed.json()["refresh_token"]
    assert rt2 != rt1

    old_reuse = api_client.post("/auth/refresh", json={"refresh_token": rt1})
    assert old_reuse.status_code == 401


def test_logout_revokes_refresh(api_client: TestClient, ops_user_plain_password: str) -> None:
    tokens = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    ).json()

    logout = api_client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout.status_code == 200

    again = api_client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert again.status_code == 401


def test_expired_refresh_rejected(api_client: TestClient, ops_user_plain_password: str) -> None:
    login_json = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    ).json()
    plain_refresh: str = login_json["refresh_token"]
    h = refresh_token_hash_hex(plain_refresh)

    db = SessionLocal()
    try:
        row = db.execute(select(StaffRefreshToken).where(StaffRefreshToken.token_hash == h)).scalar_one()
        row.expires_at = datetime.utcnow() - timedelta(days=1)
        db.add(row)
        db.commit()
    finally:
        db.close()

    r = api_client.post("/auth/refresh", json={"refresh_token": plain_refresh})
    assert r.status_code == 401


def test_staff_me_ok(api_client: TestClient, bearer_ops_headers: dict[str, str]) -> None:
    r = api_client.get("/auth/me", headers=bearer_ops_headers)
    assert r.status_code == 200
    payload: dict[str, Any] = r.json()
    assert payload["email"] == "ops-test@example.com"
    assert payload["can_moderate"] is True
    assert payload["can_run_pipeline"] is True
