from __future__ import annotations

from fastapi.testclient import TestClient

from app.core import config as app_config
from app.core.database import init_database
from app.main import app

client: TestClient = TestClient(app)


def test_provenance_disabled_returns_404() -> None:
    init_database()
    response = client.get("/internal/provenance/by-raw/1")
    assert response.status_code == 404


def test_provenance_wrong_key_returns_403(monkeypatch) -> None:
    init_database()
    monkeypatch.setattr(app_config.settings, "provenance_api_key", "secret")
    response = client.get("/internal/provenance/by-raw/1", headers={"X-Internal-Api-Key": "wrong"})
    assert response.status_code == 403


def test_provenance_missing_raw_returns_404(monkeypatch) -> None:
    init_database()
    monkeypatch.setattr(app_config.settings, "provenance_api_key", "secret")
    response = client.get("/internal/provenance/by-raw/999999", headers={"X-Internal-Api-Key": "secret"})
    assert response.status_code == 404
