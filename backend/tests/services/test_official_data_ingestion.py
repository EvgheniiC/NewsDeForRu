from __future__ import annotations

from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.database import Base
from app.models import app_user as _app_user_models
from app.models.news import RawNewsItem
from app.repositories.news_repository import NewsRepository
from app.services.official_data_ingestion import (
    EurostatIngestionService,
    GenesisIngestionService,
    genesis_payload_revision,
    genesis_stable_content,
    parse_dataset_codes,
)

assert _app_user_models.AppUser.__tablename__ == "app_users"


def _repository() -> tuple[Session, NewsRepository]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session: Session = factory()
    return session, NewsRepository(session)


def test_dataset_codes_are_trimmed_deduplicated_and_fail_closed() -> None:
    assert parse_dataset_codes(" a, b,a ,,") == ("a", "b")
    session, repository = _repository()
    try:
        with patch("app.services.official_data_ingestion.httpx.Client") as client:
            assert EurostatIngestionService(repository, Settings(eurostat_dataset_codes="")).run().fetched == 0
            assert GenesisIngestionService(repository, Settings(genesis_dataset_codes="")).run().fetched == 0
        client.assert_not_called()
    finally:
        session.close()


def test_eurostat_fetches_configured_datasets_sequentially_with_legal_metadata() -> None:
    session, repository = _repository()
    response_one: MagicMock = MagicMock()
    response_one.json.return_value = {"label": "First dataset", "value": {"0": 1}}
    response_one.raise_for_status.return_value = None
    response_two: MagicMock = MagicMock()
    response_two.json.return_value = {"label": "Second dataset", "value": {"0": 2}}
    response_two.raise_for_status.return_value = None
    client_instance: MagicMock = MagicMock()
    client_instance.get.side_effect = [response_one, response_two]
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch(
            "app.services.official_data_ingestion.httpx.Client",
            return_value=client_context,
        ):
            stats = EurostatIngestionService(
                repository,
                Settings(eurostat_dataset_codes="first,second"),
            ).run()

        assert stats.fetched == 2
        assert [call.args[0].rsplit("/", 1)[-1] for call in client_instance.get.call_args_list] == [
            "first",
            "second",
        ]
        rows: list[RawNewsItem] = list(session.execute(select(RawNewsItem)).scalars())
        assert all(row.rights_verified for row in rows)
        assert all(row.licence_url for row in rows)
        assert all(row.image_url is None for row in rows)
    finally:
        session.close()


def test_genesis_requires_token_when_dataset_codes_are_configured() -> None:
    session, repository = _repository()
    try:
        with patch("app.services.official_data_ingestion.httpx.Client") as client:
            stats = GenesisIngestionService(
                repository,
                Settings(genesis_dataset_codes="12411-0001", genesis_api_token=""),
            ).run()
        assert stats.fetched == 0
        assert stats.feeds_failed == 1
        client.assert_not_called()
    finally:
        session.close()


def test_genesis_revision_ignores_volatile_envelope_fields() -> None:
    content: str = "Verbraucherpreisindex;2024;110.1"
    first: dict[str, object] = {
        "Ident": {"Service": "data", "Method": "table"},
        "Status": {"Code": "0", "Content": "erfolgreich", "Type": "Information"},
        "Parameter": {"name": "61111-0002", "username": "********"},
        "Copyright": "© Destatis, retrieved 2026-08-04T13:17:00",
        "Object": {"Content": content, "Code": "61111-0002"},
    }
    second: dict[str, object] = {
        "Ident": {"Service": "data", "Method": "table"},
        "Status": {"Code": "0", "Content": "ok", "Type": "Information"},
        "Parameter": {"name": "61111-0002", "username": "********"},
        "Copyright": "© Destatis, retrieved 2026-08-04T13:22:00",
        "Object": {"Content": content, "Code": "61111-0002"},
    }
    assert genesis_stable_content(first) == content
    assert genesis_payload_revision("61111-0002", first) == genesis_payload_revision(
        "61111-0002",
        second,
    )
    changed: dict[str, object] = {
        **second,
        "Object": {"Content": "Verbraucherpreisindex;2024;111.0", "Code": "61111-0002"},
    }
    assert genesis_payload_revision("61111-0002", first) != genesis_payload_revision(
        "61111-0002",
        changed,
    )


def test_genesis_skips_duplicate_when_only_envelope_changes() -> None:
    session, repository = _repository()
    content: str = "Bevölkerung;2024;83194500"
    response_one: MagicMock = MagicMock()
    response_one.json.return_value = {
        "Copyright": "first-fetch",
        "Object": {"Content": content},
    }
    response_one.raise_for_status.return_value = None
    response_two: MagicMock = MagicMock()
    response_two.json.return_value = {
        "Copyright": "second-fetch",
        "Object": {"Content": content},
    }
    response_two.raise_for_status.return_value = None
    client_instance: MagicMock = MagicMock()
    client_instance.post.side_effect = [response_one, response_two]
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch(
            "app.services.official_data_ingestion.httpx.Client",
            return_value=client_context,
        ):
            service = GenesisIngestionService(
                repository,
                Settings(genesis_dataset_codes="12411-0001", genesis_api_token="token"),
            )
            assert service.run().fetched == 1
            assert service.run().fetched == 0
        rows: list[RawNewsItem] = list(session.execute(select(RawNewsItem)).scalars())
        assert len(rows) == 1
        assert "Bevölkerung Deutschland" in rows[0].title
    finally:
        session.close()
