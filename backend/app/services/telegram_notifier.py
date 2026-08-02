"""Optional Telegram Bot API notifications for published news (auto and moderator-approved)."""

from __future__ import annotations

import html
import logging
import time
from typing import Final

import httpx

from app.core.config import Settings, settings
from app.core.http_tls import httpx_verify_arg
from app.models.news import NewsTopic
from app.services.topic_covers import topic_cover_relative_path

logger: logging.Logger = logging.getLogger(__name__)


_MAX_MESSAGE_CHARS: Final[int] = 3900
_MAX_CAPTION_CHARS: Final[int] = 1024

_READ_IN_APP_LABEL: Final[str] = "Читать в приложении"
_AI_COVER_DISCLAIMER: Final[str] = "Иллюстрация: ИИ"

_DIGEST_HEADERS_BY_HOUR: Final[dict[int, str]] = {
    7: "🕖 07:00 — важное за сегодня",
    15: "🕒 15:00 — важное за сегодня",
    20: "🕗 20:00 — важное за сегодня",
}


def _telegram_api_result_ok(response: httpx.Response, processed_id: int, context: str) -> bool:
    """Telegram Bot API may return HTTP 200 with ok=false; require ok==true in JSON."""
    try:
        data: object = response.json()
    except ValueError:
        logger.warning(
            "Telegram non-JSON response processed_news_id=%s context=%s",
            processed_id,
            context,
        )
        return False
    if not isinstance(data, dict):
        logger.warning(
            "Telegram unexpected JSON shape processed_news_id=%s context=%s",
            processed_id,
            context,
        )
        return False
    body: dict[str, object] = data
    if body.get("ok") is True:
        return True
    desc: str = str(body.get("description", ""))[:500]
    logger.warning(
        "Telegram API ok=false processed_news_id=%s context=%s description=%s",
        processed_id,
        context,
        desc,
    )
    return False


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _news_topic_label_ru(topic: NewsTopic) -> str:
    labels: dict[NewsTopic, str] = {
        NewsTopic.POLITICS: "Политика",
        NewsTopic.ECONOMY: "Экономика",
        NewsTopic.LIFE: "Жизнь",
    }
    return labels[topic]


def _read_in_app_url(cfg: Settings, processed_id: int) -> str | None:
    base: str = cfg.public_app_base_url.strip()
    if not base:
        return None
    return f"{base.rstrip('/')}/news/{processed_id}"


def _topic_cover_url(cfg: Settings, topic: NewsTopic, news_id: int) -> str | None:
    """Public HTTPS URL for a stable topic-pool cover (same assets as the frontend)."""
    base: str = cfg.public_app_base_url.strip()
    if not base:
        return None
    path: str | None = topic_cover_relative_path(topic, news_id)
    if path is None:
        return None
    return f"{base.rstrip('/')}{path}"


def _inline_read_in_app_markup(app_url: str) -> dict[str, object]:
    return {
        "inline_keyboard": [
            [{"text": _READ_IN_APP_LABEL, "url": app_url}],
        ]
    }


def _format_published_html(
    *,
    header_line: str,
    title_ru: str,
    topic: NewsTopic,
    one_sentence_summary: str,
    source_url: str,
    source_name: str = "",
    changes_notice: str = "",
) -> str:
    title_esc: str = html.escape(title_ru.strip() or "(без заголовка)")
    summary_esc: str = html.escape(_truncate(one_sentence_summary.strip(), 900))
    url_esc: str = html.escape(source_url.strip())
    category_esc: str = html.escape(_news_topic_label_ru(topic))
    lines: list[str] = []
    if header_line.strip():
        lines.extend([header_line, ""])
    lines.extend(
        [
            f"<b>{title_esc}</b>",
            "",
            summary_esc,
            "",
            f"Категория: {category_esc}",
            "",
            f'Источник: <a href="{url_esc}">{html.escape(source_name.strip() or "оригинал")}</a>',
            "",
            html.escape(changes_notice.strip() or "Неофициальная AI-суммаризация на русском языке."),
            "",
            html.escape(_AI_COVER_DISCLAIMER),
        ]
    )
    body: str = "\n".join(lines)
    return _truncate(body, _MAX_MESSAGE_CHARS)


