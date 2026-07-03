"""Public in-app feedback form submissions."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps.auth import get_optional_current_user
from app.core.config import settings
from app.models.app_user import AppUser
from app.schemas.feedback import FeedbackSubmitRequest, FeedbackSubmitResponse
from app.services.feedback_service import FeedbackDeliveryContext, submit_feedback
from app.utils.feedback_rate_limit import is_feedback_rate_limited

router: APIRouter = APIRouter(prefix="/feedback", tags=["feedback"])
_logger: logging.Logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    forwarded: str | None = request.headers.get("x-forwarded-for")
    if forwarded:
        first: str = forwarded.split(",")[0].strip()
        if first:
            return first
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"


@router.post("", response_model=FeedbackSubmitResponse)
def post_feedback(
    payload: FeedbackSubmitRequest,
    request: Request,
    current_user: AppUser | None = Depends(get_optional_current_user),
) -> FeedbackSubmitResponse:
    if payload.website and payload.website.strip():
        _logger.info("feedback_honeypot_triggered ip=%s", _client_ip(request))
        return FeedbackSubmitResponse(detail="Спасибо! Сообщение отправлено.")

    ip: str = _client_ip(request)
    if is_feedback_rate_limited(
        key=ip,
        max_requests=settings.feedback_rate_limit_max_per_hour,
    ):
        raise HTTPException(status_code=429, detail="Слишком много сообщений. Попробуйте позже.")

    ctx = FeedbackDeliveryContext(
        client_ip=ip,
        authenticated_user_email=current_user.email if current_user is not None else None,
    )
    try:
        detail: str = submit_feedback(payload, ctx)
    except RuntimeError as exc:
        _logger.error("feedback_delivery_failed ip=%s reason=%s", ip, exc)
        raise HTTPException(
            status_code=503,
            detail="Сервис обратной связи временно недоступен. Напишите нам на email из раздела «Контакты».",
        ) from exc

    return FeedbackSubmitResponse(detail=detail)
