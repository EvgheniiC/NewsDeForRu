from __future__ import annotations

from datetime import datetime, timezone

from app.services.rss_entry_normalization import (
    normalize_feedparser_entry,
    parse_entry_published_at,
    strip_html_to_text,
)


def test_strip_html_removes_tags_and_unescapes() -> None:
    assert strip_html_to_text("<p>Hello &amp; <b>world</b></p>") == "Hello & world"


def test_normalize_feedparser_entry_strips_summary() -> None:
    entry: dict[str, str] = {
        "id": "urn:uuid:1",
        "title": "Title",
        "link": "https://example.com/x",
        "summary": "<div>Line <br/> two</div>",
        "published": "Thu, 24 Apr 2026 12:00:00 GMT",
    }
    normalized = normalize_feedparser_entry(entry)
    assert normalized is not None
    assert normalized.guid == "urn:uuid:1"
    assert normalized.summary == "Line two"
    assert normalized.url == "https://example.com/x"


def test_normalize_returns_none_without_id() -> None:
    assert normalize_feedparser_entry({"title": "", "link": ""}) is None


def test_normalize_extracts_image_from_enclosure() -> None:
    entry: dict[str, object] = {
        "id": "e1",
        "title": "T",
        "link": "https://example.com/page",
        "summary": "text",
        "enclosures": [{"type": "image/jpeg", "href": "https://cdn.example/photo.jpg"}],
    }
    normalized = normalize_feedparser_entry(entry)
    assert normalized is not None
    assert normalized.image_url == "https://cdn.example/photo.jpg"


def test_normalize_extracts_image_from_summary_img() -> None:
    entry: dict[str, str] = {
        "id": "e2",
        "title": "T",
        "link": "https://example.com/post",
        "summary": '<p><img src="/thumb.png" /></p>',
    }
    normalized = normalize_feedparser_entry(entry)
    assert normalized is not None
    assert normalized.image_url == "https://example.com/thumb.png"


def test_parse_entry_published_at_uses_rfc822_when_no_struct() -> None:
    entry: dict[str, str] = {"published": "Thu, 24 Apr 2026 12:00:00 GMT"}
    dt: datetime = parse_entry_published_at(entry)
    assert dt.tzinfo == timezone.utc
    assert dt.date().isoformat() == "2026-04-24"
