"""Scheduled daily probe of publisher article URLs for recent published news."""

from __future__ import annotations

import logging
import os

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.repositories.job_lock_repository import JobLockRepository
from app.services.source_url_check_service import SourceUrlCheckRunResult, run_source_url_checks

logger: logging.Logger = logging.getLogger(__name__)

SOURCE_URL_CHECK_PG_ADVISORY_KEY: int = 3829154827313


def run_source_url_check_task(
    db_session: Session,
    app_settings: Settings | None = None,
) -> SourceUrlCheckRunResult | None:
    cfg: Settings = app_settings if app_settings is not None else settings
    if not cfg.source_url_check_scheduler_enabled:
        return None

    bind = db_session.get_bind()
    dialect: str = bind.dialect.name
    if dialect == "postgresql":
        pg_got_lock: bool = bool(
            db_session.execute(
                text("SELECT pg_try_advisory_lock(:k)"),
                {"k": SOURCE_URL_CHECK_PG_ADVISORY_KEY},
            ).scalar()
        )
        if not pg_got_lock:
            logger.info("Source URL check skipped: PostgreSQL advisory lock busy")
            return None
    else:
        locks: JobLockRepository = JobLockRepository(db_session)
        holder: str = f"pid-{os.getpid()}"
        if not locks.try_acquire(
            "source_url_check",
            holder,
            cfg.source_url_check_lock_ttl_seconds,
        ):
            logger.info("Source URL check skipped: app_job_locks busy (source_url_check)")
            return None

    try:
        return run_source_url_checks(db_session, cfg)
    finally:
        if dialect == "postgresql":
            db_session.execute(
                text("SELECT pg_advisory_unlock(:k)"),
                {"k": SOURCE_URL_CHECK_PG_ADVISORY_KEY},
            )
            db_session.commit()
        else:
            JobLockRepository(db_session).release("source_url_check")
