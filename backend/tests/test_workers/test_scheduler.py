from __future__ import annotations

from unittest.mock import MagicMock, patch

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]

from app.schemas.news import PipelineRunResponse
from app.workers.scheduler import _scheduled_pipeline_run, create_scheduler


def test_create_scheduler_registers_one_job() -> None:
    sched: BackgroundScheduler = create_scheduler()
    assert len(sched.get_jobs()) == 1


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
        ok=False,
        error="e",
    )
    with patch("app.workers.scheduler.SessionLocal") as mock_sl, patch("app.workers.scheduler.logger") as log:
        session: MagicMock = MagicMock()
        mock_sl.return_value.__enter__.return_value = session
        mock_sl.return_value.__exit__.return_value = None
        _scheduled_pipeline_run()
    log.error.assert_called()


def test_pipeline_interval_uses_config_minimum_one() -> None:
    with patch("app.workers.scheduler.settings") as s:
        s.pipeline_interval_minutes = 1
        sched: BackgroundScheduler = create_scheduler()
        j = sched.get_jobs()[0]
        assert j.trigger.interval.total_seconds() == 60.0
