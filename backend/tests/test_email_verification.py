"""Email verification after reader registration."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
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
        user = repo.get_by_email(email)
        if user is not None:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_register_requires_email_verification_before_login(api_client: TestClient) -> None:
    email: str = "verify-flow@example.com"
    password: str = "reader-secret-pass-1"
    _ensure_no_reader(email)

    reg = api_client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    reg_body: dict[str, Any] = reg.json()
    assert "access_token" not in reg_body
    assert isinstance(reg_body.get("dev_verification_link"), str)

    login_before = api_client.post("/auth/login", json={"email": email, "password": password})
    assert login_before.status_code == 403

    token: str = _token_from_dev_link(reg_body["dev_verification_link"])
    verified = api_client.post("/auth/verify-email", json={"token": token})
    assert verified.status_code == 200
    tokens: dict[str, Any] = verified.json()
    assert tokens.get("token_type") == "bearer"

    me = api_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == email

    login_after = api_client.post("/auth/login", json={"email": email, "password": password})
    assert login_after.status_code == 200


def test_register_duplicate_unverified_resends(api_client: TestClient) -> None:
    email: str = "verify-dup@example.com"
    password: str = "reader-secret-pass-1"
    _ensure_no_reader(email)

    first = api_client.post("/auth/register", json={"email": email, "password": password})
    assert first.status_code == 200
    second = api_client.post("/auth/register", json={"email": email, "password": password})
    assert second.status_code == 200
    assert second.json().get("dev_verification_link")


def test_register_duplicate_verified_returns_409(api_client: TestClient) -> None:
    email: str = "verify-conflict@example.com"
    password: str = "reader-secret-pass-1"
    _ensure_no_reader(email)

    reg = api_client.post("/auth/register", json={"email": email, "password": password}).json()
    token: str = _token_from_dev_link(reg["dev_verification_link"])
    assert api_client.post("/auth/verify-email", json={"token": token}).status_code == 200

    dup = api_client.post("/auth/register", json={"email": email, "password": password})
    assert dup.status_code == 409


def test_resend_verification_for_unverified_user(api_client: TestClient) -> None:
    email: str = "verify-resend@example.com"
    password: str = "reader-secret-pass-1"
    _ensure_no_reader(email)

    assert api_client.post("/auth/register", json={"email": email, "password": password}).status_code == 200
    resent = api_client.post("/auth/resend-verification", json={"email": email})
    assert resent.status_code == 200
    assert isinstance(resent.json().get("dev_verification_link"), str)


def test_verify_email_rejects_invalid_token(api_client: TestClient) -> None:
    response = api_client.post("/auth/verify-email", json={"token": "not-a-valid-token"})
    assert response.status_code == 400


def test_resend_verification_unknown_email_is_generic(api_client: TestClient) -> None:
    response = api_client.post("/auth/resend-verification", json={"email": "nobody-verify@example.com"})
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body.get("dev_verification_link") is None
