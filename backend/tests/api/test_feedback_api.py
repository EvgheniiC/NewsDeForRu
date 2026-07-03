"""Tests for POST /feedback."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.utils.feedback_rate_limit import reset_feedback_rate_limits


@pytest.fixture(autouse=True)
def _reset_feedback_limits() -> None:
    reset_feedback_rate_limits()


def _valid_payload() -> dict[str, str]:
    return {
        "category": "suggestion",
        "message": "Предлагаю добавить фильтр по регионам.",
    }


def test_feedback_accepts_valid_submission_in_development(api_client: TestClient) -> None:
    settings.support_contact_email = "ops@example.com"
    settings.app_env = "development"
    response = api_client.post("/feedback", json=_valid_payload())
    assert response.status_code == 200
    assert "отправлено" in response.json()["detail"].lower()


def test_feedback_honeypot_returns_success_without_processing(api_client: TestClient) -> None:
    payload = {**_valid_payload(), "website": "https://spam.example"}
    response = api_client.post("/feedback", json=payload)
    assert response.status_code == 200


def test_feedback_rejects_short_message(api_client: TestClient) -> None:
    response = api_client.post(
        "/feedback",
        json={"category": "bug", "message": "коротко"},
    )
    assert response.status_code == 422


def test_feedback_rate_limited(api_client: TestClient) -> None:
    settings.support_contact_email = "ops@example.com"
    settings.app_env = "development"
    settings.feedback_rate_limit_max_per_hour = 2
    payload = _valid_payload()
    assert api_client.post("/feedback", json=payload).status_code == 200
    assert api_client.post("/feedback", json=payload).status_code == 200
    assert api_client.post("/feedback", json=payload).status_code == 429


def test_feedback_unavailable_in_production_without_inbox(api_client: TestClient) -> None:
    settings.support_contact_email = ""
    settings.app_env = "production"
    response = api_client.post("/feedback", json=_valid_payload())
    assert response.status_code == 503
