from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.schemas.news import PipelineRunResponse


@dataclass
class LastPipelineRunState:
    at_utc: datetime | None = None
    ok: bool = True
    error: str = ""
    fetched: int = 0
    feeds_failed: int = 0
    processed: int = 0


_state: LastPipelineRunState = LastPipelineRunState()


def get_state() -> LastPipelineRunState:
    return _state


def record_from_response(result: PipelineRunResponse) -> None:
    _state.at_utc = datetime.now(timezone.utc)
    _state.ok = result.ok
    _state.error = (result.error or "")[:2000]
    _state.fetched = result.fetched
    _state.feeds_failed = result.feeds_failed
    _state.processed = result.processed
