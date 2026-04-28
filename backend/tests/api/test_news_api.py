from fastapi.testclient import TestClient

from app.core.database import init_database
from app.main import app

client: TestClient = TestClient(app)


def test_news_endpoint_returns_paginated_shape() -> None:
    init_database()
    response = client.get("/news")
    assert response.status_code == 200
    data: dict = response.json()
    assert "items" in data
    assert "next_cursor" in data
    assert isinstance(data["items"], list)
    assert data["next_cursor"] is None or isinstance(data["next_cursor"], int)
