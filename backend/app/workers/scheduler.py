import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.database import SessionLocal
from app.tasks.pipeline_task import run_pipeline_task
from app.tasks.source_url_check_task import run_source_url_check_task
from app.tasks.telegram_digest_task import run_telegram_digest_for_hour

logger: logging.Logger = logging.getLogger(__name__)


def parse_telegram_digest_hours(raw: str) -> list[int]:
    out: list[int] = []
    for part in raw.split(","):
        p: str = part.strip()
        if not p:
            continue
        try:
            h: int = int(p)
        except ValueError:
            continue
        if 0 <= h <= 23:
            out.append(h)
    return sorted(set(out))


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


def _scheduled_telegram_digest(hour: int) -> None:
    with SessionLocal() as db_session:
        run_telegram_digest_for_hour(db_session, hour)


def _scheduled_source_url_check() -> None:
    with SessionLocal() as db_session:
        result = run_source_url_check_task(db_session)
        if result is not None:
            logger.info(
                "Source URL check: checked=%s unavailable=%s alive=%s inconclusive=%s",
                result.checked,
                result.marked_unavailable,
                result.marked_alive,
                result.inconclusive,
            )


def create_scheduler() -> BackgroundScheduler | None:
    scheduler: BackgroundScheduler = BackgroundScheduler()
    jobs_added: int = 0

    if settings.pipeline_scheduler_enabled:
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
        trigger = CronTrigger(minute="0", hour=hour_spec, timezone=tz)
        scheduler.add_job(_scheduled_pipeline_run, trigger, id="pipeline_hourly", replace_existing=True)
        jobs_added += 1

    if settings.telegram_notifications_enabled and settings.telegram_digest_scheduler_enabled:
        tz_digest_name: str = settings.telegram_digest_timezone.strip() or "Europe/Berlin"
        try:
            tz_digest = ZoneInfo(tz_digest_name)
        except Exception:
            logger.warning(
                "Invalid TELEGRAM_DIGEST_TIMEZONE=%r — falling back to Europe/Berlin.",
                tz_digest_name,
            )
            tz_digest = ZoneInfo("Europe/Berlin")

        for hour in parse_telegram_digest_hours(settings.telegram_digest_hours):
            trigger_d = CronTrigger(minute="0", hour=str(hour), timezone=tz_digest)
            scheduler.add_job(
                _scheduled_telegram_digest,
                trigger_d,
                args=[hour],
                id=f"telegram_digest_{hour}",
                replace_existing=True,
            )
            jobs_added += 1

    if settings.source_url_check_scheduler_enabled:
        tz_link_name: str = settings.source_url_check_timezone.strip() or "Europe/Berlin"
        try:
            tz_link = ZoneInfo(tz_link_name)
        except Exception:
            logger.warning(
                "Invalid SOURCE_URL_CHECK_TIMEZONE=%r — falling back to Europe/Berlin.",
                tz_link_name,
            )
            tz_link = ZoneInfo("Europe/Berlin")

        hour_link: int = settings.source_url_check_hour
        trigger_link = CronTrigger(minute="0", hour=str(hour_link), timezone=tz_link)
        scheduler.add_job(
            _scheduled_source_url_check,
            trigger_link,
            id="source_url_check_daily",
            replace_existing=True,
        )
        jobs_added += 1

    if jobs_added == 0:
        return None
    return scheduler
