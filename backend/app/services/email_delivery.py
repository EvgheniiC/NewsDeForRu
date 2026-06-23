"""Optional SMTP delivery for transactional email."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import settings

_logger: logging.Logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SmtpConfigStatus:
    host_set: bool
    from_set: bool
    user_set: bool
    password_set: bool

    @property
    def configured(self) -> bool:
        return self.host_set and self.from_set

    @property
    def ready(self) -> bool:
        return self.configured and self.user_set and self.password_set

    @property
    def missing_reason(self) -> str:
        if not self.host_set:
            return "SMTP_HOST is empty"
        if not self.from_set:
            return "SMTP_FROM_EMAIL is empty"
        if not self.user_set:
            return "SMTP_USER is empty"
        if not self.password_set:
            return "SMTP_PASSWORD is empty"
        return "ok"


def smtp_config_status() -> SmtpConfigStatus:
    return SmtpConfigStatus(
        host_set=bool(settings.smtp_host.strip()),
        from_set=bool(settings.smtp_from_email.strip()),
        user_set=bool(settings.smtp_user.strip()),
        password_set=bool(settings.smtp_password),
    )


def smtp_configured() -> bool:
    return smtp_config_status().configured


def smtp_ready() -> bool:
    return smtp_config_status().ready


def log_smtp_startup_status() -> None:
    status: SmtpConfigStatus = smtp_config_status()
    if status.ready:
        _logger.info(
            "smtp_ready host=%s from=%s user=%s",
            settings.smtp_host.strip(),
            settings.smtp_from_email.strip(),
            settings.smtp_user.strip(),
        )
        return
    _logger.warning("smtp_not_ready reason=%s", status.missing_reason)


def send_email(*, to_address: str, subject: str, body_text: str) -> None:
    if not smtp_ready():
        status: SmtpConfigStatus = smtp_config_status()
        raise RuntimeError(f"SMTP is not ready: {status.missing_reason}")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email.strip()
    message["To"] = to_address.strip()
    message.set_content(body_text)

    host: str = settings.smtp_host.strip()
    port: int = settings.smtp_port
    user: str = settings.smtp_user.strip()
    password: str = settings.smtp_password

    with smtplib.SMTP(host, port, timeout=30) as client:
        if settings.smtp_use_tls:
            client.starttls()
        client.login(user, password)
        client.send_message(message)
    _logger.info("email_sent to=%s subject=%s", to_address, subject)


def try_send_transactional_email(
    *,
    to_address: str,
    subject: str,
    body_text: str,
    log_context: str,
) -> bool:
    """Send email; log a clear reason on failure. Returns True when SMTP accepted the message."""
    if not smtp_ready():
        status: SmtpConfigStatus = smtp_config_status()
        _logger.error(
            "transactional_email_not_sent context=%s to=%s reason=%s",
            log_context,
            to_address,
            status.missing_reason,
        )
        return False
    try:
        send_email(to_address=to_address, subject=subject, body_text=body_text)
        return True
    except smtplib.SMTPAuthenticationError:
        _logger.exception(
            "transactional_email_auth_failed context=%s to=%s hint=check SMTP_USER/SMTP_PASSWORD (GMX: app password)",
            log_context,
            to_address,
        )
        return False
    except Exception:
        _logger.exception("transactional_email_send_failed context=%s to=%s", log_context, to_address)
        return False
