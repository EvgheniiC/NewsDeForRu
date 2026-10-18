"""Urgent-tab brief assembled from fields the model already writes.

Breaking detection and push stay on ``is_urgent``. A fresh official release with a
concrete reader step can appear in the same tab without that flag.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import ColumnElement, and_, func

from app.models.news import ProcessedNews, RawNewsItem, Source
from app.schemas.news import normalize_action_items_for_api
from app.services.open_source_card import is_open_paraphrase_source, open_paraphrase_source_keys

OFFICIAL_ACTION_MAX_AGE: timedelta = timedelta(hours=48)

# Keep in sync with ``normalize_action_items_for_api``.
_LEGACY_ACTION_PLACEHOLDER: str = (
    "- Уточните детали по официальным источникам и актуальным объявлениям."
)


def official_action_published_after(now: datetime | None = None) -> datetime:
    """Naive UTC lower bound for an official release that still counts as today."""
    current: datetime = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is not None:
        current = current.astimezone(timezone.utc).replace(tzinfo=None)
    return current - OFFICIAL_ACTION_MAX_AGE


def affects_text(
    impact_presentation: str,
    impact_unified: str,
    impact_owner: str,
    impact_tenant: str,
    impact_buyer: str,
) -> str:
    """Who the story touches: one paragraph, or the three angles as bullet lines."""
    if impact_presentation == "single":
        return impact_unified.strip()
    if impact_presentation != "multi":
        return ""
    lines: list[str] = []
    for raw in (impact_owner, impact_tenant, impact_buyer):
        text: str = raw.strip()
        if text == "":
            continue
        lines.append(text if text.startswith("- ") else f"- {text}")
    return "\n".join(lines)


def action_today_text(action_items: str) -> str:
    """Concrete steps, with the legacy filler line removed."""
    return normalize_action_items_for_api(action_items).strip()


def urgent_brief_lines(
    *,
    impact_presentation: str,
    impact_unified: str,
    impact_owner: str,
    impact_tenant: str,
    impact_buyer: str,
    action_items: str,
) -> tuple[str, str]:
    """Return ``(affects, action_today)`` for the urgent feed card."""
    return (
        affects_text(
            impact_presentation,
            impact_unified,
            impact_owner,
            impact_tenant,
            impact_buyer,
        ),
        action_today_text(action_items),
    )


def _published_naive_utc(published_at: datetime) -> datetime:
    if published_at.tzinfo is None:
        return published_at
    return published_at.astimezone(timezone.utc).replace(tzinfo=None)


def _source_key(item: ProcessedNews) -> str | None:
    raw: RawNewsItem | None = item.raw_item
    if raw is None or raw.source is None:
        return None
    return raw.source.source_key


def is_fresh_official_action(item: ProcessedNews, *, now: datetime | None = None) -> bool:
    """True for a recent official release that tells the reader what to do."""
    if not is_open_paraphrase_source(_source_key(item)):
        return False
    if action_today_text(item.action_items) == "":
        return False
    raw: RawNewsItem | None = item.raw_item
    if raw is None:
        return False
    return _published_naive_utc(raw.published_at) >= official_action_published_after(now)


def qualifies_for_urgent_feed(item: ProcessedNews, *, now: datetime | None = None) -> bool:
    """Urgent tab: breaking flag, or a fresh official release with a concrete step."""
    if item.is_urgent:
        return True
    return is_fresh_official_action(item, now=now)


def official_action_clause(published_after: datetime) -> ColumnElement[bool]:
    """SQL twin of ``is_fresh_official_action`` for the published-feed query."""
    trimmed = func.trim(ProcessedNews.action_items)
    return and_(
        Source.source_key.in_(open_paraphrase_source_keys()),
        RawNewsItem.published_at >= published_after,
        func.length(trimmed) > 0,
        trimmed != _LEGACY_ACTION_PLACEHOLDER,
    )
