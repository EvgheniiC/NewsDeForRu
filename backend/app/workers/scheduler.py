import logging

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.database import SessionLocal
from app.tasks.pipeline_task import run_pipeline_task

logger: logging.Logger = logging.getLogger(__name__)


def _scheduled_pipeline_run() -> None:
    with SessionLocal() as db_session:
        result = run_pipeline_task(db_session)
        if not result.ok:
            logger.error("Scheduled pipeline run failed: %s", result.error)
        else:
            logger.info(
                "Pipeline run: fetched=%s processed=%s feeds_failed=%s",
                result.fetched,
                result.processed,
                result.feeds_failed,
            )


def create_scheduler() -> BackgroundScheduler:
    minutes: int = max(1, settings.pipeline_interval_minutes)
    scheduler: BackgroundScheduler = BackgroundScheduler()
    scheduler.add_job(_scheduled_pipeline_run, "interval", minutes=minutes)
    return scheduler
