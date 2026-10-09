from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.core.database import Base
from app.models.news import RawNewsItem
from app.repositories.news_repository import NewsRepository
from app.services.official_press_feeds import OfficialPressFeed
from app.services.official_press_matcher import (
    OfficialPressCatalog,
    OfficialRelease,
    find_official_release,
    release_from_entry,
)
from app.services.rss_ingestion_service import RSSIngestionService

_NOW: datetime = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


def _release(title: str, url: str, *, hours_ago: int = 1, name: str = "Polizei") -> OfficialRelease:
    return OfficialRelease(
        title=title,
        url=url,
        name=name,
        published_at=_NOW - timedelta(hours=hours_ago),
    )


def test_matches_police_release_when_the_headline_shares_the_event() -> None:
    found: OfficialRelease | None = find_official_release(
        "Schockanruf in Herne: 88-Jähriger verliert sein Erspartes",
        "Die Polizei sucht Zeugen.",
        _NOW,
        [_release("Nach Schockanruf: Kriminelle bringen Herner um Erspartes", "https://www.presseportal.de/pm/1")],
        min_shared_tokens=3,
        min_title_coverage=0.55,
        max_age_hours=48,
    )

    assert found is not None
    assert found.url == "https://www.presseportal.de/pm/1"
    assert found.name == "Polizei"


def test_skips_unrelated_and_stale_releases() -> None:
    releases: list[OfficialRelease] = [
        _release("Verkehrsunfall auf der Autobahn bei Hamburg", "https://www.presseportal.de/pm/old", hours_ago=80),
        _release("Einbruch in ein Geschäft in München", "https://www.presseportal.de/pm/other"),
    ]

    found: OfficialRelease | None = find_official_release(
        "Schockanruf in Herne: 88-Jähriger verliert sein Erspartes",
        "",
        _NOW,
        releases,
        min_shared_tokens=3,
        min_title_coverage=0.55,
        max_age_hours=48,
    )

    assert found is None


def test_ambiguous_releases_are_not_chosen() -> None:
    title: str = "Nach Schockanruf verliert Herner sein Erspartes"
    releases: list[OfficialRelease] = [
        _release(title, "https://www.presseportal.de/pm/a"),
        _release(title, "https://www.presseportal.de/pm/b"),
    ]

    found: OfficialRelease | None = find_official_release(
        title,
        "",
        _NOW,
        releases,
        min_shared_tokens=3,
        min_title_coverage=0.55,
        max_age_hours=48,
    )

    assert found is None


def test_politics_feed_keeps_only_authority_releases() -> None:
    feed: OfficialPressFeed = OfficialPressFeed(
        key="presseportal_politik",
        name="Behörde",
        url="https://www.presseportal.de/rss/politik.rss2",
        require_institution_word=True,
    )
    party: dict[str, str] = {
        "title": "Luczak: Vertrauen und Kontinuität bei der Bauförderung",
        "link": "https://www.presseportal.de/pm/party",
        "published": "Fri, 09 Oct 2026 08:00:00 GMT",
    }
    ministry: dict[str, str] = {
        "title": "Bundesministerium veröffentlicht neue Regeln für den Verbraucherschutz",
        "link": "https://www.presseportal.de/pm/ministry",
        "published": "Fri, 09 Oct 2026 08:00:00 GMT",
    }

    assert release_from_entry(party, feed) is None
    kept: OfficialRelease | None = release_from_entry(ministry, feed)
    assert kept is not None
    assert kept.name == "Behörde"


def test_ingestion_stores_matched_primary_source() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    rss: bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Welt</title>
<item>
  <title>Schockanruf in Herne: 88-Jaehriger verliert sein Erspartes</title>
  <link>https://www.welt.de/item-1</link>
  <guid>welt-1</guid>
  <description>Die Polizei sucht Zeugen nach dem Schockanruf.</description>
  <pubDate>Fri, 09 Oct 2026 10:00:00 GMT</pubDate>
</item>
</channel></rss>"""
    catalog: OfficialPressCatalog = OfficialPressCatalog.from_releases(
        [
            OfficialRelease(
                title="Nach Schockanruf: Kriminelle bringen Herner um Erspartes",
                url="https://www.presseportal.de/blaulicht/pm/1",
                name="Polizei",
                published_at=datetime(2026, 10, 9, 9, 0, tzinfo=timezone.utc),
            )
        ]
    )
    mock_response: MagicMock = MagicMock()
    mock_response.content = rss
    mock_response.raise_for_status = MagicMock()
    client_cm: MagicMock = MagicMock()
    client_instance: MagicMock = MagicMock()
    client_instance.get = MagicMock(return_value=mock_response)
    client_cm.__enter__ = MagicMock(return_value=client_instance)
    client_cm.__exit__ = MagicMock(return_value=False)

    with session_factory() as session:
        service: RSSIngestionService = RSSIngestionService(NewsRepository(session), official_press=catalog)
        with (
            patch.object(settings, "rss_enabled_source_keys", "welt"),
            patch.object(settings, "rss_allow_unverified_catalog_sources", True),
            patch("app.services.rss_ingestion_service.httpx.Client", return_value=client_cm),
        ):
            service.run()
        row: RawNewsItem | None = session.execute(select(RawNewsItem)).scalar_one_or_none()

    assert row is not None
    assert row.primary_source_url == "https://www.presseportal.de/blaulicht/pm/1"
    assert row.primary_source_name == "Polizei"
