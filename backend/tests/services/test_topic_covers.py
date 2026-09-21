from app.models.news import CoverTag, NewsTopic
from app.services.cover_tags import coerce_cover_tag
from app.services.topic_covers import topic_cover_relative_path


def test_topic_cover_path_stable_for_same_id() -> None:
    a: str | None = topic_cover_relative_path(NewsTopic.ECONOMY, 10)
    b: str | None = topic_cover_relative_path(NewsTopic.ECONOMY, 10)
    assert a == b == "/topic-covers/economy/001.jpg"


def test_topic_cover_path_uses_topic_folder() -> None:
    path: str | None = topic_cover_relative_path(NewsTopic.POLITICS, 10)
    assert path == "/topic-covers/politics/001.jpg"


def test_topic_cover_path_prefers_cover_tag_folder() -> None:
    path: str | None = topic_cover_relative_path(
        NewsTopic.LIFE,
        10,
        cover_tag=CoverTag.SPORT,
    )
    assert path is not None
    assert path.startswith("/topic-covers/sport/")


def test_topic_cover_falls_back_when_tag_pool_missing() -> None:
    path: str | None = topic_cover_relative_path(NewsTopic.LIFE, 10, cover_tag=None)
    assert path == "/topic-covers/life/001.jpg"


def test_coerce_cover_tag_sport_from_russian() -> None:
    assert coerce_cover_tag("спорт", "life") == CoverTag.SPORT


def test_coerce_cover_tag_construction_from_housing() -> None:
    assert coerce_cover_tag("housing", "politics") == CoverTag.CONSTRUCTION


def test_coerce_cover_tag_defaults_by_topic() -> None:
    assert coerce_cover_tag(None, "economy") == CoverTag.MONEY
    assert coerce_cover_tag("not-a-tag", "politics") == CoverTag.GOVERNMENT