def format_auto_published_html(
    *,
    title_ru: str,
    topic: NewsTopic,
    one_sentence_summary: str,
    source_url: str,
    source_name: str = "",
    changes_notice: str = "",
) -> str:
    """Build Telegram HTML body for items that passed automatic publication checks."""
    return _format_published_html(
        header_line="",
        title_ru=title_ru,
        topic=topic,
        one_sentence_summary=one_sentence_summary,
        source_url=source_url,
        source_name=source_name,
        changes_notice=changes_notice,
    )


def format_moderation_approved_html(
    *,
    title_ru: str,
    topic: NewsTopic,
    one_sentence_summary: str,
    source_url: str,
    source_name: str = "",
    changes_notice: str = "",
) -> str:
    """Build Telegram HTML body when a moderator approves an item for the main feed."""
    return _format_published_html(
        header_line="",
        title_ru=title_ru,
        topic=topic,
        one_sentence_summary=one_sentence_summary,
        source_url=source_url,
        source_name=source_name,
        changes_notice=changes_notice,
    )


def _digest_header_for_slot_hour(slot_hour: int) -> str:
    return _DIGEST_HEADERS_BY_HOUR.get(slot_hour, "📰 Важное за сегодня")


def format_scheduled_digest_html(
    *,
    slot_hour: int,
    title_ru: str,
    topic: NewsTopic,
    one_sentence_summary: str,
    source_url: str,
    source_name: str = "",
    changes_notice: str = "",
) -> str:
    """Build Telegram HTML for scheduled digest slots (auto-published, non-urgent)."""
    header: str = _digest_header_for_slot_hour(slot_hour)
    return _format_published_html(
        header_line=header,
        title_ru=title_ru,
        topic=topic,
        one_sentence_summary=one_sentence_summary,
        source_url=source_url,
        source_name=source_name,
        changes_notice=changes_notice,
    )


def _send_telegram_message(
    *,
    token: str,
    chat_id: str,
    text: str,
    reply_markup: dict[str, object] | None,
    processed_id: int,
    tls_verify: bool | str,
) -> bool:
    msg_url: str = f"https://api.telegram.org/bot{token}/sendMessage"
    payload_msg: dict[str, object] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup is not None:
        payload_msg["reply_markup"] = reply_markup

    try:
        response = httpx.post(
            msg_url, json=payload_msg, timeout=20.0, verify=tls_verify
        )
        response.raise_for_status()
    except Exception:
        logger.exception(
            "Telegram sendMessage HTTP error processed_news_id=%s",
            processed_id,
        )
        return False
    return _telegram_api_result_ok(response, processed_id, "sendMessage")


def _post_telegram_payload(
    *,
    text: str,
    topic: NewsTopic,
    processed_id: int,
    cfg: Settings,
) -> bool:
    token: str = cfg.telegram_bot_token.strip()
    chat_id: str = cfg.telegram_chat_id.strip()
    if not token or not chat_id:
        logger.warning(
            "Telegram notifications enabled but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is empty"
        )
        return False

    tls_verify: bool | str = httpx_verify_arg(cfg)

    read_url: str | None = _read_in_app_url(cfg, processed_id)
    reply_markup: dict[str, object] | None = (
        _inline_read_in_app_markup(read_url) if read_url is not None else None
    )

    # App topic stock covers (not publisher photos). Requires PUBLIC_APP_BASE_URL.
    photo_url: str | None = _topic_cover_url(cfg, topic, processed_id)
    if photo_url is not None:
        photo_api: str = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload_photo: dict[str, object] = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": _truncate(text, _MAX_CAPTION_CHARS),
            "parse_mode": "HTML",
        }
        if reply_markup is not None:
            payload_photo["reply_markup"] = reply_markup
        try:
            response: httpx.Response = httpx.post(
                photo_api, json=payload_photo, timeout=35.0, verify=tls_verify
            )
            response.raise_for_status()
        except Exception:
            logger.warning(
                "Telegram sendPhoto HTTP error, falling back to sendMessage processed_news_id=%s",
                processed_id,
                exc_info=True,
            )
        else:
            if _telegram_api_result_ok(response, processed_id, "sendPhoto"):
                return True
            logger.warning(
                "Telegram sendPhoto ok=false, falling back to sendMessage processed_news_id=%s",
                processed_id,
            )

    return _send_telegram_message(
        token=token,
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        processed_id=processed_id,
        tls_verify=tls_verify,
    )


