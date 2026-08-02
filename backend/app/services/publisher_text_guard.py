from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.core.config import Settings, settings
from app.schemas.llm_output import LLMNewsOutput, fallback_after_validation_failure

_WORD_RE: re.Pattern[str] = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True)
class PublisherTextOverlap:
    is_suspicious: bool
    max_similarity_ratio: float
    longest_match_words: int
    longest_match_chars: int


def _normalized_words(text: str) -> tuple[str, ...]:
    normalized: str = unicodedata.normalize("NFKC", text).casefold()
    return tuple(_WORD_RE.findall(normalized))


def _text_segments(output: LLMNewsOutput) -> tuple[str, ...]:
    return (
        output.title,
        output.one_sentence_summary,
        output.plain_language,
        output.impact_unified,
        output.impact_owner,
        output.impact_tenant,
        output.impact_buyer,
        output.action_items,
        output.bonus_block,
        output.spoiler,
    )


def detect_publisher_text_overlap(
    *,
    source_title: str,
    source_summary: str,
    output_segments: tuple[str, ...],
    app_settings: Settings | None = None,
) -> PublisherTextOverlap:
    """Detect suspicious verbatim or near-verbatim reuse of publisher RSS text."""
    cfg: Settings = app_settings if app_settings is not None else settings
    source_segments: tuple[tuple[str, ...], ...] = tuple(
        words
        for words in (_normalized_words(source_title), _normalized_words(source_summary))
        if words
    )
    candidate_segments: tuple[tuple[str, ...], ...] = tuple(
        words for words in (_normalized_words(text) for text in output_segments) if words
    )

    max_ratio: float = 0.0
    longest_words: int = 0
    longest_chars: int = 0

    for source_words in source_segments:
        for candidate_words in candidate_segments:
            matcher: SequenceMatcher[str] = SequenceMatcher(
                None,
                source_words,
                candidate_words,
                autojunk=False,
            )
            ratio: float = matcher.ratio()
            match = matcher.find_longest_match()
            match_words: int = match.size
            match_chars: int = len(" ".join(source_words[match.a : match.a + match.size]))
            max_ratio = max(max_ratio, ratio)
            if (match_words, match_chars) > (longest_words, longest_chars):
                longest_words = match_words
                longest_chars = match_chars

    has_long_match: bool = (
        longest_words >= cfg.publisher_text_overlap_min_words
        and longest_chars >= cfg.publisher_text_overlap_min_chars
    )
    has_high_similarity: bool = (
        longest_chars >= cfg.publisher_text_similarity_min_chars
        and max_ratio >= cfg.publisher_text_similarity_threshold
    )
    return PublisherTextOverlap(
        is_suspicious=has_long_match or has_high_similarity,
        max_similarity_ratio=max_ratio,
        longest_match_words=longest_words,
        longest_match_chars=longest_chars,
    )


def detect_llm_output_overlap(
    *,
    source_title: str,
    source_summary: str,
    output: LLMNewsOutput,
    app_settings: Settings | None = None,
) -> PublisherTextOverlap:
    return detect_publisher_text_overlap(
        source_title=source_title,
        source_summary=source_summary,
        output_segments=_text_segments(output),
        app_settings=app_settings,
    )


def guard_llm_output(
    *,
    source_title: str,
    source_summary: str,
    output: LLMNewsOutput,
    app_settings: Settings | None = None,
) -> tuple[LLMNewsOutput, PublisherTextOverlap]:
    """Replace suspicious output before persistence or publication."""
    overlap: PublisherTextOverlap = detect_llm_output_overlap(
        source_title=source_title,
        source_summary=source_summary,
        output=output,
        app_settings=app_settings,
    )
    safe_output: LLMNewsOutput = (
        fallback_after_validation_failure() if overlap.is_suspicious else output
    )
    return safe_output, overlap
