"""Persist engagement/analytics batches."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.engagement import UserEngagementEvent
from app.schemas.engagement import RawEngagementEvent, payload_to_json


def find_existing_news_ids(db: Session, news_ids: set[int]) -> set[int]:
    if not news_ids:
        return set()
    from app.models.news import ProcessedNews  # noqa: PLC0415

    rows = db.scalars(select(ProcessedNews.id).where(ProcessedNews.id.in_(news_ids))).all()
    return {int(r) for r in rows}


def insert_engagement_batch(
    db: Session,
    anonymous_user_id: str,
    events: list[RawEngagementEvent],
) -> tuple[int, int]:
    """Returns (inserted_count, skipped_duplicates)."""
    if not events:
        return 0, 0

    client_ids: list[str] = [e.client_event_id for e in events if e.client_event_id]
    existing_ids: set[str] = set()
    if client_ids:
        found = db.scalars(
            select(UserEngagementEvent.client_event_id).where(
                UserEngagementEvent.client_event_id.in_(client_ids)
            )
        ).all()
        existing_ids = {str(x) for x in found if x is not None}

    inserted: int = 0
    skipped: int = 0
    pending_client_ids: set[str] = set()
    for raw in events:
        if raw.client_event_id:
            cid: str = raw.client_event_id
            if cid in existing_ids or cid in pending_client_ids:
                skipped += 1
                continue
            pending_client_ids.add(cid)
        row: UserEngagementEvent = UserEngagementEvent(
            anonymous_user_id=anonymous_user_id,
            processed_news_id=raw.news_id,
            event_type=raw.event_type.value,
            payload_json=payload_to_json(raw.payload),
            client_event_id=raw.client_event_id,
        )
        db.add(row)
        inserted += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return inserted, skipped
