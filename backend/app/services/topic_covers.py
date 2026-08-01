"""Topic cover pool: same paths as frontend/public/topic-covers/."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Final

from app.models.news import NewsTopic

_MANIFEST_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent / "data" / "topic_covers_manifest.json"
)


@lru_cache(maxsize=1)
def _load_manifest() -> dict[str, tuple[str, ...]]:
    raw: object = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    out: dict[str, tuple[str, ...]] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, list):
            continue
        files: list[str] = [str(item) for item in value if isinstance(item, str) and item.strip()]
        if files:
            out[key] = tuple(files)
    return out


def topic_cover_relative_path(topic: NewsTopic, news_id: int) -> str | None:
    """Stable cover path for a news item, e.g. ``/topic-covers/life/001.jpg``."""
    files: tuple[str, ...] | None = _load_manifest().get(topic.value)
    if not files:
        return None
    index: int = abs(int(news_id)) % len(files)
    return f"/topic-covers/{topic.value}/{files[index]}"
