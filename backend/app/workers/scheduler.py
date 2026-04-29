import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]

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
    tz_name: str = settings.pipeline_schedule_timezone.strip() or "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        logger.warning(
            "Invalid PIPELINE_SCHEDULE_TIMEZONE=%r — falling back to UTC. Fix timezone name.",
            tz_name,
        )
        tz = ZoneInfo("UTC")

    start_h: int = settings.pipeline_schedule_start_hour
    end_h: int = settings.pipeline_schedule_end_hour
    hour_spec: str = f"{start_h}-{end_h}"

    scheduler: BackgroundScheduler = BackgroundScheduler(timezone=tz)
    trigger = CronTrigger(minute="0", hour=hour_spec, timezone=tz)
    scheduler.add_job(_scheduled_pipeline_run, trigger)
    return scheduler
