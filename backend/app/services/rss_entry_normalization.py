"""Normalize feedparser entry dicts into stable fields for RawNewsItem."""

from __future__ import annotations

import html
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import mktime
from typing import Any

from app.services.preview_image_service import normalize_image_url

# Match DB column limits
_MAX_GUID_LEN: int = 512
_MAX_TITLE_LEN: int = 512
_MAX_URL_LEN: int = 1024
_MAX_SUMMARY_LEN: int = 200_000

_IMG_SRC_RE: re.Pattern[str] = re.compile(
    r"""<img\s[^>]*\bsrc\s*=\s*(["'])(?P<src>.*?)\1""",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class NormalizedFeedEntry:
    guid: str
    title: str
    summary: str
    url: str
    published_at: datetime
    image_url: str | None

_TAG_RE: re.Pattern[str] = re.compile(r"<[^>]+>")


def strip_html_to_text(raw: str) -> str:
    """Remove simple HTML tags and unescape entities (RSS summaries are often HTML)."""
    if not raw:
        return ""
    no_tags: str = _TAG_RE.sub(" ", raw)
    return html.unescape(re.sub(r"\s+", " ", no_tags).strip())


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 1].rstrip() + "…"


def _first_dict_url(container: Any) -> str:
    if isinstance(container, list) and container:
        first: Any = container[0]
        if isinstance(first, dict):
            raw: Any = first.get("url") or first.get("href")
            if raw:
                return str(raw).strip()
    if isinstance(container, dict):
        raw_d: Any = container.get("url") or container.get("href")
        if raw_d:
            return str(raw_d).strip()
    return ""


def _image_from_media_fields(entry: Mapping[str, Any]) -> str:
    media_content: Any = entry.get("media_content")
    if isinstance(media_content, list):
        for item in media_content:
            if not isinstance(item, dict):
                continue
            url: Any = item.get("url") or item.get("href")
            if url:
                return str(url).strip()
    thumb: Any = entry.get("media_thumbnail")
    u: str = _first_dict_url(thumb)
    if u:
        return u
    return ""


def _image_from_enclosures(entry: Mapping[str, Any]) -> str:
    enclosures: Any = entry.get("enclosures")
    if not isinstance(enclosures, list):
        return ""
    for enc in enclosures:
        if not isinstance(enc, dict):
            continue
        type_val: str = str(enc.get("type") or "").lower()
        if type_val.startswith("image/"):
            href: Any = enc.get("href")
            if href:
                return str(href).strip()
    return ""


def _image_from_summary_html(summary_html: str, article_link: str) -> str:
    match: re.Match[str] | None = _IMG_SRC_RE.search(summary_html)
    if match is None:
        return ""
    raw_src: str = match.group("src").strip()
    return normalize_image_url(article_link, raw_src)


def extract_feed_entry_image_url(entry: Mapping[str, Any], article_link: str) -> str | None:
    """Pick preview image from RSS / Atom fields (no network)."""
    link: str = article_link.strip()
    for getter in (_image_from_media_fields, _image_from_enclosures):
        raw: str = getter(entry)
        if raw:
            abs_u: str = normalize_image_url(link, raw)
            return abs_u or None
    summary_html: str = _extract_summary(entry)
    if summary_html and "<img" in summary_html.lower():
        abs_html: str = _image_from_summary_html(summary_html, link)
        return abs_html or None
    return None


def _extract_summary(entry: Mapping[str, Any]) -> str:
    summary_val: Any = entry.get("summary")
    if summary_val:
        return str(summary_val)
    content: Any = entry.get("content")
    if isinstance(content, list) and content:
        first: Any = content[0]
        if isinstance(first, dict):
            val: Any = first.get("value")
            if val:
                return str(val)
    return ""


def _parse_struct_time_to_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(mktime(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def _parse_rfc822_to_utc(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        dt: datetime = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def parse_entry_published_at(entry: Mapping[str, Any]) -> datetime:
    """Pick the best available timestamp; default to now (UTC)."""
    for parsed_key in ("published_parsed", "updated_parsed"):
        dt: datetime | None = _parse_struct_time_to_utc(entry.get(parsed_key))
        if dt is not None:
            return dt
    for header_key in ("published", "updated"):
        dt = _parse_rfc822_to_utc(entry.get(header_key))
        if dt is not None:
            return dt
    return datetime.now(timezone.utc)


def normalize_feedparser_entry(entry: Mapping[str, Any]) -> NormalizedFeedEntry | None:
    """Map a feedparser entry to normalized DB fields; return None if the item has no stable id."""
    guid_raw: str = str(entry.get("id") or entry.get("guid") or entry.get("link") or entry.get("title") or "").strip()
    if not guid_raw:
        return None

    title_plain: str = strip_html_to_text(str(entry.get("title") or "Untitled"))
    summary_html: str = _extract_summary(entry)
    summary_plain: str = strip_html_to_text(summary_html)
    url: str = str(entry.get("link") or "").strip()
    image_url: str | None = extract_feed_entry_image_url(entry, url)

    return NormalizedFeedEntry(
        guid=_truncate(guid_raw, _MAX_GUID_LEN),
        title=_truncate(title_plain or "Untitled", _MAX_TITLE_LEN),
        summary=_truncate(summary_plain, _MAX_SUMMARY_LEN),
        url=_truncate(url, _MAX_URL_LEN),
        published_at=parse_entry_published_at(entry),
        image_url=image_url,
    )
