"""Forgot-password and reset-password API."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.models.password_reset_token import PasswordResetToken
from app.repositories.user_repository import UserRepository
from app.services.passwords import hash_password, verify_password
from app.services.staff_tokens import refresh_token_hash_hex


@pytest.fixture()
def api_client() -> Generator[TestClient, None, None]:
    settings.password_reset_dev_expose_link = True
    settings.password_reset_frontend_base_url = "http://127.0.0.1:5173"
    with TestClient(app) as client:
        yield client


def _ensure_user(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        existing = repo.get_by_email(email)
        if existing is not None:
            db.delete(existing)
            db.commit()
        repo.create_reader(email=email, password_hash=hash_password(password))
    finally:
        db.close()


def test_forgot_password_generic_response_for_unknown_email(api_client: TestClient) -> None:
    r = api_client.post("/auth/forgot-password", json={"email": "nobody-here@example.com"})
    assert r.status_code == 200
    assert "registered" in r.json()["detail"].lower()


def test_forgot_and_reset_password_flow(api_client: TestClient) -> None:
    email: str = "reset-flow@example.com"
    old_password: str = "old-password-1"
    new_password: str = "new-password-9"
    _ensure_user(email, old_password)

    forgot = api_client.post("/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    body: dict[str, object] = forgot.json()
    dev_link: str | None = body.get("dev_reset_link") if isinstance(body.get("dev_reset_link"), str) else None

    db = SessionLocal()
    try:
        row = db.execute(select(PasswordResetToken)).scalars().all()
        assert len(row) >= 1
        token_row = row[-1]
        # Recover plain token from dev link or brute from DB is not possible; use dev link in dev tests
        if dev_link is None:
            pytest.skip("PASSWORD_RESET_DEV_EXPOSE_LINK not enabled; enable for local test")
        token_plain: str = dev_link.split("token=")[-1]
    finally:
        db.close()

    bad = api_client.post(
        "/auth/reset-password",
        json={"token": token_plain, "new_password": "short"},
    )
    assert bad.status_code == 422

    reset = api_client.post(
        "/auth/reset-password",
        json={"token": token_plain, "new_password": new_password},
    )
    assert reset.status_code == 200

    login_old = api_client.post("/auth/login", json={"email": email, "password": old_password})
    assert login_old.status_code == 401

    login_new = api_client.post("/auth/login", json={"email": email, "password": new_password})
    assert login_new.status_code == 200

    reuse = api_client.post(
        "/auth/reset-password",
        json={"token": token_plain, "new_password": "another-pass-1"},
    )
    assert reuse.status_code == 400


def test_reset_password_expired_token(api_client: TestClient) -> None:
    email: str = "reset-expired@example.com"
    _ensure_user(email, "password-abc-1")

    forgot = api_client.post("/auth/forgot-password", json={"email": email})
    dev_link = forgot.json().get("dev_reset_link")
    if not isinstance(dev_link, str):
        pytest.skip("PASSWORD_RESET_DEV_EXPOSE_LINK not enabled")

    token_plain: str = dev_link.split("token=")[-1]
    h = refresh_token_hash_hex(token_plain)

    db = SessionLocal()
    try:
        row = db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == h)).scalar_one()
        row.expires_at = datetime.utcnow() - timedelta(minutes=5)
        db.add(row)
        db.commit()
    finally:
        db.close()

    r = api_client.post(
        "/auth/reset-password",
        json={"token": token_plain, "new_password": "fresh-pass-1"},
    )
    assert r.status_code == 400
