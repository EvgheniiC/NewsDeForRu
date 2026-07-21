"""Probe publisher article URLs and classify link health."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.core.http_tls import httpx_verify_arg
from app.models.news import ProcessedNews, SourceUrlStatus
from app.repositories.news_repository import NewsRepository
from app.utils.feed_period import period_start_for_lookback_days

logger: logging.Logger = logging.getLogger(__name__)

_DEAD_STATUSES: frozenset[int] = frozenset({404, 410})
_METHOD_NOT_ALLOWED: frozenset[int] = frozenset({405, 501})


@dataclass(frozen=True)
class SourceUrlProbeResult:
    status: SourceUrlStatus
    http_status: int | None


@dataclass(frozen=True)
class SourceUrlCheckRunResult:
    checked: int
    marked_unavailable: int
    marked_alive: int
    inconclusive: int


def classify_http_status(http_status: int) -> SourceUrlStatus:
    """Map an HTTP status to link health. Only 404/410 mean unavailable."""
    if http_status in _DEAD_STATUSES:
        return SourceUrlStatus.UNAVAILABLE
    if 200 <= http_status < 400:
        return SourceUrlStatus.ALIVE
    return SourceUrlStatus.UNKNOWN


def resolve_next_status(
    previous: SourceUrlStatus,
    probe: SourceUrlProbeResult,
) -> SourceUrlStatus:
    """Keep prior status on inconclusive probes; flip on confirmed alive/dead."""
    if probe.status is SourceUrlStatus.UNAVAILABLE:
        return SourceUrlStatus.UNAVAILABLE
    if probe.status is SourceUrlStatus.ALIVE:
        return SourceUrlStatus.ALIVE
    return previous


def probe_source_url(client: httpx.Client, url: str) -> SourceUrlProbeResult:
    """HEAD first; fall back to streamed GET when HEAD is not allowed."""
    cleaned: str = url.strip()
    if not cleaned.startswith(("http://", "https://")):
        return SourceUrlProbeResult(status=SourceUrlStatus.UNKNOWN, http_status=None)

    try:
        head_response: httpx.Response = client.head(cleaned, follow_redirects=True)
        if head_response.status_code not in _METHOD_NOT_ALLOWED:
            return SourceUrlProbeResult(
                status=classify_http_status(head_response.status_code),
                http_status=head_response.status_code,
            )
    except httpx.HTTPError as e:
        logger.debug("Source URL HEAD failed url=%s err=%s", cleaned[:120], e)

    try:
        with client.stream("GET", cleaned, follow_redirects=True) as get_response:
            code: int = get_response.status_code
            return SourceUrlProbeResult(
                status=classify_http_status(code),
                http_status=code,
            )
    except httpx.HTTPError as e:
        logger.debug("Source URL GET failed url=%s err=%s", cleaned[:120], e)
        return SourceUrlProbeResult(status=SourceUrlStatus.UNKNOWN, http_status=None)


def run_source_url_checks(
    db_session: Session,
    app_settings: Settings | None = None,
) -> SourceUrlCheckRunResult:
    """Check published news from the configured lookback window and persist link status."""
    cfg: Settings = app_settings if app_settings is not None else settings
    since: datetime = period_start_for_lookback_days(cfg.source_url_check_lookback_days)
    repository: NewsRepository = NewsRepository(db_session)
    items: list[ProcessedNews] = repository.list_published_since_with_raw(
        published_at_since=since,
        limit=cfg.source_url_check_max_items,
    )

    checked: int = 0
    marked_unavailable: int = 0
    marked_alive: int = 0
    inconclusive: int = 0
    now: datetime = datetime.utcnow()
    timeout: httpx.Timeout = httpx.Timeout(cfg.source_url_check_timeout_seconds)
    headers: dict[str, str] = {"User-Agent": cfg.rss_user_agent}

    with httpx.Client(
        timeout=timeout,
        headers=headers,
        verify=httpx_verify_arg(cfg),
        follow_redirects=True,
    ) as client:
        for item in items:
            probe: SourceUrlProbeResult = probe_source_url(client, item.source_url)
            next_status: SourceUrlStatus = resolve_next_status(item.source_url_status, probe)
            item.source_url_status = next_status
            item.source_url_checked_at = now
            item.source_url_http_status = probe.http_status
            checked += 1
            if next_status is SourceUrlStatus.UNAVAILABLE:
                marked_unavailable += 1
            elif next_status is SourceUrlStatus.ALIVE:
                marked_alive += 1
            else:
                inconclusive += 1

    db_session.commit()
    logger.info(
        "Source URL check: checked=%s unavailable=%s alive=%s inconclusive=%s lookback_days=%s",
        checked,
        marked_unavailable,
        marked_alive,
        inconclusive,
        cfg.source_url_check_lookback_days,
    )
    return SourceUrlCheckRunResult(
        checked=checked,
        marked_unavailable=marked_unavailable,
        marked_alive=marked_alive,
        inconclusive=inconclusive,
    )
