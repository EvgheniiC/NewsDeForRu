"""Reader (app user) registration and JWT; separate audience from staff."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.reader_user import ReaderRefreshToken
from app.repositories.reader_repository import ReaderRepository


@pytest.fixture()
def api_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def reader_credentials() -> tuple[str, str]:
    return "reader-test@example.com", "reader-secret-pass-1"


def _ensure_no_reader(email: str) -> None:
    db = SessionLocal()
    try:
        repo = ReaderRepository(db)
        u = repo.get_by_email(email)
        if u is not None:
            db.delete(u)
            db.commit()
    finally:
        db.close()


@pytest.fixture()
def registered_reader(api_client: TestClient, reader_credentials: tuple[str, str]) -> dict[str, str]:
    email, password = reader_credentials
    _ensure_no_reader(email)
    reg = api_client.post("/reader/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    return reg.json()


@pytest.fixture()
def ops_user_plain_password(api_client: TestClient) -> str:
    from app.repositories.staff_repository import StaffRepository
    from app.services.passwords import hash_password

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


@pytest.fixture()
def bearer_ops_headers(api_client: TestClient, ops_user_plain_password: str) -> dict[str, str]:
    tokens = api_client.post(
        "/auth/login",
        json={"email": "ops-test@example.com", "password": ops_user_plain_password},
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_reader_register_login_and_me(
    api_client: TestClient,
    reader_credentials: tuple[str, str],
) -> None:
    email, password = reader_credentials
    _ensure_no_reader(email)

    reg = api_client.post("/reader/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    reg_body: dict[str, Any] = reg.json()
    assert reg_body.get("token_type") == "bearer"

    me = api_client.get(
        "/reader/auth/me",
        headers={"Authorization": f"Bearer {reg_body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == email.lower()

    login = api_client.post("/reader/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200


def test_reader_register_duplicate_email(api_client: TestClient, reader_credentials: tuple[str, str]) -> None:
    email, password = reader_credentials
    _ensure_no_reader(email)
    assert api_client.post("/reader/auth/register", json={"email": email, "password": password}).status_code == 200
    dup = api_client.post("/reader/auth/register", json={"email": email, "password": password})
    assert dup.status_code == 409


def test_reader_token_not_valid_for_staff_me(
    api_client: TestClient,
    registered_reader: dict[str, str],
) -> None:
    r = api_client.get("/auth/me", headers={"Authorization": f"Bearer {registered_reader['access_token']}"})
    assert r.status_code == 401


def test_staff_token_not_valid_for_reader_me(api_client: TestClient, bearer_ops_headers: dict[str, str]) -> None:
    r = api_client.get("/reader/auth/me", headers=bearer_ops_headers)
    assert r.status_code == 401


def test_reader_refresh_rotates(api_client: TestClient, reader_credentials: tuple[str, str]) -> None:
    email, password = reader_credentials
    _ensure_no_reader(email)
    first = api_client.post("/reader/auth/register", json={"email": email, "password": password})
    rt1: str = first.json()["refresh_token"]
    second = api_client.post("/reader/auth/refresh", json={"refresh_token": rt1})
    assert second.status_code == 200
    rt2: str = second.json()["refresh_token"]
    assert rt2 != rt1
    assert api_client.post("/reader/auth/refresh", json={"refresh_token": rt1}).status_code == 401


def test_reader_expired_refresh_rejected(api_client: TestClient, reader_credentials: tuple[str, str]) -> None:
    from app.services.staff_tokens import refresh_token_hash_hex

    email, password = reader_credentials
    _ensure_no_reader(email)
    login_json = api_client.post("/reader/auth/register", json={"email": email, "password": password}).json()
    plain_refresh: str = login_json["refresh_token"]
    h = refresh_token_hash_hex(plain_refresh)

    db = SessionLocal()
    try:
        row = db.execute(select(ReaderRefreshToken).where(ReaderRefreshToken.token_hash == h)).scalar_one()
        row.expires_at = datetime.utcnow() - timedelta(days=1)
        db.add(row)
        db.commit()
    finally:
        db.close()

    assert api_client.post("/reader/auth/refresh", json={"refresh_token": plain_refresh}).status_code == 401
