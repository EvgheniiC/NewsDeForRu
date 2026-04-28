"""Anonymous engagement analytics (likes, dwell, navigation)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.repositories.engagement_repository import find_existing_news_ids, insert_engagement_batch
from app.schemas.engagement import EngagementBatchRequest, EngagementBatchResponse, RawEngagementEvent

router: APIRouter = APIRouter()


def _validate_uuid(value: str) -> str:
    try:
        u: UUID = UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid anonymous_user_id") from exc
    return str(u)


def _merge_session_into_payload(payload: dict[str, Any], session_id: str | None) -> dict[str, Any]:
    if not session_id:
        return payload
    out: dict[str, Any] = dict(payload)
    if "session_id" not in out:
        out["session_id"] = session_id
    return out


@router.post("/events", response_model=EngagementBatchResponse)
def post_engagement_events(
    body: EngagementBatchRequest,
    db: Session = Depends(get_db_session),
) -> EngagementBatchResponse:
    uid: str = _validate_uuid(body.anonymous_user_id)

    if not body.events:
        return EngagementBatchResponse(inserted=0, skipped_duplicate=0)

    raw_ids = {e.news_id for e in body.events}
    existing: set[int] = find_existing_news_ids(db, raw_ids)
    missing = raw_ids - existing
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown news_id values: {sorted(missing)}")

    prepared_events: list[RawEngagementEvent] = []
    for ev in body.events:
        payload: dict[str, Any] = _merge_session_into_payload(dict(ev.payload), body.session_id)
        prepared_events.append(
            RawEngagementEvent(
                news_id=ev.news_id,
                event_type=ev.event_type,
                client_event_id=ev.client_event_id,
                payload=payload,
            )
        )

    inserted, skipped = insert_engagement_batch(db, uid, prepared_events)
    return EngagementBatchResponse(inserted=inserted, skipped_duplicate=skipped)
