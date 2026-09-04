import pytest

from app.core.config import settings
from app.services.relevance_filter_service import RelevanceFilterService


def test_relevance_filter_accepts_life_impact_topics() -> None:
    service = RelevanceFilterService()
    result = service.evaluate(
        title="Neues Gesetz zur Heizung",
        summary="Eigentümer erhalten Fördergeld beim Austausch.",
    )
    assert result.is_relevant is True
    assert result.score >= 0.12


def test_relevance_filter_rejects_sports() -> None:
    service = RelevanceFilterService()
    result = service.evaluate(
        title="Bundesliga Spieltag",
        summary="Sportnachrichten ohne direkten Alltagsnutzen.",
    )
    assert result.is_relevant is False


def test_relevance_filter_accepts_breaking_school_attack() -> None:
    service = RelevanceFilterService()
    result = service.evaluate(
        title="Schongau (Bayern): Mehrere Verletzte am Welfen-Gymnasium – der Überblick",
        summary="Am Welfen-Gymnasium sind mehrere Menschen verletzt worden, die Polizei hat einen 16-Jährigen festgenommen.",
    )
    assert result.is_relevant is True
    assert result.score >= 0.85
    assert result.reason == "Breaking news bypass."


def test_relevance_filter_bypasses_official_statistics_sources() -> None:
    service = RelevanceFilterService()
    result = service.evaluate(
        title="Destatis GENESIS: Datensatz 61111-0002",
        summary='{"Object":{"Content":"raw csv"}}',
        source_key="destatis_genesis",
    )
    assert result.is_relevant is True
    assert result.score == 1.0
    assert result.reason == "Official statistics source bypass."

    eurostat = service.evaluate(
        title="Eurostat: Inflation",
        summary="{}",
        source_key="eurostat",
    )
    assert eurostat.is_relevant is True
    assert eurostat.reason == "Official statistics source bypass."

    govdata = service.evaluate(
        title="GovData: Demo",
        summary="csv",
        source_key="govdata",
    )
    assert govdata.is_relevant is True
    assert govdata.reason == "Official statistics source bypass."

    europa = service.evaluate(
        title="data.europa.eu: Demo",
        summary="csv",
        source_key="data_europa",
    )
    assert europa.is_relevant is True
    assert europa.reason == "Official statistics source bypass."


def test_relevance_filter_rejects_publisher_news_when_google_test_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "rss_allow_unverified_catalog_sources", False)
    service = RelevanceFilterService()
    result = service.evaluate(
        title="Bundesliga Spieltag",
        summary="Sportnachrichten ohne direkten Alltagsnutzen.",
        source_key="die_zeit",
    )
    assert result.is_relevant is False


def test_relevance_filter_bypasses_publisher_sources_during_google_test(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "rss_allow_unverified_catalog_sources", True)
    service = RelevanceFilterService()
    result = service.evaluate(
        title="Bundesliga Spieltag",
        summary="Sportnachrichten ohne direkten Alltagsnutzen.",
        source_key="bild",
    )
    assert result.is_relevant is True
    assert result.score == 1.0
    assert result.reason == "Google test publisher source bypass."
