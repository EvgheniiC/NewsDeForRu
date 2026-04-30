from __future__ import annotations

from unittest.mock import MagicMock, patch

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]

from app.schemas.news import PipelineRunResponse
from app.workers.scheduler import (
    _scheduled_pipeline_run,
    _scheduled_telegram_digest,
    create_scheduler,
    parse_telegram_digest_hours,
)


def _patch_pipeline_settings(mock_settings: MagicMock) -> None:
    mock_settings.pipeline_scheduler_enabled = True
    mock_settings.pipeline_schedule_start_hour = 6
    mock_settings.pipeline_schedule_end_hour = 22
    mock_settings.pipeline_schedule_timezone = "Europe/Berlin"


def test_create_scheduler_registers_pipeline_job_when_enabled() -> None:
    with patch("app.workers.scheduler.settings") as s:
        _patch_pipeline_settings(s)
        s.telegram_notifications_enabled = False
        s.telegram_digest_scheduler_enabled = True
        sched: BackgroundScheduler | None = create_scheduler()
        assert sched is not None
        assert len(sched.get_jobs()) == 1


def test_create_scheduler_returns_none_when_nothing_enabled() -> None:
    with patch("app.workers.scheduler.settings") as s:
        s.pipeline_scheduler_enabled = False
        s.telegram_notifications_enabled = False
        s.telegram_digest_scheduler_enabled = True
        assert create_scheduler() is None


def test_create_scheduler_adds_digest_jobs() -> None:
    with patch("app.workers.scheduler.settings") as s:
        s.pipeline_scheduler_enabled = False
        s.telegram_notifications_enabled = True
        s.telegram_digest_scheduler_enabled = True
        s.telegram_digest_hours = "7,15,20"
        s.telegram_digest_timezone = "Europe/Berlin"
        sched: BackgroundScheduler | None = create_scheduler()
        assert sched is not None
        assert len(sched.get_jobs()) == 3


def test_parse_telegram_digest_hours() -> None:
    assert parse_telegram_digest_hours("7, 15 ,20") == [7, 15, 20]
    assert parse_telegram_digest_hours("") == []
    assert parse_telegram_digest_hours("bad,7") == [7]


@patch("app.workers.scheduler.run_pipeline_task")
def test_scheduled_pipeline_invokes_task(mock_task: MagicMock) -> None:
    mock_task.return_value = PipelineRunResponse(
        fetched=0,
        feeds_failed=0,
        filtered_out=0,
        clustered=0,
        processed=0,
        published=0,
        needs_review=0,
        run_id="00000000-0000-0000-0000-000000000000",
    )
    with patch("app.workers.scheduler.SessionLocal") as mock_sl:
        session: MagicMock = MagicMock()
        mock_sl.return_value.__enter__.return_value = session
        mock_sl.return_value.__exit__.return_value = None
        _scheduled_pipeline_run()
    mock_task.assert_called_once_with(session)


@patch("app.workers.scheduler.run_pipeline_task")
def test_scheduled_pipeline_logs_on_failure(mock_task: MagicMock) -> None:
    mock_task.return_value = PipelineRunResponse(
        fetched=0,
        feeds_failed=0,
        filtered_out=0,
        clustered=0,
        processed=0,
        published=0,
        needs_review=0,
        run_id="00000000-0000-0000-0000-000000000000",
        ok=False,
        error="e",
    )
    with patch("app.workers.scheduler.SessionLocal") as mock_sl, patch("app.workers.scheduler.logger") as log:
        session: MagicMock = MagicMock()
        mock_sl.return_value.__enter__.return_value = session
        mock_sl.return_value.__exit__.return_value = None
        _scheduled_pipeline_run()
    log.error.assert_called()


@patch("app.workers.scheduler.run_telegram_digest_for_hour")
def test_scheduled_telegram_digest_passes_hour(mock_digest: MagicMock) -> None:
    with patch("app.workers.scheduler.SessionLocal") as mock_sl:
        session: MagicMock = MagicMock()
        mock_sl.return_value.__enter__.return_value = session
        mock_sl.return_value.__exit__.return_value = None
        _scheduled_telegram_digest(15)
    mock_digest.assert_called_once_with(session, 15)


def test_create_scheduler_uses_hourly_cron_in_configured_window() -> None:
    with patch("app.workers.scheduler.settings") as s:
        _patch_pipeline_settings(s)
        s.telegram_notifications_enabled = False
        s.telegram_digest_scheduler_enabled = True
        sched: BackgroundScheduler | None = create_scheduler()
        assert sched is not None
        job = sched.get_jobs()[0]
        assert isinstance(job.trigger, CronTrigger)
