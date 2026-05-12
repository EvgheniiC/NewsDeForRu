from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.core.http_tls import httpx_verify_arg
from app.models.news import NewsTopic
from app.services.telegram_notifier import (
    format_auto_published_html,
    format_moderation_approved_html,
    format_scheduled_digest_html,
    send_auto_published_notice,
    send_moderation_approved_notice,
)


@pytest.fixture(autouse=True)
def reset_http_tls_insecure_warning_flag() -> None:
    setattr(httpx_verify_arg, "_insecure_warned", False)
    yield


def _mock_telegram_response(*, ok: bool, description: str = "") -> MagicMock:
    m: MagicMock = MagicMock(spec=httpx.Response)
    m.raise_for_status = MagicMock()
    m.json.return_value = {"ok": ok, **({"description": description} if description else {})}
    return m


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


def test_format_scheduled_digest_html() -> None:
    html_out: str = format_scheduled_digest_html(
        slot_hour=7,
        title_ru="Заголовок",
        topic=NewsTopic.ECONOMY,
        one_sentence_summary="Кратко.",
        source_url="https://example.com/a",
    )
    assert "07:00" in html_out
    assert "Заголовок" in html_out


def test_format_moderation_approved_html() -> None:
    html_out: str = format_moderation_approved_html(
        title_ru="Заголовок",
        topic=NewsTopic.LIFE,
        one_sentence_summary="Кратко о событии.",
        source_url="https://example.com/a",
    )
    assert "Модерация" not in html_out
    assert "Заголовок" in html_out
    assert "Жизнь" in html_out
    assert "processed_news" not in html_out


def test_send_notice_skips_when_disabled() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=False,
        telegram_bot_token="secret",
        telegram_chat_id="1",
    )
    with patch("app.services.telegram_notifier.httpx.post") as mock_post:
        out: bool = send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=1,
            app_settings=cfg,
        )
    mock_post.assert_not_called()
    assert out is False


def test_send_notice_posts_when_enabled() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
    )
    mock_resp: MagicMock = _mock_telegram_response(ok=True)

    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        out: bool = send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=7,
            app_settings=cfg,
        )

    mock_post.assert_called_once()
    assert out is True
    call_kw: dict[str, object] = mock_post.call_args.kwargs
    assert call_kw["json"]["chat_id"] == "999"
    assert call_kw.get("verify") is True
    assert "parse_mode" in call_kw["json"]
    body: str = str(call_kw["json"]["text"])
    assert "Автопубликация" not in body
    assert "<b>t</b>" in body
    assert "confidence" not in body.lower()
    assert "processed_news" not in body
    assert "reply_markup" not in call_kw["json"]


def test_send_notice_includes_read_in_app_markup_when_base_url_set() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
        public_app_base_url="https://app.example.com",
    )
    mock_resp: MagicMock = _mock_telegram_response(ok=True)

    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=42,
            app_settings=cfg,
        )

    payload: dict[str, object] = mock_post.call_args.kwargs["json"]
    mk: object = payload.get("reply_markup")
    assert isinstance(mk, dict)
    rows: object = mk["inline_keyboard"]
    assert isinstance(rows, list)
    first_row: object = rows[0]
    assert isinstance(first_row, list)
    btn: object = first_row[0]
    assert isinstance(btn, dict)
    assert btn.get("text") == "Читать в приложении"
    assert btn.get("url") == "https://app.example.com/news/42"


def test_send_photo_failure_falls_back_to_send_message() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
    )
    mock_ok: MagicMock = _mock_telegram_response(ok=True)
    call_urls: list[str] = []

    def post_side_effect(url: str, **kwargs: object) -> MagicMock:
        call_urls.append(url)
        if "sendPhoto" in url:
            raise RuntimeError("photo transport failed")
        return mock_ok

    with patch("app.services.telegram_notifier.httpx.post", side_effect=post_side_effect):
        out: bool = send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            image_url="https://cdn.example/p.png",
            processed_id=7,
            app_settings=cfg,
        )

    assert out is True
    assert len(call_urls) == 2
    assert "sendPhoto" in call_urls[0]
    assert "sendMessage" in call_urls[1]


