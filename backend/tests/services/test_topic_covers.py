from app.models.news import NewsTopic
from app.services.topic_covers import topic_cover_relative_path


def test_topic_cover_path_stable_for_same_id() -> None:
    a: str | None = topic_cover_relative_path(NewsTopic.ECONOMY, 10)
    b: str | None = topic_cover_relative_path(NewsTopic.ECONOMY, 10)
    assert a == b == "/topic-covers/economy/001.jpg"


def test_topic_cover_path_uses_topic_folder() -> None:
    path: str | None = topic_cover_relative_path(NewsTopic.POLITICS, 1)
    assert path == "/topic-covers/politics/001.jpg"
