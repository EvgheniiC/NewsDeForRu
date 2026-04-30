"""Format datetimes for API responses in Europe/Berlin (single clock for operators and UI)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.utils.feed_period import BERLIN_TZ


def to_berlin_iso(dt: datetime) -> str:
    """Interpret naive values as UTC (matches DB), return ISO 8601 with Berlin offset."""
    if dt.tzinfo is None:
        utc_instant: datetime = dt.replace(tzinfo=timezone.utc)
    else:
        utc_instant = dt.astimezone(timezone.utc)
    berlin: datetime = utc_instant.astimezone(BERLIN_TZ)
    return berlin.isoformat(timespec="microseconds")
