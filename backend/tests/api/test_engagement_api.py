from fastapi.testclient import TestClient

from app.core.database import init_database
from app.main import app

client: TestClient = TestClient(app)

VALID_ANON: str = "550e8400-e29b-41d4-a716-446655440000"


def test_engagement_empty_batch_returns_zeroes() -> None:
    init_database()
    response = client.post("/engagement/events", json={"anonymous_user_id": VALID_ANON, "events": []})
    assert response.status_code == 200
    assert response.json() == {"inserted": 0, "skipped_duplicate": 0}


def test_engagement_rejects_unknown_news_id() -> None:
    init_database()
    response = client.post(
        "/engagement/events",
        json={
            "anonymous_user_id": VALID_ANON,
            "events": [{"news_id": 9_999_999, "event_type": "useful", "payload": {"value": True}}],
        },
    )
    assert response.status_code == 400
    assert "news_id" in response.json()["detail"].lower()


def test_engagement_rejects_invalid_anonymous_id() -> None:
    init_database()
    response = client.post(
        "/engagement/events",
        json={"anonymous_user_id": "not-a-uuid", "events": []},
    )
    assert response.status_code in (400, 422)