def test_urgent_retries_then_succeeds() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
        telegram_urgent_send_max_attempts=3,
        telegram_urgent_send_retry_base_seconds=0.01,
    )
    mock_ok: MagicMock = _mock_telegram_response(ok=True)
    attempt: list[int] = []

    def post_side_effect(url: str, **kwargs: object) -> MagicMock:
        attempt.append(1)
        if len(attempt) < 3:
            raise RuntimeError("transient")
        return mock_ok

    with patch("app.services.telegram_notifier.httpx.post", side_effect=post_side_effect), patch(
        "app.services.telegram_notifier.time.sleep"
    ) as mock_sleep:
        out: bool = send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=5,
            app_settings=cfg,
            use_urgent_retries=True,
        )

    assert out is True
    assert len(attempt) == 3
    assert mock_sleep.call_count == 2


def test_send_notice_uses_sendphoto_when_image_url_set() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
        public_app_base_url="https://app.example.com",
    )
    mock_resp: MagicMock = _mock_telegram_response(ok=True)

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
    assert "reply_markup" in payload


def test_send_moderation_notice_posts_when_enabled() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="100",
    )
    mock_resp: MagicMock = _mock_telegram_response(ok=True)

    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        ok: bool = send_moderation_approved_notice(
            title_ru="t",
            topic=NewsTopic.POLITICS,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=3,
            app_settings=cfg,
        )

    mock_post.assert_called_once()
    assert ok is True
    body: str = str(mock_post.call_args.kwargs["json"]["text"])
    assert "t" in body
    assert "Модерация" not in body
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


def test_send_notice_fails_when_http_200_but_api_ok_false() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
    )
    mock_resp: MagicMock = _mock_telegram_response(ok=False, description="bot was blocked by the user")
    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        out: bool = send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=9,
            app_settings=cfg,
        )
    mock_post.assert_called_once()
    assert out is False


def test_send_photo_ok_false_falls_back_to_send_message() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
    )
    bad: MagicMock = _mock_telegram_response(ok=False, description="failed to get HTTP URL content")
    good: MagicMock = _mock_telegram_response(ok=True)
    responses: list[MagicMock] = [bad, good]

    def post_side_effect(url: str, **kwargs: object) -> MagicMock:
        return responses.pop(0)

    with patch("app.services.telegram_notifier.httpx.post", side_effect=post_side_effect):
        out: bool = send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            image_url="https://cdn.example/p.png",
            processed_id=11,
            app_settings=cfg,
        )
    assert out is True


def test_send_notice_passes_ca_bundle_path_to_httpx() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
        http_ca_bundle_path=r"C:\certs\corp-bundle.pem",
    )
    mock_resp: MagicMock = _mock_telegram_response(ok=True)
    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=1,
            app_settings=cfg,
        )
    kw: dict[str, object] = mock_post.call_args.kwargs
    assert kw["verify"] == r"C:\certs\corp-bundle.pem"


def test_send_notice_disables_tls_verify_when_configured() -> None:
    cfg: Settings = Settings(
        telegram_notifications_enabled=True,
        telegram_bot_token="TOKEN",
        telegram_chat_id="999",
        http_verify_ssl=False,
    )
    mock_resp: MagicMock = _mock_telegram_response(ok=True)
    with patch("app.services.telegram_notifier.httpx.post", return_value=mock_resp) as mock_post:
        send_auto_published_notice(
            title_ru="t",
            topic=NewsTopic.LIFE,
            one_sentence_summary="s",
            source_url="https://x",
            processed_id=1,
            app_settings=cfg,
        )
    assert mock_post.call_args.kwargs["verify"] is False