def _retrying_post_telegram_payload(
    *,
    text: str,
    topic: NewsTopic,
    processed_id: int,
    cfg: Settings,
    max_attempts: int,
    base_delay: float,
    context: str,
) -> bool:
    """Full transport retries (e.g. moderation / digest) after failed HTTP or ok=false."""
    for attempt in range(max_attempts):
        if _post_telegram_payload(
            text=text,
            topic=topic,
            processed_id=processed_id,
            cfg=cfg,
        ):
            return True
        if attempt < max_attempts - 1:
            delay: float = base_delay * (2**attempt)
            logger.warning(
                "Telegram %s transport retry processed_news_id=%s attempt=%s/%s delay_s=%.1f",
                context,
                processed_id,
                attempt + 1,
                max_attempts,
                delay,
            )
            time.sleep(delay)
    return False


def send_auto_published_notice(
    *,
    title_ru: str,
    topic: NewsTopic,
    one_sentence_summary: str,
    source_url: str,
    processed_id: int,
    source_name: str = "",
    changes_notice: str = "",
    app_settings: Settings | None = None,
    use_urgent_retries: bool = False,
) -> bool:
    """Urgent / breaking auto-publish: send to Telegram immediately. Returns True if API succeeded."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.telegram_notifications_enabled:
        return False

    text: str = format_auto_published_html(
        title_ru=title_ru,
        topic=topic,
        one_sentence_summary=one_sentence_summary,
        source_url=source_url,
        source_name=source_name,
        changes_notice=changes_notice,
    )
    attempts: int = cfg.telegram_urgent_send_max_attempts if use_urgent_retries else 1
    base_delay: float = cfg.telegram_urgent_send_retry_base_seconds

    for attempt in range(attempts):
        ok: bool = _post_telegram_payload(
            text=text, topic=topic, processed_id=processed_id, cfg=cfg
        )
        if ok:
            return True
        if attempt < attempts - 1:
            delay: float = base_delay * (2**attempt)
            logger.warning(
                "Telegram urgent send will retry processed_news_id=%s attempt=%s/%s delay_s=%.1f",
                processed_id,
                attempt + 1,
                attempts,
                delay,
            )
            time.sleep(delay)
    return False


def send_scheduled_digest_notice(
    *,
    title_ru: str,
    topic: NewsTopic,
    one_sentence_summary: str,
    source_url: str,
    processed_id: int,
    slot_hour: int,
    source_name: str = "",
    changes_notice: str = "",
    app_settings: Settings | None = None,
) -> bool:
    """Non-urgent auto-publish digest slot (e.g. 7:00 / 15:00 / 20:00)."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.telegram_notifications_enabled:
        return False

    text: str = format_scheduled_digest_html(
        slot_hour=slot_hour,
        title_ru=title_ru,
        topic=topic,
        one_sentence_summary=one_sentence_summary,
        source_url=source_url,
        source_name=source_name,
        changes_notice=changes_notice,
    )
    return _retrying_post_telegram_payload(
        text=text,
        topic=topic,
        processed_id=processed_id,
        cfg=cfg,
        max_attempts=cfg.telegram_digest_send_max_attempts,
        base_delay=cfg.telegram_digest_send_retry_base_seconds,
        context="digest",
    )


def send_moderation_approved_notice(
    *,
    title_ru: str,
    topic: NewsTopic,
    one_sentence_summary: str,
    source_url: str,
    processed_id: int,
    source_name: str = "",
    changes_notice: str = "",
    app_settings: Settings | None = None,
) -> bool:
    """Notify Telegram right after moderator approval (same channel/settings as autopublish)."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.telegram_notifications_enabled:
        return False

    text: str = format_moderation_approved_html(
        title_ru=title_ru,
        topic=topic,
        one_sentence_summary=one_sentence_summary,
        source_url=source_url,
        source_name=source_name,
        changes_notice=changes_notice,
    )
    return _retrying_post_telegram_payload(
        text=text,
        topic=topic,
        processed_id=processed_id,
        cfg=cfg,
        max_attempts=cfg.telegram_moderation_send_max_attempts,
        base_delay=cfg.telegram_moderation_send_retry_base_seconds,
        context="moderation",
    )


__all__ = [
    "format_auto_published_html",
    "format_moderation_approved_html",
    "format_scheduled_digest_html",
    "send_auto_published_notice",
    "send_moderation_approved_notice",
    "send_scheduled_digest_notice",
]
