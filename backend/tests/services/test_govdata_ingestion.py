from __future__ import annotations

from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.database import Base
from app.models import app_user as _app_user_models
from app.models.news import RawNewsItem, Source
from app.repositories.news_repository import NewsRepository
from app.services.govdata_ingestion import (
    GovDataIngestionService,
    govdata_content_revision,
    is_text_resource,
)
from app.services.http_fetch_limits import ResponseTooLargeError, read_http_body_with_limit

assert _app_user_models.AppUser.__tablename__ == "app_users"


def _repository() -> tuple[Session, NewsRepository]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session: Session = factory()
    return session, NewsRepository(session)


def _stream_response(body: bytes, headers: dict[str, str] | None = None) -> MagicMock:
    response: MagicMock = MagicMock()
    response.headers = headers or {}
    response.raise_for_status.return_value = None
    response.iter_bytes.return_value = [body]
    response.close.return_value = None
    stream_cm: MagicMock = MagicMock()
    stream_cm.__enter__.return_value = response
    stream_cm.__exit__.return_value = False
    return stream_cm


def test_is_text_resource_accepts_csv_and_blocks_media() -> None:
    assert is_text_resource("CSV", "https://example.com/file")
    assert is_text_resource("", "https://example.com/data.json")
    assert not is_text_resource("PDF", "https://example.com/a.pdf")
    assert not is_text_resource("PNG", "https://example.com/a.png")
    assert not is_text_resource("ZIP", "https://example.com/a.zip")


def test_govdata_fail_closed_when_package_ids_empty() -> None:
    session, repository = _repository()
    try:
        with patch("app.services.govdata_ingestion.httpx.Client") as client:
            stats = GovDataIngestionService(
                repository,
                Settings(govdata_package_ids=""),
            ).run()
        assert stats.fetched == 0
        client.assert_not_called()
    finally:
        session.close()


def test_govdata_ingests_allowed_csv_from_publisher_not_govdata() -> None:
    session, repository = _repository()
    package_payload: dict[str, object] = {
        "success": True,
        "result": {
            "id": "pkg-1",
            "name": "demo-package",
            "title": "Demo Bevoelkerung",
            "license_id": None,
            "organization": {"title": "Bundesministerium des Innern und Heimat"},
            "resources": [
                {
                    "id": "res-csv",
                    "format": "CSV",
                    "license": "http://dcat-ap.de/def/licenses/dl-by-de/2.0",
                    "url": "https://publisher.example.de/data.csv",
                },
                {
                    "id": "res-pdf",
                    "format": "PDF",
                    "license": "http://dcat-ap.de/def/licenses/dl-by-de/2.0",
                    "url": "https://publisher.example.de/data.pdf",
                },
            ],
        },
    }
    package_response: MagicMock = MagicMock()
    package_response.raise_for_status.return_value = None
    package_response.json.return_value = package_payload

    csv_body: bytes = b"year;value\n2020;83.1\n"
    client_instance: MagicMock = MagicMock()
    client_instance.get.return_value = package_response
    client_instance.stream.return_value = _stream_response(csv_body)
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch("app.services.govdata_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.govdata_ingestion.time.sleep"):
                stats = GovDataIngestionService(
                    repository,
                    Settings(
                        govdata_package_ids="demo-package",
                        govdata_request_delay_seconds=0,
                    ),
                ).run()

        assert stats.fetched == 1
        assert stats.feeds_failed == 0
        assert client_instance.stream.call_args.args[1] == "https://publisher.example.de/data.csv"
        rows: list[RawNewsItem] = list(session.execute(select(RawNewsItem)).scalars())
        assert len(rows) == 1
        assert rows[0].rights_verified is True
        assert rows[0].copyright_holder == "Bundesministerium des Innern und Heimat"
        assert rows[0].licence == "DL-DE BY 2.0"
        assert "govdata.de" not in (rows[0].copyright_holder or "").lower()
        assert rows[0].url == "https://publisher.example.de/data.csv"
        assert rows[0].guid == govdata_content_revision("demo-package", "res-csv", csv_body)
        source: Source = session.execute(select(Source)).scalar_one()
        assert source.source_key == "govdata"
    finally:
        session.close()


