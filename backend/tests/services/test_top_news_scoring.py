from __future__ import annotations

from datetime import datetime, timedelta

from app.services.top_news_scoring import freshness_points, mentions_points, total_top_score


def test_mentions_points_caps_at_five() -> None:
    assert mentions_points(1) == 1
    assert mentions_points(5) == 5
    assert mentions_points(99) == 5


def test_freshness_tiers() -> None:
    now: datetime = datetime(2026, 4, 30, 12, 0, 0)
    assert freshness_points(now - timedelta(minutes=30), now) == 3
    assert freshness_points(now - timedelta(hours=3), now) == 2
    assert freshness_points(now - timedelta(hours=12), now) == 1
    assert freshness_points(now - timedelta(hours=25), now) == 0


def test_total_top_score_sum() -> None:
    now: datetime = datetime(2026, 4, 30, 12, 0, 0)
    pub: datetime = now - timedelta(minutes=10)
    total, m, f, ai = total_top_score(
        distinct_source_count=3,
        published_at_utc_naive=pub,
        now_utc_naive=now,
        ai_importance_1_to_10=8,
    )
    assert m == 3 and f == 3 and ai == 8
    assert total == 14
