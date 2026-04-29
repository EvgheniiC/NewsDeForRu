"""Optional Telegram Bot notifications for auto-published news only."""

from __future__ import annotations

import html
import logging
from typing import Final

import httpx

from app.core.config import Settings, settings

logger: logging.Logger = logging.getLogger(__name__)

_MAX_MESSAGE_CHARS: Final[int] = 3900


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


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
    title_esc: str = html.escape(title_ru.strip() or "(без заголовка)")
    summary_esc: str = html.escape(_truncate(one_sentence_summary.strip(), 900))
    url_esc: str = html.escape(source_url.strip())

    header: str = "✅ <b>Автопубликация</b> — попадёт в ленту без модерации"
    scores_line: str = (
        f"scores: confidence={confidence_score:.2f}, relevance={relevance_score:.2f}"
    )
    lines: list[str] = [
        header,
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


def send_auto_published_notice(
    *,
    title_ru: str,
    one_sentence_summary: str,
    confidence_score: float,
    relevance_score: float,
    source_url: str,
    processed_id: int,
    app_settings: Settings | None = None,
) -> None:
    """POST sendMessage to Telegram; failures are logged only (never raises)."""
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.telegram_notifications_enabled:
        return

    token: str = cfg.telegram_bot_token.strip()
    chat_id: str = cfg.telegram_chat_id.strip()
    if not token or not chat_id:
        logger.warning(
            "Telegram notifications enabled but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is empty"
        )
        return

    text: str = format_auto_published_html(
        title_ru=title_ru,
        one_sentence_summary=one_sentence_summary,
        confidence_score=confidence_score,
        relevance_score=relevance_score,
        source_url=source_url,
        processed_id=processed_id,
    )

    url: str = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict[str, str | bool] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response: httpx.Response = httpx.post(url, json=payload, timeout=20.0)
        response.raise_for_status()
    except Exception:
        logger.exception(
            "Telegram sendMessage failed processed_news_id=%s",
            processed_id,
        )
