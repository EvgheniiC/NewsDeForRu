"""Send and consume email verification tokens after reader registration."""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.app_user import AppUser
from app.models.email_verification_token import EmailVerificationToken
from app.repositories.user_repository import UserRepository
from app.services.email_delivery import send_email, smtp_configured
from app.services.staff_tokens import refresh_token_hash_hex

_logger: logging.Logger = logging.getLogger(__name__)

REGISTER_ACK: str = "Check your email to confirm your account."
RESEND_ACK: str = "If this email is registered and not yet confirmed, you will receive a verification link shortly."


@dataclass(frozen=True)
class RegisterVerificationResult:
    message: str
    dev_verification_link: str | None = None


def _verification_frontend_base_url() -> str:
    base: str = settings.password_reset_frontend_base_url.strip() or settings.public_app_base_url.strip()
    return base.rstrip("/")


def build_verification_link(token_plain: str) -> str:
    base: str = _verification_frontend_base_url()
    if not base:
        return f"/account/verify?token={token_plain}"
    return f"{base}/account/verify?token={token_plain}"


def _invalidate_active_tokens(db: Session, user_id: int) -> None:
    rows = db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None),
        )
    ).scalars()
    now: datetime = datetime.utcnow()
    for row in rows:
        row.used_at = now
        db.add(row)
    db.commit()


def _issue_verification_token(db: Session, user_id: int) -> str:
    plain: str = secrets.token_urlsafe(32)
    token_hash: str = refresh_token_hash_hex(plain)
    expires_at: datetime = datetime.utcnow() + timedelta(minutes=settings.email_verification_expire_minutes)

    _invalidate_active_tokens(db, user_id)
    db.add(
        EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    db.commit()
    return plain


def _send_verification_email(user: AppUser, link: str) -> str | None:
    body: str = (
        "Подтвердите регистрацию в newsForGermanyRU.\n\n"
        f"Откройте ссылку (действует {settings.email_verification_expire_minutes} мин.):\n{link}\n\n"
        "Если вы не регистрировались, проигнорируйте это письмо.\n"
    )

    dev_link: str | None = None
    if smtp_configured():
        try:
            send_email(
                to_address=user.email,
                subject="Подтвердите email — newsForGermanyRU",
                body_text=body,
            )
        except Exception:
            _logger.exception("email_verification_send_failed user_id=%s", user.id)
    elif settings.app_env.strip().lower() == "development" and settings.email_verification_dev_expose_link:
        dev_link = link
        _logger.warning("email_verification_dev_link user_id=%s link=%s", user.id, link)
    else:
        _logger.warning(
            "email_verification_email_skipped_smtp_not_configured user_id=%s",
            user.id,
        )
    return dev_link


def send_registration_verification(db: Session, user: AppUser) -> RegisterVerificationResult:
    if not settings.email_verification_enabled:
        return RegisterVerificationResult(message=REGISTER_ACK)

    plain: str = _issue_verification_token(db, user.id)
    link: str = build_verification_link(plain)
    dev_link: str | None = _send_verification_email(user, link)
    return RegisterVerificationResult(message=REGISTER_ACK, dev_verification_link=dev_link)


def resend_verification_email(db: Session, email: str) -> RegisterVerificationResult:
    if not settings.email_verification_enabled:
        return RegisterVerificationResult(message=RESEND_ACK)

    repo = UserRepository(db)
    user: AppUser | None = repo.get_by_email(email)
    if user is None or not user.is_active or user.is_email_verified():
        return RegisterVerificationResult(message=RESEND_ACK)

    plain: str = _issue_verification_token(db, user.id)
    link: str = build_verification_link(plain)
    dev_link: str | None = _send_verification_email(user, link)
    return RegisterVerificationResult(message=RESEND_ACK, dev_verification_link=dev_link)


def verify_email_with_token(db: Session, token_plain: str) -> AppUser:
    token_hash: str = refresh_token_hash_hex(token_plain.strip())
    row: EmailVerificationToken | None = db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    ).scalar_one_or_none()

    if row is None or row.used_at is not None:
        raise ValueError("invalid_token")
    if row.expires_at.replace(tzinfo=None) < datetime.utcnow():
        raise ValueError("expired_token")

    user: AppUser | None = db.get(AppUser, row.user_id)
    if user is None or not user.is_active:
        raise ValueError("invalid_token")

    now: datetime = datetime.utcnow()
    user.email_verified_at = now
    row.used_at = now
    db.add(user)
    db.add(row)
    db.commit()
    db.refresh(user)
    _logger.info("email_verification_success user_id=%s", user.id)
    return user
