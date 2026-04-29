"""Optional Telegram Bot API notifications for published news (auto and moderator-approved)."""

from __future__ import annotations

import html
import logging
from typing import Final

import httpx

from app.core.config import Settings, settings

logger: logging.Logger = logging.getLogger(__name__)

_MAX_MESSAGE_CHARS: Final[int] = 3900
_MAX_CAPTION_CHARS: Final[int] = 1024


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _format_published_html(
    *,
    header_line: str,
    title_ru: str,
    one_sentence_summary: str,
    confidence_score: float,
    relevance_score: float,
    source_url: str,
    processed_id: int,
) -> str:
    title_esc: str = html.escape(title_ru.strip() or "(без заголовка)")
    summary_esc: str = html.escape(_truncate(one_sentence_summary.strip(), 900))
    url_esc: str = html.escape(source_url.strip())
    scores_line: str = (
        f"scores: confidence={confidence_score:.2f}, relevance={relevance_score:.2f}"
    )
    lines: list[str] = [
        header_line,
        "",
        f"<b>{title_esc}</b>",
        "",
        summary_esc,
        "",
        html.escape(scores_line),
        f"id processed_news={processed_id}",
        f'<a href="{url_esc}">источник</a>',
    ]
    body: str = "\n".join(lines)
    return _truncate(body, _MAX_MESSAGE_CHARS)


def format_auto_published_html(
    *,
    title_ru: str,
    one_sentence_summary: str,
    confidence_score: float,
    relevance_score: float,
    source_url: str,
    processed_id: int,
) -> str:
    """Build Telegram HTML body for items that passed automatic publication checks."""
    header: str = "✅ <b>Автопубликация</b> — попадёт в ленту без модерации"
    return _format_published_html(
        header_line=header,
        title_ru=title_ru,
        one_sentence_summary=one_sentence_summary,
        confidence_score=confidence_score,
        relevance_score=relevance_score,
        source_url=source_url,
        processed_id=processed_id,
    )


def format_moderation_approved_html(
    *,
    title_ru: str,
    one_sentence_summary: str,
    confidence_score: float,
    relevance_score: float,
    source_url: str,
    processed_id: int,
) -> str:
    """Build Telegram HTML body when a moderator approves an item for the main feed."""
    header: str = "✅ <b>Модерация</b> — опубликовано в основную ленту"
    return _format_published_html(
        header_line=header,
        title_ru=title_ru,
        one_sentence_summary=one_sentence_summary,
        confidence_score=confidence_score,
        relevance_score=relevance_score,
        source_url=source_url,
        processed_id=processed_id,
    )


def _post_telegram_payload(
    *,
    text: str,
    image_url: str | None,
    processed_id: int,
    cfg: Settings,
) -> None:
    token: str = cfg.telegram_bot_token.strip()
    chat_id: str = cfg.telegram_chat_id.strip()
    if not token or not chat_id:
        logger.warning(
            "Telegram notifications enabled but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is empty"
        )
        return

    photo_candidate: str = (image_url or "").strip()
    use_photo: bool = photo_candidate.startswith(("http://", "https://"))

    if use_photo:
        photo_api: str = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload_photo: dict[str, str | int | bool] = {
            "chat_id": chat_id,
            "photo": photo_candidate,
            "caption": _truncate(text, _MAX_CAPTION_CHARS),
            "parse_mode": "HTML",
        }
        try:
            response: httpx.Response = httpx.post(photo_api, json=payload_photo, timeout=35.0)
            response.raise_for_status()
            return
        except Exception:
            logger.exception(
                "Telegram sendPhoto failed processed_news_id=%s",
                processed_id,
            )

    msg_url: str = f"https://api.telegram.org/bot{token}/sendMessage"
    payload_msg: dict[str, str | int | bool] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = httpx.post(msg_url, json=payload_msg, timeout=20.0)
        response.raise_for_status()
    except Exception:
        logger.exception(
            "Telegram sendMessage failed processed_news_id=%s",
            processed_id,
        )


def send_auto_published_notice(
    *,
    title_ru: str,
    one_sentence_summary: str,
    confidence_score: float,
    relevance_score: float,
    source_url: str,
    processed_id: int,
    image_url: str | None = None,
    app_settings: Settings | None = None,
) -> None:
    """POST sendPhoto or sendMessage to Telegram; failures are logged only (never raises)."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.telegram_notifications_enabled:
        return

    text: str = format_auto_published_html(
        title_ru=title_ru,
        one_sentence_summary=one_sentence_summary,
        confidence_score=confidence_score,
        relevance_score=relevance_score,
        source_url=source_url,
        processed_id=processed_id,
    )
    _post_telegram_payload(text=text, image_url=image_url, processed_id=processed_id, cfg=cfg)


def send_moderation_approved_notice(
    *,
    title_ru: str,
    one_sentence_summary: str,
    confidence_score: float,
    relevance_score: float,
    source_url: str,
    processed_id: int,
    image_url: str | None = None,
    app_settings: Settings | None = None,
) -> None:
    """Notify Telegram right after moderator approval (same channel/settings as autopublish)."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.telegram_notifications_enabled:
        return

    text: str = format_moderation_approved_html(
        title_ru=title_ru,
        one_sentence_summary=one_sentence_summary,
        confidence_score=confidence_score,
        relevance_score=relevance_score,
        source_url=source_url,
        processed_id=processed_id,
    )
    _post_telegram_payload(text=text, image_url=image_url, processed_id=processed_id, cfg=cfg)
