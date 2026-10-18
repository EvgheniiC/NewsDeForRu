from datetime import datetime, timedelta

from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews, RawNewsItem, Source
from app.services.urgent_brief import (
    action_today_text,
    affects_text,
    is_fresh_official_action,
    qualifies_for_urgent_feed,
    urgent_brief_lines,
)


def _item(
    *,
    source_key: str,
    action_items: str,
    published_at: datetime,
    is_urgent: bool = False,
    presentation: ImpactPresentation = ImpactPresentation.SINGLE,
) -> ProcessedNews:
    source: Source = Source(source_key=source_key, name=source_key, rss_url="https://example.test/feed")
    raw: RawNewsItem = RawNewsItem(
        source_id=1,
        guid="g",
        title="t",
        summary="s",
        url="https://example.test/item",
        published_at=published_at,
        source=source,
    )
    return ProcessedNews(
        raw_item_id=1,
        title="Заголовок",
        one_sentence_summary="Суть",
        plain_language="Просто",
        impact_presentation=presentation,
        impact_unified="Касается арендаторов с сегодняшнего дня.",
        impact_owner="Собственники платят сбор.",
        impact_tenant="Арендаторы получают письмо.",
        impact_buyer="",
        action_items=action_items,
        source_url="https://example.test/item",
        publication_status=PipelineStatus.PUBLISHED,
        topic=NewsTopic.LIFE,
        is_urgent=is_urgent,
        raw_item=raw,
    )


def test_affects_uses_single_paragraph_or_three_angles() -> None:
    single: str = affects_text("single", "Жители Баварии.", "a", "b", "c")
    assert single == "Жители Баварии."
    multi: str = affects_text("multi", "", "Собственники.", "Арендаторы.", "")
    assert multi == "- Собственники.\n- Арендаторы."
    assert affects_text("none", "скрыто", "a", "b", "c") == ""


def test_action_today_drops_legacy_filler() -> None:
    filler: str = "- Уточните детали по официальным источникам и актуальным объявлениям."
    assert action_today_text(filler) == ""
    assert action_today_text("- Подать заявление до 18:00") == "- Подать заявление до 18:00"


def test_brief_lines_pair_who_and_today() -> None:
    affects, today = urgent_brief_lines(
        impact_presentation="single",
        impact_unified="Касается пассажиров.",
        impact_owner="",
        impact_tenant="",
        impact_buyer="",
        action_items="- Выйти раньше.",
    )
    assert affects == "Касается пассажиров."
    assert today == "- Выйти раньше."


def test_fresh_official_action_requires_source_step_and_age() -> None:
    now: datetime = datetime(2026, 10, 18, 12, 0, 0)
    fresh: ProcessedNews = _item(
        source_key="eurostat",
        action_items="- Подать заявление сегодня.",
        published_at=now - timedelta(hours=5),
    )
    stale: ProcessedNews = _item(
        source_key="destatis",
        action_items="- Подать заявление сегодня.",
        published_at=now - timedelta(hours=60),
    )
    empty_step: ProcessedNews = _item(
        source_key="govdata",
        action_items="",
        published_at=now - timedelta(hours=1),
    )
    publisher: ProcessedNews = _item(
        source_key="welt",
        action_items="- Подать заявление сегодня.",
        published_at=now - timedelta(hours=1),
    )
    assert is_fresh_official_action(fresh, now=now) is True
    assert is_fresh_official_action(stale, now=now) is False
    assert is_fresh_official_action(empty_step, now=now) is False
    assert is_fresh_official_action(publisher, now=now) is False


def test_urgent_feed_keeps_breaking_items_without_a_step() -> None:
    now: datetime = datetime(2026, 10, 18, 12, 0, 0)
    incident: ProcessedNews = _item(
        source_key="custom",
        action_items="",
        published_at=now,
        is_urgent=True,
    )
    assert qualifies_for_urgent_feed(incident, now=now) is True
