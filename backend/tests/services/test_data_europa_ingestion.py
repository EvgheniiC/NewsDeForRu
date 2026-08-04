from __future__ import annotations

from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.database import Base
from app.models import app_user as _app_user_models
from app.models.news import RawNewsItem, Source
from app.repositories.news_repository import NewsRepository
from app.services.data_europa_ingestion import (
    DataEuropaIngestionService,
    classify_distribution_license,
    data_europa_content_revision,
    is_stable_tabular_distribution,
    select_stable_distributions,
)
from app.services.open_license_gate import LicenseVerdict

assert _app_user_models.AppUser.__tablename__ == "app_users"


def _repository() -> tuple[Session, NewsRepository]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session: Session = factory()
    return session, NewsRepository(session)


def _stream_response(body: bytes, content_type: str = "text/csv") -> MagicMock:
    response: MagicMock = MagicMock()
    response.headers = {"Content-Type": content_type}
    response.raise_for_status.return_value = None
    response.iter_bytes.return_value = [body]
    response.close.return_value = None
    stream_cm: MagicMock = MagicMock()
    stream_cm.__enter__.return_value = response
    stream_cm.__exit__.return_value = False
    return stream_cm


def test_is_stable_tabular_distribution_blocks_api_json() -> None:
    assert is_stable_tabular_distribution(
        "CSV",
        "https://www.regionalstatistik.de/genesisws/downloader/06/tables/AIG-08-2_06.csv",
    )
    assert not is_stable_tabular_distribution(
        "JSON",
        "https://www.regionalstatistik.de/genesisws/rest/2020/GOJsonApi.json",
    )
    assert not is_stable_tabular_distribution(
        "CSV",
        "https://example.de/api/v1/table.csv",
    )


def test_select_stable_distributions_prefers_newest_csv() -> None:
    selected = select_stable_distributions(
        [
            {
                "id": "api",
                "format": {"id": "JSON"},
                "access_url": [
                    "https://www.regionalstatistik.de/genesisws/rest/2020/GOJsonApi.json"
                ],
            },
            {
                "id": "old",
                "format": {"id": "CSV"},
                "access_url": ["https://opendata.example.de/ALO_2020_Q4.csv"],
            },
            {
                "id": "new",
                "format": {"id": "CSV"},
                "download_url": ["https://opendata.example.de/ALO_2026_Q1.csv"],
            },
        ],
        max_dists=1,
    )
    assert len(selected) == 1
    assert selected[0]["id"] == "new"


def test_classify_distribution_license_prefers_distribution_object() -> None:
    result = classify_distribution_license(
        {"licence": "https://example.com/unknown"},
        {
            "license": {
                "resource": "http://dcat-ap.de/def/licenses/dl-by-de/2.0",
                "id": "http://dcat-ap.de/def/licenses/dl-by-de/2.0",
                "label": "dl-by-de/2.0",
            }
        },
    )
    assert result.verdict == LicenseVerdict.ALLOWED
    assert result.canonical_name == "DL-DE BY 2.0"


def test_data_europa_fail_closed_when_ids_empty() -> None:
    session, repository = _repository()
    try:
        with patch("app.services.data_europa_ingestion.httpx.Client") as client:
            stats = DataEuropaIngestionService(
                repository,
                Settings(data_europa_dataset_ids=""),
            ).run()
        assert stats.fetched == 0
        client.assert_not_called()
    finally:
        session.close()


def test_data_europa_ingests_allowed_csv_from_publisher() -> None:
    session, repository = _repository()
    dataset_payload: dict[str, object] = {
        "result": {
            "id": "demo-eu-dataset",
            "title": {"en": "Unemployment indicators", "de": "Arbeitslosigkeit"},
            "publisher": {"name": "Statistische Aemter des Bundes und der Laender", "type": "Agent"},
            "distributions": [
                {
                    "id": "dist-html",
                    "format": {"id": "HTML"},
                    "license": {"resource": "http://dcat-ap.de/def/licenses/dl-by-de/2.0"},
                    "access_url": ["https://publisher.example.de/page.html"],
                },
                {
                    "id": "dist-csv",
                    "format": {"id": "CSV"},
                    "license": {"resource": "http://dcat-ap.de/def/licenses/dl-by-de/2.0"},
                    "access_url": ["https://publisher.example.de/data.csv"],
                },
                {
                    "id": "dist-csv-dup",
                    "format": {"id": "JSON"},
                    "license": {"resource": "http://dcat-ap.de/def/licenses/dl-by-de/2.0"},
                    "access_url": ["https://publisher.example.de/data.csv"],
                },
            ],
        }
    }
    detail_response: MagicMock = MagicMock()
    detail_response.raise_for_status.return_value = None
    detail_response.json.return_value = dataset_payload
    client_instance: MagicMock = MagicMock()
    client_instance.get.return_value = detail_response
    client_instance.stream.return_value = _stream_response(b"year;rate\n2024;5.1\n")
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch("app.services.data_europa_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.data_europa_ingestion.time.sleep"):
                stats = DataEuropaIngestionService(
                    repository,
                    Settings(
                        data_europa_dataset_ids="demo-eu-dataset",
                        data_europa_request_delay_seconds=0,
                    ),
                ).run()
        assert stats.fetched == 1
        assert client_instance.stream.call_count == 1
        assert client_instance.stream.call_args.args[1] == "https://publisher.example.de/data.csv"
        row: RawNewsItem = session.execute(select(RawNewsItem)).scalar_one()
        assert row.rights_verified is True
        assert row.copyright_holder == "Statistische Aemter des Bundes und der Laender"
        assert "data.europa.eu" not in (row.copyright_holder or "").lower()
        assert row.licence == "DL-DE BY 2.0"
        assert row.url == "https://publisher.example.de/data.csv"
        assert "Catalogue: data.europa.eu" in row.summary
        source: Source = session.execute(select(Source)).scalar_one()
        assert source.source_key == "data_europa"
    finally:
        session.close()


