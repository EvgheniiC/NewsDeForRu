"""Heuristic score for 'top news today': cross-source mentions, freshness, AI importance."""

from __future__ import annotations

from datetime import datetime, timedelta


def mentions_points(distinct_source_count: int) -> int:
    """More outlets covering the same cluster → higher weight (cap at 5)."""
    n: int = max(int(distinct_source_count), 1)
    return min(n, 5)


def freshness_points(published_at_utc_naive: datetime, now_utc_naive: datetime) -> int:
    """Reward recency of the original article (<1h / <6h / <24h)."""
    if published_at_utc_naive > now_utc_naive:
        return 3
    age: timedelta = now_utc_naive - published_at_utc_naive
    hours: float = age.total_seconds() / 3600.0
    if hours < 1.0:
        return 3
    if hours < 6.0:
        return 2
    if hours < 24.0:
        return 1
    return 0


def total_top_score(
    *,
    distinct_source_count: int,
    published_at_utc_naive: datetime,
    now_utc_naive: datetime,
    ai_importance_1_to_10: int,
) -> tuple[int, int, int, int]:
    """Return (total, mentions_part, freshness_part, ai_part)."""
    m: int = mentions_points(distinct_source_count)
    f: int = freshness_points(published_at_utc_naive, now_utc_naive)
    ai: int = max(1, min(int(ai_importance_1_to_10), 10))
    total: int = m + f + ai
    return total, m, f, ai
