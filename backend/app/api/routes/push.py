"""Register / unregister Android FCM tokens for urgent-news push."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.repositories.push_repository import PushRepository
from app.schemas.push import PushSubscribeRequest, PushSubscriptionResponse, PushUnsubscribeRequest
from app.services.push_notifier import (
    subscribe_device_to_urgent_topic,
    unsubscribe_device_from_urgent_topic,
)

router: APIRouter = APIRouter()


@router.post("/subscribe", response_model=PushSubscriptionResponse)
def subscribe_push(
    body: PushSubscribeRequest,
    db_session: Session = Depends(get_db_session),
) -> PushSubscriptionResponse:
    if not settings.push_notifications_enabled:
        raise HTTPException(status_code=503, detail="Push notifications are disabled on the server.")

    token: str = body.device_token.strip()
    ok: bool = subscribe_device_to_urgent_topic(device_token=token)
    if not ok:
        raise HTTPException(status_code=502, detail="Could not subscribe device to push topic.")

    PushRepository(db_session).upsert_enabled(device_token=token, platform=body.platform)
    return PushSubscriptionResponse(subscribed=True, topic=settings.fcm_urgent_topic)


@router.post("/unsubscribe", response_model=PushSubscriptionResponse)
def unsubscribe_push(
    body: PushUnsubscribeRequest,
    db_session: Session = Depends(get_db_session),
) -> PushSubscriptionResponse:
    token: str = body.device_token.strip()
    if settings.push_notifications_enabled:
        unsubscribe_device_from_urgent_topic(device_token=token)
    PushRepository(db_session).disable(token)
    return PushSubscriptionResponse(subscribed=False, topic=settings.fcm_urgent_topic)
