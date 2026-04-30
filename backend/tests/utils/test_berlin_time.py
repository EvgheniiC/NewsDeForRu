from __future__ import annotations

from datetime import datetime, timezone

from app.utils.berlin_time import to_berlin_iso


def test_to_berlin_iso_naive_utc_becomes_berlin_offset_summer() -> None:
    # CEST: UTC+2
    utc_naive: datetime = datetime(2026, 4, 30, 16, 1, 38, 256136)
    out: str = to_berlin_iso(utc_naive)
    assert out.startswith("2026-04-30T18:01:38")
    assert out.endswith("+02:00")


def test_to_berlin_iso_aware_utc() -> None:
    dt: datetime = datetime(2026, 4, 30, 16, 1, 38, tzinfo=timezone.utc)
    out: str = to_berlin_iso(dt)
    assert "18:01:38" in out
    assert "+02:00" in out


def test_to_berlin_iso_winter_offset() -> None:
    utc_naive: datetime = datetime(2026, 1, 15, 12, 0, 0)
    out: str = to_berlin_iso(utc_naive)
    assert out.startswith("2026-01-15T13:00:00")
    assert out.endswith("+01:00")
