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
