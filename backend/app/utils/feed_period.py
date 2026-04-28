"""Compute UTC-naive lower bounds for feed date filters (calendar semantics in Europe/Berlin)."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.models.news import FeedPeriod

BERLIN_TZ: ZoneInfo = ZoneInfo("Europe/Berlin")
UTC_TZ: ZoneInfo = ZoneInfo("UTC")


def period_start_utc_naive(period: FeedPeriod | None) -> datetime | None:
    """Return inclusive lower bound for ``created_at`` (DB stores naive UTC)."""
    if period is None:
        return None

    now_berlin: datetime = datetime.now(BERLIN_TZ)
    start_berlin: datetime

    if period is FeedPeriod.TODAY:
        start_berlin = datetime.combine(now_berlin.date(), time.min, tzinfo=BERLIN_TZ)
    elif period is FeedPeriod.LAST_3_DAYS:
        day: date = now_berlin.date() - timedelta(days=2)
        start_berlin = datetime.combine(day, time.min, tzinfo=BERLIN_TZ)
    elif period is FeedPeriod.THIS_WEEK:
        d: date = now_berlin.date()
        monday: date = d - timedelta(days=d.weekday())
        start_berlin = datetime.combine(monday, time.min, tzinfo=BERLIN_TZ)
    elif period is FeedPeriod.THIS_MONTH:
        start_berlin = now_berlin.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return start_berlin.astimezone(UTC_TZ).replace(tzinfo=None)
