from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.models import app_user as _app_user_models
from app.models.news import RawNewsItem, Source
from app.repositories.news_repository import NewsRepository
from app.services.rss_ingestion_service import RSSIngestionService
from app.services.rss_sources import enabled_rss_sources

assert _app_user_models.AppUser.__tablename__ == "app_users"

_MINIMAL_RSS: bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test</title>
<item>
  <title><![CDATA[Hello]]></title>
  <link>https://example.com/item-1</link>
  <guid isPermaLink="true">https://example.com/item-1</guid>
  <description>&lt;p&gt;Plain &amp; bold&lt;/p&gt;</description>
  <pubDate>Thu, 24 Apr 2026 12:00:00 GMT</pubDate>
</item>
</channel></rss>"""


def test_rss_ingestion_persists_stripped_summary() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    mock_response: MagicMock = MagicMock()
    mock_response.content = _MINIMAL_RSS
    mock_response.raise_for_status = MagicMock()

    client_cm: MagicMock = MagicMock()
    client_instance: MagicMock = MagicMock()
    client_instance.get = MagicMock(return_value=mock_response)
    client_cm.__enter__ = MagicMock(return_value=client_instance)
    client_cm.__exit__ = MagicMock(return_value=False)

    with session_factory() as session:
        repo: NewsRepository = NewsRepository(session)
        with (
            patch.object(settings, "rss_enabled_source_keys", "destatis"),
            patch("app.services.rss_ingestion_service.httpx.Client", return_value=client_cm),
        ):
            service: RSSIngestionService = RSSIngestionService(repo)
            stats = service.run()

        assert stats.feeds_failed == 0
        assert stats.fetched >= 1

        raw_rows: list[RawNewsItem] = list(session.execute(select(RawNewsItem)).scalars().all())
        assert len(raw_rows) >= 1
        assert raw_rows[0].summary == "Plain & bold"

        sources: list[Source] = list(session.execute(select(Source)).scalars().all())
        assert all(s.source_key for s in sources)


def test_rss_ingestion_retries_then_succeeds() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    mock_response: MagicMock = MagicMock()
    mock_response.content = _MINIMAL_RSS
    mock_response.raise_for_status = MagicMock()

    fail: bool = True

    def get_side_effect(_: str) -> MagicMock:
        nonlocal fail
        if fail:
            fail = False
            err: httpx.ReadTimeout = httpx.ReadTimeout("timeout", request=MagicMock())
            raise err
        return mock_response

    client_instance: MagicMock = MagicMock()
    client_instance.get = MagicMock(side_effect=get_side_effect)
    client_cm: MagicMock = MagicMock()
    client_cm.__enter__ = MagicMock(return_value=client_instance)
    client_cm.__exit__ = MagicMock(return_value=False)

    with session_factory() as session:
        repo: NewsRepository = NewsRepository(session)
        with (
            patch.object(settings, "rss_enabled_source_keys", "destatis"),
            patch("app.services.rss_ingestion_service.httpx.Client", return_value=client_cm),
        ):
            service: RSSIngestionService = RSSIngestionService(repo)
            stats = service.run()
        assert stats.feeds_failed == 0
        assert client_instance.get.call_count >= 2


def test_rss_ingestion_skips_network_when_no_source_is_approved() -> None:
    repository: MagicMock = MagicMock(spec=NewsRepository)

    with (
        patch.object(settings, "rss_enabled_source_keys", ""),
        patch("app.services.rss_ingestion_service.httpx.Client") as client_class,
    ):
        stats = RSSIngestionService(repository).run()

    assert stats.fetched == 0
    assert stats.feeds_failed == 0
    client_class.assert_not_called()


def test_upsert_source_updates_name_and_url() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with session_factory() as session:
        repo: NewsRepository = NewsRepository(session)
        first: Source = repo.upsert_source(source_key="t1", name="Old", rss_url="https://a/feed")
        assert first.name == "Old"

        second: Source = repo.upsert_source(source_key="t1", name="New", rss_url="https://b/feed")
        assert second.id == first.id
        assert second.name == "New"
        assert second.rss_url == "https://b/feed"


def test_open_rss_sources_have_verified_text_only_policies() -> None:
    sources = enabled_rss_sources("destatis,ec_press_corner")

    assert {source.key for source in sources} == {"destatis", "ec_press_corner"}
    assert all(source.rights_verified for source in sources)
    assert all(source.text_only for source in sources)
    assert all(source.licence and source.licence_url for source in sources)


def test_unverified_rss_sources_remain_disabled_even_when_requested() -> None:
    assert enabled_rss_sources("tagesschau,spiegel,welt,bild") == ()


def test_unverified_rss_sources_enabled_for_google_test() -> None:
    sources = enabled_rss_sources(
        "tagesschau,spiegel,welt,bild",
        allow_unverified=True,
    )
    assert {source.key for source in sources} == {"tagesschau", "spiegel", "welt", "bild"}
    assert all(source.text_only for source in sources)
    assert all(not source.rights_verified for source in sources)
