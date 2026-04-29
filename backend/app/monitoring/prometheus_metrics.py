"""Optional Prometheus counters; increment only when ``prometheus_metrics_enabled`` is True."""

from __future__ import annotations

from prometheus_client import Counter

from app.core.config import settings

_pipeline_runs_total: Counter = Counter(
    "news_pipeline_runs_finished_total",
    "Pipeline task finished (scheduled or manual)",
    ("outcome",),
)


def record_pipeline_finished(*, ok: bool) -> None:
    if not settings.prometheus_metrics_enabled:
        return
    _pipeline_runs_total.labels(outcome="success" if ok else "failure").inc()
