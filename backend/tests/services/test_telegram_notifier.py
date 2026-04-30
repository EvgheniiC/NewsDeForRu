from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.models.news import NewsTopic
from app.services.telegram_notifier import (
    format_auto_published_html,
    format_moderation_approved_html,
    send_auto_published_notice,
    send_moderation_approved_notice,
)


def test_format_auto_published_html() -> None:
    html_out: str = format_auto_published_html(
        title_ru="Заголовок",
        topic=NewsTopic.POLITICS,
        one_sentence_summary="Кратко о событии.",
        source_url="https://example.com/a",
    )
    assert "Автопубликация" not in html_out
    assert "Заголовок" in html_out
    assert "Категория" in html_out
    assert "Политика" in html_out
    assert "confidence" not in html_out.lower()
    assert "relevance" not in html_out.lower()
    assert "processed_news" not in html_out


def test_format_moderation_approved_html() -> None:
    html_out: str = format_moderation_approved_html(
        title_ru="Заголовок",
        topic=NewsTopic.LIFE,
        one_sentence_summary="Кратко о событии.",
        source_url="https://example.com/a",
    )
    assert "Модерация" in html_out
    assert "основную ленту" in html_out
    assert "Жизнь" in html_out
    assert "processed_news" not in html_out


def test_send_notice_skips_when_disabled() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=False,
        telegram_bot_token="secret",
        telegram_chat_id="1",
    )
    with patch("app.services.telegram_notifier.httpx.post") as mock_post:
        send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=1,
            app_settings=cfg,
        )
    mock_post.assert_not_called()


def test_send_notice_posts_when_enabled() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
    )
    mock_resp: MagicMock = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=7,
            app_settings=cfg,
        )

    mock_post.assert_called_once()
    call_kw: dict[str, object] = mock_post.call_args.kwargs
    assert call_kw["json"]["chat_id"] == "999"
    assert "parse_mode" in call_kw["json"]
    body: str = str(call_kw["json"]["text"])
    assert "Автопубликация" not in body
    assert "<b>t</b>" in body
    assert "confidence" not in body.lower()
    assert "processed_news" not in body


def test_send_notice_uses_sendphoto_when_image_url_set() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
    )
    mock_resp: MagicMock = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            image_url="https://cdn.example/p.png",
            processed_id=7,
            app_settings=cfg,
        )

    mock_post.assert_called_once()
    post_url: str = str(mock_post.call_args[0][0])
    assert "sendPhoto" in post_url
    payload: dict[str, object] = mock_post.call_args.kwargs["json"]
    assert payload["photo"] == "https://cdn.example/p.png"
    assert "parse_mode" in payload


def test_send_moderation_notice_posts_when_enabled() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="100",
    )
    mock_resp: MagicMock = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        send_moderation_approved_notice(
            title_ru="t",
            topic=NewsTopic.POLITICS,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=3,
            app_settings=cfg,
        )

    mock_post.assert_called_once()
    body: str = str(mock_post.call_args.kwargs["json"]["text"])
    assert "Модерация" in body
    assert "Автопубликация" not in body
    assert "processed_news" not in body


@pytest.mark.parametrize(
    "missing_token,missing_chat",
    [
        ("", "1"),
        ("tok", ""),
    ],
)
def test_send_notice_missing_credentials_logs_no_network(
    missing_token: str,
    missing_chat: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token=missing_token,
        telegram_chat_id=missing_chat,
    )
    with patch("app.services.telegram_notifier.httpx.post") as mock_post:
        send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=1,
            app_settings=cfg,
        )
    mock_post.assert_not_called()
    assert "empty" in caplog.text.lower() or "telegram" in caplog.text.lower()
