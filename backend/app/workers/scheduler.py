from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]

from app.core.database import SessionLocal
from app.tasks.pipeline_task import run_pipeline_task


def _scheduled_pipeline_run() -> None:
    with SessionLocal() as db_session:
        run_pipeline_task(db_session)


def create_scheduler(interval_minutes: int = 30) -> BackgroundScheduler:
    scheduler: BackgroundScheduler = BackgroundScheduler()
    scheduler.add_job(_scheduled_pipeline_run, "interval", minutes=interval_minutes)
    return scheduler
