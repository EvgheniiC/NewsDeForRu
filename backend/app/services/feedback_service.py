"""Deliver user feedback to the operator inbox."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import settings
from app.schemas.feedback import FeedbackCategory, FeedbackSubmitRequest, feedback_category_label_ru
from app.services.email_delivery import try_send_transactional_email

_logger: logging.Logger = logging.getLogger(__name__)

SUCCESS_DETAIL: str = "Спасибо! Сообщение отправлено."


@dataclass(frozen=True)
class FeedbackDeliveryContext:
    client_ip: str
    authenticated_user_email: str | None = None


def _support_inbox() -> str:
    return settings.support_contact_email.strip()


def _build_email_body(payload: FeedbackSubmitRequest, ctx: FeedbackDeliveryContext) -> str:
    lines: list[str] = [
        "Новое сообщение обратной связи — newsForGermanyRU",
        "",
        f"Категория: {feedback_category_label_ru(payload.category)} ({payload.category.value})",
        "",
        "Сообщение:",
        payload.message.strip(),
        "",
    ]
    if payload.contact_email is not None:
        lines.append(f"Email для ответа: {payload.contact_email}")
    if ctx.authenticated_user_email:
        lines.append(f"Аккаунт (авторизован): {ctx.authenticated_user_email}")
    if payload.page_url:
        lines.append(f"Страница: {payload.page_url}")
    if payload.platform:
        lines.append(f"Платформа: {payload.platform}")
    if payload.app_version:
        lines.append(f"Версия приложения: {payload.app_version}")
    lines.append(f"IP клиента: {ctx.client_ip}")
    return "\n".join(lines)


def _subject_for(category: FeedbackCategory) -> str:
    label: str = feedback_category_label_ru(category)
    return f"[Обратная связь] {label} — newsForGermanyRU"


def submit_feedback(payload: FeedbackSubmitRequest, ctx: FeedbackDeliveryContext) -> str:
    """Persist feedback by emailing the operator. Returns user-facing confirmation text."""
    inbox: str = _support_inbox()
    if not inbox:
        if settings.app_env.strip().lower() == "development":
            _logger.warning(
                "feedback_logged_without_inbox category=%s ip=%s message_len=%s",
                payload.category.value,
                ctx.client_ip,
                len(payload.message.strip()),
            )
            return SUCCESS_DETAIL
        raise RuntimeError("Feedback inbox is not configured")

    body_text: str = _build_email_body(payload, ctx)
    subject: str = _subject_for(payload.category)
    sent: bool = try_send_transactional_email(
        to_address=inbox,
        subject=subject,
        body_text=body_text,
        log_context="feedback",
    )
    if sent:
        return SUCCESS_DETAIL

    if settings.app_env.strip().lower() == "development":
        _logger.warning(
            "feedback_logged_smtp_unavailable category=%s ip=%s",
            payload.category.value,
            ctx.client_ip,
        )
        return SUCCESS_DETAIL

    raise RuntimeError("Unable to deliver feedback email")
