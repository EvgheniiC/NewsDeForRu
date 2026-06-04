"""Unified app auth: readers, editorial permissions, protected endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.app_user import AppRefreshToken
from app.repositories.user_repository import UserRepository
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
        repo = UserRepository(db)
        existing = repo.get_by_email("ops-test@example.com")
        if existing is None:
            repo.create_staff_user(
                email="ops-test@example.com",
                password_hash=hash_password("correct horse battery staple"),
                can_moderate=True,
                can_run_pipeline=True,
            )
        else:
            repo.grant_staff_privileges(
                existing,
                can_moderate=True,
                can_run_pipeline=True,
            )
        return "correct horse battery staple"
    finally:
        db.close()


@pytest.fixture()
def bearer_ops_headers(api_client: TestClient, ops_user_plain_password: str) -> dict[str, str]:
    tokens = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def reader_credentials() -> tuple[str, str]:
    return "reader-test@example.com", "reader-secret-pass-1"


def _ensure_no_reader(email: str) -> None:
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        u = repo.get_by_email(email)
        if u is not None:
            db.delete(u)
            db.commit()
    finally:
        db.close()


def test_register_login_and_me(api_client: TestClient, reader_credentials: tuple[str, str]) -> None:
    email, password = reader_credentials
    _ensure_no_reader(email)

    reg = api_client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    reg_body: dict[str, Any] = reg.json()
    assert reg_body.get("token_type") == "bearer"

    me = api_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {reg_body['access_token']}"},
    )
    assert me.status_code == 200
    me_body: dict[str, Any] = me.json()
    assert me_body["email"] == email.lower()
    assert me_body["role"] == "reader"
    assert me_body["can_moderate"] is False
    assert me_body["can_run_pipeline"] is False

    login = api_client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200


def test_register_duplicate_email(api_client: TestClient, reader_credentials: tuple[str, str]) -> None:
    email, password = reader_credentials
    _ensure_no_reader(email)
    assert api_client.post("/auth/register", json={"email": email, "password": password}).status_code == 200
    dup = api_client.post("/auth/register", json={"email": email, "password": password})
    assert dup.status_code == 409


def test_reader_cannot_access_moderation(api_client: TestClient, reader_credentials: tuple[str, str]) -> None:
    email, password = reader_credentials
    _ensure_no_reader(email)
    reg = api_client.post("/auth/register", json={"email": email, "password": password}).json()
    r = api_client.get("/moderation/queue", headers={"Authorization": f"Bearer {reg['access_token']}"})
    assert r.status_code == 403


def test_staff_login_issues_tokens(api_client: TestClient, ops_user_plain_password: str) -> None:
    resp = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    )
    assert resp.status_code == 200
    data: dict[str, Any] = resp.json()
    assert data.get("token_type") == "bearer"
    assert isinstance(data.get("access_token"), str)


def test_moderation_queue_requires_auth(api_client: TestClient) -> None:
    assert api_client.get("/moderation/queue").status_code == 401


def test_moderation_queue_with_editor_token(
    api_client: TestClient,
    bearer_ops_headers: dict[str, str],
) -> None:
    r = api_client.get("/moderation/queue", headers=bearer_ops_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_pipeline_requires_auth(api_client: TestClient) -> None:
    assert api_client.post("/pipeline/run").status_code == 401


def test_me_requires_valid_token(api_client: TestClient) -> None:
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
    assert api_client.post("/auth/refresh", json={"refresh_token": rt1}).status_code == 401


def test_logout_revokes_refresh(api_client: TestClient, ops_user_plain_password: str) -> None:
    tokens = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    ).json()

    assert api_client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
    assert api_client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_expired_refresh_rejected(api_client: TestClient, ops_user_plain_password: str) -> None:
    login_json = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    ).json()
    plain_refresh: str = login_json["refresh_token"]
    h = refresh_token_hash_hex(plain_refresh)

    db = SessionLocal()
    try:
        row = db.execute(select(AppRefreshToken).where(AppRefreshToken.token_hash == h)).scalar_one()
        row.expires_at = datetime.utcnow() - timedelta(days=1)
        db.add(row)
        db.commit()
    finally:
        db.close()

    assert api_client.post("/auth/refresh", json={"refresh_token": plain_refresh}).status_code == 401


def test_staff_me_ok(api_client: TestClient, bearer_ops_headers: dict[str, str]) -> None:
    r = api_client.get("/auth/me", headers=bearer_ops_headers)
    assert r.status_code == 200
    payload: dict[str, Any] = r.json()
    assert payload["email"] == "ops-test@example.com"
    assert payload["can_moderate"] is True
    assert payload["can_run_pipeline"] is True
    assert payload["role"] == "admin"
