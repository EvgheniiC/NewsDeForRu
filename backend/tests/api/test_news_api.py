from fastapi.testclient import TestClient

from app.core.database import init_database
from app.main import app

client: TestClient = TestClient(app)


def test_news_endpoint_returns_list() -> None:
    init_database()
    response = client.get("/news")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
