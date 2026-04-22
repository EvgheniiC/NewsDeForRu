from typing import Dict

from fastapi.testclient import TestClient

from app.main import app

client: TestClient = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    data: Dict[str, str] = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
