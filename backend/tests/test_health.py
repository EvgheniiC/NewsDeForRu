from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client: TestClient = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    data: dict[str, Any] = response.json()

    assert response.status_code == 200
    assert data["status"] in ("ok", "degraded")
    assert data["database"] in ("ok", "unavailable")
    assert "last_pipeline_run_at" in data
    assert "last_pipeline_ok" in data
    assert "pipeline_scheduler" in data
