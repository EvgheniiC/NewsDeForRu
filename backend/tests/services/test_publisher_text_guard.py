from __future__ import annotations

from app.core.config import Settings
from app.schemas.llm_output import LLMNewsOutput
from app.services.publisher_text_guard import (
    PublisherTextOverlap,
    detect_llm_output_overlap,
    detect_publisher_text_overlap,
    guard_llm_output,
)


def _settings() -> Settings:
    return Settings(
        publisher_text_overlap_min_words=8,
        publisher_text_overlap_min_chars=50,
        publisher_text_similarity_min_chars=40,
        publisher_text_similarity_threshold=0.72,
    )


def _output(*, plain_language: str) -> LLMNewsOutput:
    return LLMNewsOutput(
        title="Новая мера вступает в силу",
        one_sentence_summary="Власти сообщили об изменении правил.",
        plain_language=plain_language,
        impact_presentation="none",
        impact_unified="",
        impact_owner="",
        impact_tenant="",
        impact_buyer="",
        action_items="",
        bonus_block="",
        spoiler="",
        topic="politics",
        is_positive=False,
        confidence_score=0.95,
        importance_score=7,
    )


def test_detects_long_verbatim_rss_fragment() -> None:
    source_summary: str = (
        "Die Bundesregierung hat am Mittwoch neue Maßnahmen für den öffentlichen "
        "Nahverkehr in mehreren deutschen Städten beschlossen."
    )
    result: PublisherTextOverlap = detect_publisher_text_overlap(
        source_title="Neue Maßnahmen beschlossen",
        source_summary=source_summary,
        output_segments=(f"Контекст: {source_summary}",),
        app_settings=_settings(),
    )

    assert result.is_suspicious is True
    assert result.longest_match_words >= 8
    assert result.longest_match_chars >= 50


def test_detects_unusually_high_similarity_after_small_edits() -> None:
    result: PublisherTextOverlap = detect_publisher_text_overlap(
        source_title="",
        source_summary=(
            "Die Regierung beschließt heute ein neues Programm für bezahlbare "
            "Wohnungen in großen deutschen Städten."
        ),
        output_segments=(
            "Die Regierung beschließt nun ein neues Programm für bezahlbare "
            "Wohnungen in deutschen Städten.",
        ),
        app_settings=_settings(),
    )

    assert result.is_suspicious is True
    assert result.max_similarity_ratio >= 0.72


def test_allows_short_common_phrase() -> None:
    result: PublisherTextOverlap = detect_publisher_text_overlap(
        source_title="Neue Maßnahmen beschlossen",
        source_summary="Weitere Einzelheiten sollen am Freitag veröffentlicht werden.",
        output_segments=("Neue Maßnahmen beschlossen.",),
        app_settings=_settings(),
    )

    assert result.is_suspicious is False


def test_allows_independent_russian_summary() -> None:
    result: PublisherTextOverlap = detect_llm_output_overlap(
        source_title="Bundesregierung beschließt neue Maßnahmen",
        source_summary=(
            "Die Änderungen sollen den öffentlichen Nahverkehr in deutschen "
            "Großstädten langfristig verbessern."
        ),
        output=_output(
            plain_language=(
                "Правительство утвердило меры для развития городского транспорта. "
                "Подробности программы объявят позднее."
            )
        ),
        app_settings=_settings(),
    )

    assert result.is_suspicious is False


def test_guard_replaces_suspicious_output_with_review_only_fallback() -> None:
    source_summary: str = (
        "Die Bundesregierung hat am Mittwoch neue Maßnahmen für den öffentlichen "
        "Nahverkehr in mehreren deutschen Städten beschlossen."
    )
    unsafe_output: LLMNewsOutput = _output(plain_language=source_summary)

    safe_output: LLMNewsOutput
    overlap: PublisherTextOverlap
    safe_output, overlap = guard_llm_output(
        source_title="Neue Maßnahmen beschlossen",
        source_summary=source_summary,
        output=unsafe_output,
        app_settings=_settings(),
    )

    assert overlap.is_suspicious is True
    assert safe_output.confidence_score == 0.0
    assert source_summary not in safe_output.model_dump_json()
