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


def test_news_endpoint_accepts_period_filter() -> None:
    init_database()
    for period in ("today", "last_3_days", "this_week", "this_month"):
        response = client.get("/news", params={"period": period})
        assert response.status_code == 200, period
        data: dict = response.json()
        assert "items" in data


def test_top_news_today_returns_shape() -> None:
    init_database()
    response = client.get("/news/top-today")
    assert response.status_code == 200
    data: dict = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    for it in data["items"]:
        assert "rank" in it
        r: dict = it["rank"]
        assert "total_score" in r
        assert "source_count" in r
