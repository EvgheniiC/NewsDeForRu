from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.monitoring import last_pipeline_run
from app.tasks.pipeline_task import run_pipeline_task


def test_run_pipeline_task_swallow_returns_envelope() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory: sessionmaker[Session] = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    with session_factory() as db_session:
        with patch("app.tasks.pipeline_task.PipelineService") as mock_class:
            instance: MagicMock = MagicMock()
            instance.run.side_effect = ValueError("pipeline boom")
            mock_class.return_value = instance
            out = run_pipeline_task(db_session, swallow_errors=True)
    assert out.ok is False
    assert out.error and "pipeline boom" in out.error
    st = last_pipeline_run.get_state()
    assert st.ok is False
    assert "pipeline boom" in st.error


def test_run_pipeline_task_reraise_when_configured() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory: sessionmaker[Session] = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    with session_factory() as db_session:
        with patch("app.tasks.pipeline_task.PipelineService") as mock_class:
            instance: MagicMock = MagicMock()
            instance.run.side_effect = ValueError("no")
            mock_class.return_value = instance
            with pytest.raises(ValueError, match="no"):
                run_pipeline_task(db_session, swallow_errors=False)
