"""In-process correlation id for a single pipeline run (logging + API)."""

from __future__ import annotations

import contextvars

_pipeline_run_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "pipeline_run_id",
    default=None,
)


def get_pipeline_run_id() -> str | None:
    return _pipeline_run_id.get()


def set_pipeline_run_id(run_id: str) -> contextvars.Token[str | None]:
    return _pipeline_run_id.set(run_id)


def reset_pipeline_run_id(token: contextvars.Token[str | None]) -> None:
    _pipeline_run_id.reset(token)