def test_data_europa_unknown_license_not_auto_verified_and_html_rejected() -> None:
    session, repository = _repository()
    dataset_payload: dict[str, object] = {
        "result": {
            "id": "unknown-eu",
            "title": {"en": "Custom"},
            "publisher": {"name": "Some Agency"},
            "distributions": [
                {
                    "id": "d1",
                    "format": {"id": "CSV"},
                    "license": {"resource": "https://example.com/custom-licence"},
                    "access_url": ["https://publisher.example.de/a.csv"],
                }
            ],
        }
    }
    detail_response: MagicMock = MagicMock()
    detail_response.raise_for_status.return_value = None
    detail_response.json.return_value = dataset_payload
    client_instance: MagicMock = MagicMock()
    client_instance.get.return_value = detail_response
    client_instance.stream.return_value = _stream_response(b"a,b\n1,2\n")
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch("app.services.data_europa_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.data_europa_ingestion.time.sleep"):
                stats = DataEuropaIngestionService(
                    repository,
                    Settings(data_europa_dataset_ids="unknown-eu", data_europa_request_delay_seconds=0),
                ).run()
        assert stats.fetched == 1
        row: RawNewsItem = session.execute(select(RawNewsItem)).scalar_one()
        assert row.rights_verified is False
        assert not row.licence_url

        # HTML body must not create an item.
        client_instance.stream.return_value = _stream_response(
            b"<!DOCTYPE html><html><body>x</body></html>",
            content_type="text/html",
        )
        detail_response.json.return_value = {
            "result": {
                "id": "html-eu",
                "title": {"en": "HTML trap"},
                "publisher": {"name": "Agency"},
                "distributions": [
                    {
                        "id": "d-html",
                        "format": {"id": "CSV"},
                        "license": {"resource": "http://dcat-ap.de/def/licenses/cc-by"},
                        "access_url": ["https://publisher.example.de/fake.csv"],
                    }
                ],
            }
        }
        with patch("app.services.data_europa_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.data_europa_ingestion.time.sleep"):
                stats_html = DataEuropaIngestionService(
                    repository,
                    Settings(data_europa_dataset_ids="html-eu", data_europa_request_delay_seconds=0),
                ).run()
        assert stats_html.fetched == 0
        assert stats_html.feeds_failed == 1
    finally:
        session.close()


def test_data_europa_blocks_nc_and_skips_create() -> None:
    session, repository = _repository()
    dataset_payload: dict[str, object] = {
        "result": {
            "id": "nc-eu",
            "title": {"en": "NC"},
            "publisher": {"name": "Agency"},
            "distributions": [
                {
                    "id": "d-nc",
                    "format": {"id": "CSV"},
                    "license": {"resource": "https://creativecommons.org/licenses/by-nc/4.0/"},
                    "access_url": ["https://publisher.example.de/nc.csv"],
                }
            ],
        }
    }
    detail_response: MagicMock = MagicMock()
    detail_response.raise_for_status.return_value = None
    detail_response.json.return_value = dataset_payload
    client_instance: MagicMock = MagicMock()
    client_instance.get.return_value = detail_response
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch("app.services.data_europa_ingestion.httpx.Client", return_value=client_context):
            with patch("app.services.data_europa_ingestion.time.sleep"):
                stats = DataEuropaIngestionService(
                    repository,
                    Settings(data_europa_dataset_ids="nc-eu", data_europa_request_delay_seconds=0),
                ).run()
        assert stats.fetched == 0
        client_instance.stream.assert_not_called()
        assert list(session.execute(select(RawNewsItem)).scalars()) == []
        assert data_europa_content_revision("a", "b", b"x").startswith("data_europa:a:b:")
    finally:
        session.close()
