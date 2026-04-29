"""Optional JSON logging and pipeline run id on log records."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.monitoring.pipeline_run_context import get_pipeline_run_id

_configured: bool = False


class RunIdPlainFormatter(logging.Formatter):
    """Prepend correlation id to human-readable log lines when present."""

    def format(self, record: logging.LogRecord) -> str:
        line: str = super().format(record)
        rid: str | None = getattr(record, "pipeline_run_id", None)
        if rid:
            return f"[run_id={rid}] {line}"
        return line


class PipelineRunIdFilter(logging.Filter):
    """Attach ``pipeline_run_id`` to the record when a pipeline run is active."""

    def filter(self, record: logging.LogRecord) -> bool:
        rid: str | None = get_pipeline_run_id()
        if rid is not None:
            record.pipeline_run_id = rid
        else:
            record.pipeline_run_id = None
        return True


class JsonLogFormatter(logging.Formatter):
    """One JSON object per line; suitable for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid: str | None = getattr(record, "pipeline_run_id", None)
        if rid:
            payload["run_id"] = rid
        if record.pathname:
            payload["module"] = record.module
        if record.lineno:
            payload["line"] = record.lineno
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Attach run-id filter; optionally switch root handlers to JSON format (once)."""
    global _configured
    if _configured:
        return
    _configured = True

    run_filter: PipelineRunIdFilter = PipelineRunIdFilter()
    root: logging.Logger = logging.getLogger()
    root.addFilter(run_filter)

    if not settings.log_json and settings.log_prefix_run_id_plain:
        plain_fmt: RunIdPlainFormatter = RunIdPlainFormatter(
            fmt="%(levelname)s %(name)s %(message)s",
        )
        for handler in root.handlers:
            handler.setFormatter(plain_fmt)
    if not settings.log_json:
        return

    json_formatter: JsonLogFormatter = JsonLogFormatter()
    for handler in root.handlers:
        handler.setFormatter(json_formatter)
    if not root.handlers:
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(json_formatter)
        stream.addFilter(run_filter)
        root.addHandler(stream)
