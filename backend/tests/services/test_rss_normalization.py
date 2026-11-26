from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, repair_implausible_published_dates
from app.models import app_user as _app_user_models
from app.models.news import RawNewsItem, Source
from app.services.rss_entry_normalization import (
    correct_published_at,
    normalize_feedparser_entry,
    parse_entry_published_at,
    strip_html_to_text,
)

assert _app_user_models.AppUser.__tablename__ == "app_users"


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


_NOW: datetime = datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc)


def test_correct_published_at_shifts_year_2926_back_to_2026() -> None:
    stored: datetime = datetime(2926, 4, 1, 5, 19)
    corrected: datetime = correct_published_at(stored, now=_NOW)
    assert corrected == datetime(2026, 4, 1, 5, 19)
    assert corrected.tzinfo is None


def test_correct_published_at_keeps_a_real_publication_time() -> None:
    stored: datetime = datetime(2026, 4, 1, 5, 19)
    assert correct_published_at(stored, now=_NOW) == stored


def test_correct_published_at_replaces_other_far_future_dates_with_now() -> None:
    stored: datetime = datetime(2035, 1, 2, 3, 4, tzinfo=timezone.utc)
    corrected: datetime = correct_published_at(stored, now=_NOW)
    assert corrected == _NOW


def test_repair_rewrites_stored_year_2926() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory: sessionmaker[Session] = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    session: Session = session_factory()
    source: Source = Source(
        source_key="bild",
        name="BILD",
        rss_url="https://www.bild.de/feed/alles.xml",
    )
    session.add(source)
    session.flush()
    raw: RawNewsItem = RawNewsItem(
        source_id=source.id,
        guid="bild-roaming",
        title="t",
        summary="s",
        url="https://www.bild.de/leben-wissen/sparfochs/teurer-fehler",
        published_at=datetime(2926, 4, 1, 5, 19),
    )
    kept: RawNewsItem = RawNewsItem(
        source_id=source.id,
        guid="bild-today",
        title="t2",
        summary="s2",
        url="https://www.bild.de/today",
        published_at=datetime(2026, 11, 26, 8, 0),
    )
    session.add(raw)
    session.add(kept)
    session.commit()

    fixed: int = repair_implausible_published_dates(session)
    session.refresh(raw)
    session.refresh(kept)

    assert fixed == 1
    assert raw.published_at == datetime(2026, 4, 1, 5, 19)
    assert kept.published_at == datetime(2026, 11, 26, 8, 0)
    assert repair_implausible_published_dates(session) == 0
    session.close()
