"""Optional FCM push notifications for urgent / breaking news (Android)."""

from __future__ import annotations

import logging
import time
from _thread import LockType
from threading import Lock
from typing import Final, cast

from app.core.config import Settings, settings

logger: logging.Logger = logging.getLogger(__name__)

_MAX_TITLE_CHARS: Final[int] = 120
_MAX_BODY_CHARS: Final[int] = 240
_URGENT_TITLE: Final[str] = "⚡ Срочно"

_firebase_initialized: bool = False
_firebase_init_lock: Final[LockType] = Lock()


def _truncate(text: str, limit: int) -> str:
    cleaned: str = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "…"


def _ensure_firebase_app(cfg: Settings) -> bool:
    global _firebase_initialized
    path: str = cfg.fcm_service_account_path.strip()
    if not path:
        logger.warning("Push notifications enabled but FCM_SERVICE_ACCOUNT_PATH is empty")
        return False
    if _firebase_initialized:
        return True

    with _firebase_init_lock:
        if _firebase_initialized:
            return True
        try:
            import firebase_admin  # type: ignore[import-untyped]
            from firebase_admin import credentials

            try:
                firebase_admin.get_app()
            except ValueError:
                cred = credentials.Certificate(path)
                try:
                    firebase_admin.initialize_app(cred)
                except ValueError:
                    # Another initializer may have created the default app concurrently.
                    firebase_admin.get_app()
            _firebase_initialized = True
            return True
        except Exception:
            logger.exception("Failed to initialize Firebase Admin SDK")
            return False


def subscribe_device_to_urgent_topic(*, device_token: str, app_settings: Settings | None = None) -> bool:
    """Register an Android FCM token on the urgent-news topic."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.push_notifications_enabled:
        return False
    if not _ensure_firebase_app(cfg):
        return False

    try:
        from firebase_admin import messaging

        response = messaging.subscribe_to_topic([device_token], cfg.fcm_urgent_topic)
        if response.failure_count > 0:
            for err in response.errors:
                logger.warning(
                    "FCM subscribe_to_topic error reason=%s index=%s",
                    err.reason,
                    err.index,
                )
            return False
        return cast(bool, response.success_count > 0)
    except Exception:
        logger.exception("FCM subscribe_to_topic failed")
        return False


def unsubscribe_device_from_urgent_topic(*, device_token: str, app_settings: Settings | None = None) -> bool:
    """Remove an Android FCM token from the urgent-news topic."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.push_notifications_enabled:
        return True
    if not _ensure_firebase_app(cfg):
        return False

    try:
        from firebase_admin import messaging

        response = messaging.unsubscribe_from_topic([device_token], cfg.fcm_urgent_topic)
        if response.failure_count > 0:
            for err in response.errors:
                logger.warning(
                    "FCM unsubscribe_from_topic error reason=%s index=%s",
                    err.reason,
                    err.index,
                )
        return cast(bool, response.success_count > 0 or response.failure_count == 0)
    except Exception:
        logger.exception("FCM unsubscribe_from_topic failed")
        return False


def send_urgent_push_notice(
    *,
    title_ru: str,
    one_sentence_summary: str,
    processed_id: int,
    source_name: str = "",
    source_url: str = "",
    app_settings: Settings | None = None,
    use_urgent_retries: bool = False,
) -> bool:
    """Broadcast urgent news to the FCM topic. Returns True if the API call succeeded."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.push_notifications_enabled:
        return False
    if not _ensure_firebase_app(cfg):
        return False

    attribution: str = f"Источник: {source_name.strip()}" if source_name.strip() else ""
    body_parts: list[str] = [part for part in (one_sentence_summary or title_ru, attribution) if part]
    body: str = _truncate("\n".join(body_parts), _MAX_BODY_CHARS)
    notification_title: str = _truncate(title_ru, _MAX_TITLE_CHARS)

    attempts: int = cfg.push_urgent_send_max_attempts if use_urgent_retries else 1
    base_delay: float = cfg.push_urgent_send_retry_base_seconds

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(
                title=_URGENT_TITLE,
                body=f"{notification_title}\n{body}" if body else notification_title,
            ),
            data={
                "news_id": str(processed_id),
                "path": f"/news/{processed_id}",
                "source_name": source_name,
                "source_url": source_url,
            },
            topic=cfg.fcm_urgent_topic,
            android=messaging.AndroidConfig(priority="high"),
        )

        for attempt in range(attempts):
            try:
                messaging.send(message)
                return True
            except Exception:
                logger.exception(
                    "FCM urgent push send failed processed_news_id=%s attempt=%s/%s",
                    processed_id,
                    attempt + 1,
                    attempts,
                )
                if attempt < attempts - 1:
                    delay: float = base_delay * (2**attempt)
                    time.sleep(delay)
        return False
    except Exception:
        logger.exception("FCM urgent push build/send failed processed_news_id=%s", processed_id)
        return False


__all__ = [
    "send_urgent_push_notice",
    "subscribe_device_to_urgent_topic",
    "unsubscribe_device_from_urgent_topic",
]
