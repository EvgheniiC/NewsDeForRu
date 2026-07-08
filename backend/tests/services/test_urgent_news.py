from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.llm_output import LLMNewsOutput
from app.services import urgent_news
from app.services.urgent_news import ev_is_urgent_news, is_breaking_news


def _llm(*, importance: int = 5) -> LLMNewsOutput:
    return LLMNewsOutput(
        title="Т",
        one_sentence_summary="К",
        plain_language="П",
        impact_presentation="multi",
        impact_unified="",
        impact_owner="a",
        impact_tenant="b",
        impact_buyer="c",
        action_items="- x",
        bonus_block="b",
        spoiler="s",
        topic="life",
        is_positive=False,
        confidence_score=0.5,
        importance_score=importance,
    )


def test_ev_is_urgent_news_inert_text_false() -> None:
    assert ev_is_urgent_news("t", "s", _llm()) is False


def test_eilmeldung_strong() -> None:
    assert ev_is_urgent_news("Eilmeldung: Test", "", _llm(importance=3)) is True


def test_explosion_strong() -> None:
    assert ev_is_urgent_news("Explosion in Halle", "Details folgen.", _llm(importance=4)) is True


def test_explosion_negated_not_strong_still_false_without_other_signals() -> None:
    assert (
        ev_is_urgent_news(
            "Update",
            "Keine Explosion bestätigt.",
            _llm(importance=4),
        )
        is False
    )


def test_evakuierung_negated() -> None:
    assert (
        ev_is_urgent_news(
            "Fabrikbrand",
            "Keine Evakuierung nötig.",
            _llm(importance=5),
        )
        is False
    )


def test_weak_polizei_title_only_low_importance_false() -> None:
    assert ev_is_urgent_news("Polizei ermittelt", "Routine.", _llm(importance=5)) is False


def test_weak_polizei_title_with_echo_in_summary() -> None:
    assert (
        ev_is_urgent_news(
            "Polizei vor Ort",
            "Schwerer Unfall auf der A9.",
            _llm(importance=5),
        )
        is True
    )


def test_weak_polizei_high_importance() -> None:
    assert ev_is_urgent_news("Polizei sperrt Zentrum", "", _llm(importance=8)) is True


def test_noisy_jetzt_low_importance_false(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now: datetime = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(urgent_news, "_utc_now", lambda: fixed_now)
    pub: datetime = fixed_now - timedelta(hours=1)
    assert ev_is_urgent_news("Jetzt mehr News", "...", _llm(importance=5), published_at=pub) is False


def test_noisy_jetzt_high_importance() -> None:
    assert ev_is_urgent_news("Jetzt: Grossalarm", "—", _llm(importance=8)) is True


def test_noisy_live_headline_with_weak_body() -> None:
    assert (
        ev_is_urgent_news(
            "Live-Blog",
            "Bahn-Streik angekündigt.",
            _llm(importance=5),
        )
        is True
    )


def test_fresh_weak_polizei_importance_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now: datetime = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(urgent_news, "_utc_now", lambda: fixed_now)
    pub: datetime = fixed_now - timedelta(hours=2)
    assert (
        ev_is_urgent_news(
            "Polizei meldet Sperrung",
            "",
            _llm(importance=7),
            published_at=pub,
        )
        is True
    )


def test_stale_weak_polizei_importance_seven_false(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now: datetime = datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(urgent_news, "_utc_now", lambda: fixed_now)
    pub: datetime = fixed_now - timedelta(hours=30)
    assert (
        ev_is_urgent_news(
            "Polizei meldet Sperrung",
            "",
            _llm(importance=7),
            published_at=pub,
        )
        is False
    )


def test_is_breaking_news_school_attack_schongau() -> None:
    assert is_breaking_news(
        "Schongau (Bayern): Mehrere Verletzte am Welfen-Gymnasium – der Überblick",
        "Am Welfen-Gymnasium sind mehrere Menschen verletzt worden, die Polizei hat einen 16-Jährigen festgenommen.",
    )


def test_is_breaking_news_amok_keyword() -> None:
    assert is_breaking_news(
        "Update aus Bayern",
        "Nach dem Vorfall deutet vieles auf eine Amoklage hin.",
    )


def test_is_breaking_news_routine_education_false() -> None:
    assert (
        is_breaking_news(
            "Bildung: Jeder dritte Lehrer in Deutschland ist über 50",
            "Statistik zu Lehrkräften an Schulen in Deutschland.",
        )
        is False
    )


def test_ev_is_urgent_news_school_attack_without_high_importance() -> None:
    assert (
        ev_is_urgent_news(
            "Schongau: Mehrere Verletzte am Welfen-Gymnasium",
            "Polizei hat einen 16-Jährigen festgenommen.",
            _llm(importance=4),
        )
        is True
    )
