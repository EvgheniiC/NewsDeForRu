"""Tests for FCM urgent push notifier."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.services import push_notifier


def _enabled_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "push_notifications_enabled": True,
        "fcm_service_account_path": "/tmp/fake-service-account.json",
        "fcm_urgent_topic": "urgent-news",
        "push_urgent_send_max_attempts": 2,
        "push_urgent_send_retry_base_seconds": 0.01,
    }
    base.update(overrides)
    return Settings(**base)


def test_send_urgent_push_disabled_returns_false() -> None:
    cfg: Settings = Settings(push_notifications_enabled=False)
    ok: bool = push_notifier.send_urgent_push_notice(
        title_ru="Test",
        one_sentence_summary="Summary",
        processed_id=1,
        app_settings=cfg,
    )
    assert ok is False


@patch.object(push_notifier, "_ensure_firebase_app", return_value=True)
def test_send_urgent_push_success(_mock_init: MagicMock) -> None:
    mock_send = MagicMock(return_value="projects/x/messages/1")
    mock_message = MagicMock()
    mock_notification = MagicMock()
    mock_android = MagicMock()

    with patch("firebase_admin.messaging.send", mock_send), patch(
        "firebase_admin.messaging.Message", mock_message
    ), patch("firebase_admin.messaging.Notification", mock_notification), patch(
        "firebase_admin.messaging.AndroidConfig", mock_android
    ):
        ok: bool = push_notifier.send_urgent_push_notice(
            title_ru="Заголовок",
            one_sentence_summary="Кратко",
            processed_id=42,
            app_settings=_enabled_settings(),
        )
    assert ok is True
    mock_send.assert_called_once()


@patch.object(push_notifier, "_ensure_firebase_app", return_value=True)
def test_subscribe_device_to_topic(_mock_init: MagicMock) -> None:
    response = MagicMock(success_count=1, failure_count=0, errors=[])
    with patch("firebase_admin.messaging.subscribe_to_topic", return_value=response) as mock_sub:
        ok: bool = push_notifier.subscribe_device_to_urgent_topic(
            device_token="a" * 32,
            app_settings=_enabled_settings(),
        )
    assert ok is True
    mock_sub.assert_called_once_with(["a" * 32], "urgent-news")