def test_govdata_unknown_license_goes_to_review_path_not_verified() -> None:
    session, repository = _repository()
    package_payload: dict[str, object] = {
        "success": True,
        "result": {
            "id": "pkg-2",
            "name": "unknown-lic-package",
            "title": "Unknown licence dataset",
            "organization": {"title": "Some Agency"},
            "resources": [
                {
                    "id": "res-1",
                    "format": "CSV",
                    "license": "https://example.com/custom-licence",
                    "url": "https://publisher.example.de/x.csv",
                }
            ],
        },
    }
    package_response: MagicMock = MagicMock()
    package_response.raise_for_status.return_value = None
    package_response.json.return_value = package_payload
    client_instance: MagicMock = MagicMock()
    client_instance.get.return_value = package_response
    client_instance.stream.return_value = _stream_response(b"a,b\n1,2\n")
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch("app.services.govdata_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.govdata_ingestion.time.sleep"):
                stats = GovDataIngestionService(
                    repository,
                    Settings(govdata_package_ids="unknown-lic-package", govdata_request_delay_seconds=0),
                ).run()
        assert stats.fetched == 1
        row: RawNewsItem = session.execute(select(RawNewsItem)).scalar_one()
        assert row.rights_verified is False
        assert not row.licence_url
    finally:
        session.close()


def test_govdata_blocks_nc_license_and_skips_create() -> None:
    session, repository = _repository()
    package_payload: dict[str, object] = {
        "success": True,
        "result": {
            "id": "pkg-3",
            "name": "nc-package",
            "title": "NC dataset",
            "organization": {"title": "Agency"},
            "resources": [
                {
                    "id": "res-nc",
                    "format": "CSV",
                    "license": "https://creativecommons.org/licenses/by-nc/4.0/",
                    "url": "https://publisher.example.de/nc.csv",
                }
            ],
        },
    }
    package_response: MagicMock = MagicMock()
    package_response.raise_for_status.return_value = None
    package_response.json.return_value = package_payload
    client_instance: MagicMock = MagicMock()
    client_instance.get.return_value = package_response
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch("app.services.govdata_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.govdata_ingestion.time.sleep"):
                stats = GovDataIngestionService(
                    repository,
                    Settings(govdata_package_ids="nc-package", govdata_request_delay_seconds=0),
                ).run()
        assert stats.fetched == 0
        client_instance.stream.assert_not_called()
        assert list(session.execute(select(RawNewsItem)).scalars()) == []
    finally:
        session.close()


def test_govdata_skips_duplicate_revision_and_rejects_oversized() -> None:
    session, repository = _repository()
    body: bytes = b"year;value\n2021;1\n"
    package_payload: dict[str, object] = {
        "success": True,
        "result": {
            "id": "pkg-4",
            "name": "dup-package",
            "title": "Dup",
            "organization": {"title": "Agency"},
            "resources": [
                {
                    "id": "res-1",
                    "format": "CSV",
                    "license": "http://dcat-ap.de/def/licenses/dl-by-de/2.0",
                    "url": "https://publisher.example.de/d.csv",
                }
            ],
        },
    }
    package_response: MagicMock = MagicMock()
    package_response.raise_for_status.return_value = None
    package_response.json.return_value = package_payload
    client_instance: MagicMock = MagicMock()
    client_instance.get.return_value = package_response
    client_instance.stream.side_effect = [
        _stream_response(body),
        _stream_response(body),
    ]
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch("app.services.govdata_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.govdata_ingestion.time.sleep"):
                service = GovDataIngestionService(
                    repository,
                    Settings(govdata_package_ids="dup-package", govdata_request_delay_seconds=0),
                )
                assert service.run().fetched == 1
                assert service.run().fetched == 0

        oversized: MagicMock = MagicMock()
        oversized.headers = {"Content-Length": "500001"}
        oversized.raise_for_status.return_value = None
        oversized.close.return_value = None
        oversized_cm: MagicMock = MagicMock()
        oversized_cm.__enter__.return_value = oversized
        oversized_cm.__exit__.return_value = False
        client_instance.stream.side_effect = [oversized_cm]
        with patch("app.services.govdata_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.govdata_ingestion.time.sleep"):
                stats = GovDataIngestionService(
                    repository,
                    Settings(
                        govdata_package_ids="dup-package",
                        govdata_request_delay_seconds=0,
                        govdata_max_response_bytes=10_000,
                    ),
                ).run()
        assert stats.fetched == 0
        assert stats.feeds_failed == 1
    finally:
        session.close()


def test_read_http_body_with_limit_raises() -> None:
    response: MagicMock = MagicMock()
    response.headers = {}
    response.iter_bytes.return_value = [b"12345", b"67890"]
    response.close.return_value = None
    try:
        read_http_body_with_limit(response, max_bytes=8)
        raise AssertionError("expected ResponseTooLargeError")
    except ResponseTooLargeError:
        response.close.assert_called()
