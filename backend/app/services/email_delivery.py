"""Optional SMTP delivery for transactional email."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

_logger: logging.Logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(settings.smtp_host.strip() and settings.smtp_from_email.strip())


def send_email(*, to_address: str, subject: str, body_text: str) -> None:
    if not smtp_configured():
        raise RuntimeError("SMTP is not configured")

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
        if user:
            client.login(user, password)
        client.send_message(message)
    _logger.info("email_sent to=%s subject=%s", to_address, subject)
