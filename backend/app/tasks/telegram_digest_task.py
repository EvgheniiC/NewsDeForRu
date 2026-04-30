"""Scheduled Telegram digest: high-importance auto-published items at fixed local hours."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.models.news import ProcessedNews
from app.repositories.news_repository import NewsRepository
from app.services.telegram_notifier import send_scheduled_digest_notice

logger: logging.Logger = logging.getLogger(__name__)

# TODO(digest-fairness): Reduce starvation when many high-importance items queue up.
# - Track waiting time (e.g. telegram_queued_at or created_at) and boost score for older rows.
# - Optional: force-send items waiting longer than N hours.
# - Blend importance with top-today-style score (sources + freshness).


def run_telegram_digest_for_hour(
    db_session: Session,
    slot_hour: int,
    app_settings: Settings | None = None,
) -> None:
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.telegram_notifications_enabled or not cfg.telegram_digest_scheduler_enabled:
        return

    repository: NewsRepository = NewsRepository(db_session)
    candidates: list[ProcessedNews] = repository.list_telegram_digest_candidates(
        min_importance=cfg.telegram_digest_min_importance,
        limit=cfg.telegram_digest_max_per_slot,
        max_scan=cfg.telegram_digest_candidate_scan_limit,
    )
    if not candidates:
        logger.info("Telegram digest: no candidates for slot_hour=%s", slot_hour)
        return

    for item in candidates:
        ok: bool = send_scheduled_digest_notice(
            title_ru=item.title,
            topic=item.topic,
            one_sentence_summary=item.one_sentence_summary,
            source_url=item.source_url,
            image_url=item.image_url,
            processed_id=item.id,
            slot_hour=slot_hour,
            app_settings=cfg,
        )
        if ok:
            repository.mark_telegram_notified(item.id)


__all__ = ["run_telegram_digest_for_hour"]
