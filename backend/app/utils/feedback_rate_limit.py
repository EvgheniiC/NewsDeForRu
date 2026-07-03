"""Simple in-memory rate limit for public feedback submissions."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

_lock: threading.Lock = threading.Lock()
_hits_by_key: dict[str, deque[float]] = defaultdict(deque)


def _prune_old(hits: deque[float], *, window_seconds: float, now: float) -> None:
    cutoff: float = now - window_seconds
    while hits and hits[0] <= cutoff:
        hits.popleft()


def is_feedback_rate_limited(*, key: str, max_requests: int, window_seconds: float = 3600.0) -> bool:
    """Return True when the key exceeded ``max_requests`` inside the sliding window."""
    if max_requests <= 0:
        return False
    now: float = time.monotonic()
    with _lock:
        hits: deque[float] = _hits_by_key[key]
        _prune_old(hits, window_seconds=window_seconds, now=now)
        if len(hits) >= max_requests:
            return True
        hits.append(now)
        return False


def reset_feedback_rate_limits() -> None:
    """Clear counters (tests only)."""
    with _lock:
        _hits_by_key.clear()
