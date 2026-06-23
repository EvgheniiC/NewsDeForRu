"""Create and consume password-reset tokens."""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.app_user import AppUser
from app.models.password_reset_token import PasswordResetToken
from app.repositories.user_repository import UserRepository
from app.services.email_delivery import try_send_transactional_email
from app.services.passwords import hash_password
from app.services.staff_tokens import refresh_token_hash_hex

_logger: logging.Logger = logging.getLogger(__name__)

GENERIC_ACK: str = (
    "If this email is registered, you will receive password reset instructions shortly."
)


@dataclass(frozen=True)
class ForgotPasswordResult:
    message: str
    dev_reset_link: str | None = None


def _reset_frontend_base_url() -> str:
    base: str = settings.password_reset_frontend_base_url.strip() or settings.public_app_base_url.strip()
    return base.rstrip("/")


def build_reset_link(token_plain: str) -> str:
    base: str = _reset_frontend_base_url()
    if not base:
        return f"/account/reset?token={token_plain}"
    return f"{base}/account/reset?token={token_plain}"


def _invalidate_active_tokens(db: Session, user_id: int) -> None:
    rows = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
    ).scalars()
    now: datetime = datetime.utcnow()
    for row in rows:
        row.used_at = now
        db.add(row)
    db.commit()


def request_password_reset(db: Session, email: str) -> ForgotPasswordResult:
    if not settings.password_reset_enabled:
        return ForgotPasswordResult(message=GENERIC_ACK)

    repo = UserRepository(db)
    user: AppUser | None = repo.get_by_email(email)
    if user is None or not user.is_active:
        return ForgotPasswordResult(message=GENERIC_ACK)

    plain: str = secrets.token_urlsafe(32)
    token_hash: str = refresh_token_hash_hex(plain)
    expires_at: datetime = datetime.utcnow() + timedelta(minutes=settings.password_reset_expire_minutes)

    _invalidate_active_tokens(db, user.id)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    db.commit()

    link: str = build_reset_link(plain)
    body: str = (
        "Вы запросили сброс пароля для аккаунта newsForGermanyRU.\n\n"
        f"Откройте ссылку (действует {settings.password_reset_expire_minutes} мин.):\n{link}\n\n"
        "Если вы не запрашивали сброс, проигнорируйте это письмо.\n"
    )

    dev_link: str | None = None
    sent: bool = try_send_transactional_email(
        to_address=user.email,
        subject="Сброс пароля — newsForGermanyRU",
        body_text=body,
        log_context=f"password_reset user_id={user.id}",
    )
    if sent:
        return ForgotPasswordResult(message=GENERIC_ACK, dev_reset_link=dev_link)
    if settings.app_env.strip().lower() == "development" and settings.password_reset_dev_expose_link:
        dev_link = link
        _logger.warning("password_reset_dev_link user_id=%s link=%s", user.id, link)
    return ForgotPasswordResult(message=GENERIC_ACK, dev_reset_link=dev_link)


def reset_password_with_token(db: Session, token_plain: str, new_password: str) -> None:
    token_hash: str = refresh_token_hash_hex(token_plain.strip())
    row: PasswordResetToken | None = db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).scalar_one_or_none()

    if row is None or row.used_at is not None:
        raise ValueError("invalid_token")
    if row.expires_at.replace(tzinfo=None) < datetime.utcnow():
        raise ValueError("expired_token")

    user: AppUser | None = db.get(AppUser, row.user_id)
    if user is None or not user.is_active:
        raise ValueError("invalid_token")

    user.password_hash = hash_password(new_password)
    row.used_at = datetime.utcnow()
    db.add(user)
    db.add(row)
    db.commit()
    _logger.info("password_reset_success user_id=%s", user.id)
