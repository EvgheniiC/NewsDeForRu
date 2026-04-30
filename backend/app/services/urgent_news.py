"""Breaking / urgent news detection (pipeline hook).

Uses a fast keyword layer on raw German RSS title/summary:
- Strong cues (Eilmeldung, Breaking, Explosion, Evakuierung) → urgent unless negated.
- Weak cues (Unfall, Polizei, Streik) → urgent only with a second signal (body echo,
  high LLM importance, or fresh item).
- Noisy cues (Live, Jetzt) → urgent only in the headline plus high importance or another cue.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from app.schemas.llm_output import LLMNewsOutput

_STRONG_KEYWORDS: frozenset[str] = frozenset(
    {
        "eilmeldung",
        "breaking",
        "explosion",
        "evakuierung",
    }
)

# Routine crime/transport keywords — only urgent with confirmation signals.
_WEAK_KEYWORDS: frozenset[str] = frozenset(
    {
        "unfall",
        "polizei",
        "streik",
    }
)

# Often used for emphasis or non-breaking contexts — stricter rules.
_NOISY_KEYWORDS: frozenset[str] = frozenset(
    {
        "live",
        "jetzt",
    }
)

# If this substring appears, ignore Evakuierung-only strong hits (routine 'no evacuation').
_NEGATION_EVACUATION: tuple[str, ...] = (
    "keine evakuierung",
    "keine evakuierungs",
    "kein evakuierungs",
)

_NEGATION_EXPLOSION: tuple[str, ...] = (
    "keine explosion",
    "ohne explosion",
)

_FRESH_MAX_AGE: timedelta = timedelta(hours=24)
_IMPORTANCE_STRONG_SECOND_SIGNAL: int = 8
_IMPORTANCE_NOISY_HEADLINE: int = 8
_IMPORTANCE_WEAK_FRESH: int = 7


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_for_match(text: str) -> str:
    t: str = text.casefold()
    t = t.replace("ß", "ss")
    return t


def _word_hit(haystack_lower: str, keyword_lower: str) -> bool:
    """True if keyword appears as a whole token (handles German headlines)."""
    pattern: str = rf"(?<![\w]){re.escape(keyword_lower)}(?![\w])"
    return re.search(pattern, haystack_lower, flags=re.UNICODE) is not None


def _any_keyword(haystack_lower: str, keywords: frozenset[str]) -> bool:
    return any(_word_hit(haystack_lower, kw) for kw in keywords)


def _keyword_hits(haystack_lower: str, keywords: frozenset[str]) -> frozenset[str]:
    return frozenset(kw for kw in keywords if _word_hit(haystack_lower, kw))


def _has_negation_for_evacuation(text_lower: str) -> bool:
    return any(snippet in text_lower for snippet in _NEGATION_EVACUATION)


def _has_negation_for_explosion(text_lower: str) -> bool:
    return any(snippet in text_lower for snippet in _NEGATION_EXPLOSION)


def _strong_match_respects_negation(title_lower: str, summary_lower: str, keyword: str) -> bool:
    in_title: bool = _word_hit(title_lower, keyword)
    in_summary: bool = _word_hit(summary_lower, keyword)
    if not in_title and not in_summary:
        return False
    combined: str = f"{title_lower} {summary_lower}"
    if keyword == "evakuierung" and _has_negation_for_evacuation(combined):
        return False
    if keyword == "explosion" and _has_negation_for_explosion(combined):
        return False
    return True


def _is_fresh(published_at: datetime | None) -> bool:
    if published_at is None:
        return False
    pub: datetime = _to_aware_utc(published_at)
    return (_utc_now() - pub) <= _FRESH_MAX_AGE


def ev_is_urgent_news(
    raw_title: str,
    raw_summary: str,
    llm: LLMNewsOutput,
    *,
    published_at: datetime | None = None,
) -> bool:
    """
    Return True if this item should appear under the "⚡ Срочно" feed filter.

    Combines German keyword tiers on raw RSS fields with lightweight LLM/recency signals.
    """
    title_n: str = _normalize_for_match(raw_title)
    summary_n: str = _normalize_for_match(raw_summary)
    combined: str = f"{title_n} {summary_n}"

    importance: int = llm.importance_score
    fresh: bool = _is_fresh(published_at)

    has_strong: bool = any(
        _strong_match_respects_negation(title_n, summary_n, kw) for kw in _STRONG_KEYWORDS
    )
    if has_strong:
        return True

    weak_title: frozenset[str] = _keyword_hits(title_n, _WEAK_KEYWORDS)
    weak_summary: frozenset[str] = _keyword_hits(summary_n, _WEAK_KEYWORDS)
    noisy_title: bool = _any_keyword(title_n, _NOISY_KEYWORDS)
    weak_anywhere: bool = _any_keyword(combined, _WEAK_KEYWORDS)

    if weak_title:
        second_signal: bool = (
            bool(weak_summary)
            or importance >= _IMPORTANCE_STRONG_SECOND_SIGNAL
            or (fresh and importance >= _IMPORTANCE_WEAK_FRESH)
        )
        if second_signal:
            return True

    if noisy_title:
        if importance >= _IMPORTANCE_NOISY_HEADLINE:
            return True
        # Do not use raw strong-keyword substring here — negated "Explosion" must not unlock Jetzt/Live.
        if weak_anywhere:
            return True

    return False


__all__ = ["ev_is_urgent_news"]
