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
