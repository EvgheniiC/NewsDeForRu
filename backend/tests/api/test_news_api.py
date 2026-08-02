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
    for item in data["items"]:
        assert "published_at" in item
        assert "source_name" in item


def test_news_detail_includes_attribution_fields() -> None:
    init_database()
    list_response = client.get("/news")
    assert list_response.status_code == 200
    items: list[dict] = list_response.json()["items"]
    if not items:
        return
    news_id: int = int(items[0]["id"])
    detail_response = client.get(f"/news/{news_id}")
    assert detail_response.status_code == 200
    detail: dict = detail_response.json()
    assert detail["published_at"]
    assert detail["source_name"]


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


def test_news_endpoint_accepts_positive_only_filter() -> None:
    init_database()
    response = client.get("/news", params={"positive_only": "true"})
    assert response.status_code == 200
    data: dict = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_full_article_endpoint_is_not_available() -> None:
    init_database()
    response = client.get("/news/1/full-article")
    assert response.status_code == 404
