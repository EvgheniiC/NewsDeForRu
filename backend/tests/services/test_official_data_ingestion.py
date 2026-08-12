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
    EUROSTAT_DATASET_SPECS,
    EurostatIngestionService,
    EurostatResponseTooLargeError,
    GenesisIngestionService,
    build_eurostat_summary,
    build_eurostat_query_params,
    eurostat_key_figures,
    eurostat_payload_revision,
    genesis_item_revision,
    genesis_payload_revision,
    genesis_stable_content,
    normalize_genesis_content,
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


def _eurostat_stream_response(payload: dict[str, object]) -> MagicMock:
    body: bytes = __import__("json").dumps(payload).encode("utf-8")
    response: MagicMock = MagicMock()
    response.headers = {}
    response.raise_for_status.return_value = None
    response.iter_bytes.return_value = [body]
    response.close.return_value = None
    stream_cm: MagicMock = MagicMock()
    stream_cm.__enter__.return_value = response
    stream_cm.__exit__.return_value = False
    return stream_cm


def test_eurostat_query_params_are_germany_scoped_and_bounded() -> None:
    hicp = build_eurostat_query_params(EUROSTAT_DATASET_SPECS["prc_hicp_midx"])
    assert hicp["geo"] == "DE"
    assert hicp["lastTimePeriod"] == "6"
    assert hicp["coicop"] == "CP00"
    assert hicp["unit"] == "I15"

    une = build_eurostat_query_params(EUROSTAT_DATASET_SPECS["une_rt_m"])
    assert une["geo"] == "DE"
    assert une["s_adj"] == "SA"
    assert une["unit"] == "PC_ACT"

    demo = build_eurostat_query_params(EUROSTAT_DATASET_SPECS["demo_pjan"])
    assert demo["geo"] == "DE"
    assert demo["age"] == "TOTAL"
    assert demo["sex"] == "T"


def test_eurostat_json_stat_values_are_decoded_for_llm_context() -> None:
    payload: dict[str, object] = {
        "label": "Population on 1 January by age and sex",
        "updated": "2026-02-01",
        "id": ["age", "sex", "geo", "time"],
        "size": [1, 1, 1, 2],
        "dimension": {
            "age": {"category": {"index": {"TOTAL": 0}, "label": {"TOTAL": "Total"}}},
            "sex": {"category": {"index": {"T": 0}, "label": {"T": "Total"}}},
            "geo": {"category": {"index": {"DE": 0}, "label": {"DE": "Germany"}}},
            "time": {
                "category": {
                    "index": {"2024": 0, "2025": 1},
                    "label": {"2024": "2024", "2025": "2025"},
                }
            },
        },
        "value": {"0": 83_456_045, "1": 83_577_140},
    }

    figures: tuple[str, ...] = eurostat_key_figures(payload)
    summary: str = build_eurostat_summary(
        EUROSTAT_DATASET_SPECS["demo_pjan"],
        payload,
        6000,
    )

    assert figures == (
        "2024: 83 456 045",
        "2025: 83 577 140",
    )
    assert "Key figures (decoded from Eurostat JSON-stat):" in summary
    assert "- 2025: 83 577 140" in summary
    assert "age=TOTAL" in summary
    assert "sex=T" in summary
    assert "Do not claim a breakdown that is excluded by the filters." in summary


def test_eurostat_fetches_allowlisted_datasets_sequentially_with_filters() -> None:
    session, repository = _repository()
    client_instance: MagicMock = MagicMock()
    client_instance.stream.side_effect = [
        _eurostat_stream_response(
            {"label": "HICP", "updated": "2026-08-01", "value": {"0": 120.1}, "size": [1]}
        ),
        _eurostat_stream_response(
            {"label": "Unemployment", "updated": "2026-08-01", "value": {"0": 3.2}, "size": [1]}
        ),
    ]
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
                Settings(eurostat_dataset_codes="prc_hicp_midx,une_rt_m,unknown_code"),
            ).run()

        assert stats.fetched == 2
        assert stats.feeds_failed == 1
        assert len(client_instance.stream.call_args_list) == 2
        first_params: dict[str, str] = client_instance.stream.call_args_list[0].kwargs["params"]
        assert first_params["geo"] == "DE"
        assert first_params["lastTimePeriod"] == "6"
        second_url: str = client_instance.stream.call_args_list[1].args[1]
        assert second_url.endswith("/une_rt_m")
        rows: list[RawNewsItem] = list(session.execute(select(RawNewsItem)).scalars())
        assert len(rows) == 2
        assert all(row.rights_verified for row in rows)
        assert all(row.licence_url for row in rows)
        assert all(row.image_url is None for row in rows)
        assert all("EDITOR NOTES (open dataset" in row.summary for row in rows)
        assert rows[0].title == "Eurostat: HICP monthly index Germany (all-items)"
    finally:
        session.close()


def test_eurostat_skips_duplicate_revision_and_rejects_oversized_response() -> None:
    session, repository = _repository()
    payload: dict[str, object] = {
        "label": "HICP",
        "updated": "2026-08-01",
        "value": {"0": 120.1},
        "size": [1],
    }
    client_instance: MagicMock = MagicMock()
    client_instance.stream.side_effect = [
        _eurostat_stream_response(payload),
        _eurostat_stream_response(payload),
    ]
    client_context: MagicMock = MagicMock()
    client_context.__enter__.return_value = client_instance
    client_context.__exit__.return_value = False

    try:
        with patch(
            "app.services.official_data_ingestion.httpx.Client",
            return_value=client_context,
        ):
            service = EurostatIngestionService(
                repository,
                Settings(eurostat_dataset_codes="prc_hicp_midx"),
            )
            assert service.run().fetched == 1
            assert service.run().fetched == 0
        assert eurostat_payload_revision("prc_hicp_midx", payload).startswith("prc_hicp_midx:")

        oversized: MagicMock = MagicMock()
        oversized.headers = {"Content-Length": "500001"}
        oversized.raise_for_status.return_value = None
        oversized.close.return_value = None
        oversized_cm: MagicMock = MagicMock()
        oversized_cm.__enter__.return_value = oversized
        oversized_cm.__exit__.return_value = False
        client_instance.stream.side_effect = [oversized_cm]
        with patch(
            "app.services.official_data_ingestion.httpx.Client",
            return_value=client_context,
        ):
            stats = EurostatIngestionService(
                repository,
                Settings(
                    eurostat_dataset_codes="prc_hicp_midx",
                    eurostat_max_response_bytes=10_000,
                ),
            ).run()
        assert stats.fetched == 0
        assert stats.feeds_failed == 1
    finally:
        session.close()


def test_eurostat_response_limit_helper_raises() -> None:
    response: MagicMock = MagicMock()
    response.headers = {}
    response.iter_bytes.return_value = [b"12345", b"67890"]
    response.close.return_value = None
    try:
        from app.services.official_data_ingestion import _read_http_body_with_limit

        _read_http_body_with_limit(response, max_bytes=8)
        raise AssertionError("expected EurostatResponseTooLargeError")
    except EurostatResponseTooLargeError:
        response.close.assert_called()


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


def test_genesis_revision_ignores_volatile_envelope_and_csv_headers() -> None:
    first_csv: str = (
        "Erstellt am 04.08.2026 13:17:00\n"
        "© Destatis\n"
        "2023;83456045\n"
        "2024;83500000\n"
    )
    second_csv: str = (
        "Erstellt am 04.08.2026 13:22:00\n"
        "© Destatis\n"
        "2023;83456045\n"
        "2024;83500000\n"
    )
    first: dict[str, object] = {
        "Ident": {"Service": "data", "Method": "table"},
        "Status": {"Code": "0", "Content": "erfolgreich", "Type": "Information"},
        "Parameter": {"name": "12411-0001", "username": "********"},
        "Copyright": "© Destatis, retrieved 2026-08-04T13:17:00",
        "Object": {"Content": first_csv, "Code": "12411-0001"},
    }
    second: dict[str, object] = {
        "Ident": {"Service": "data", "Method": "table"},
        "Status": {"Code": "0", "Content": "ok", "Type": "Information"},
        "Parameter": {"name": "12411-0001", "username": "********"},
        "Copyright": "© Destatis, retrieved 2026-08-04T13:22:00",
        "Object": {"Content": second_csv, "Code": "12411-0001"},
    }
    assert genesis_stable_content(first) == "2023;83456045\n2024;83500000"
    assert normalize_genesis_content(first_csv) == normalize_genesis_content(second_csv)
    assert genesis_payload_revision("12411-0001", first) == genesis_payload_revision(
        "12411-0001",
        second,
    )
    assert genesis_item_revision("12411-0001", first, "31.12.2024") == "12411-0001:upd:31.12.2024"


def test_genesis_skips_duplicate_when_only_envelope_changes() -> None:
    session, repository = _repository()
    content: str = "31.12.2023;83456045\n31.12.2024;83500000"
    meta: MagicMock = MagicMock()
    meta.json.return_value = {"Object": {"Updated": "31.12.2024"}}
    meta.raise_for_status.return_value = None
    response_one: MagicMock = MagicMock()
    response_one.json.return_value = {
        "Copyright": "first-fetch",
        "Object": {"Content": f"Erstellt am 13:17\n{content}"},
    }
    response_one.raise_for_status.return_value = None
    response_two: MagicMock = MagicMock()
    response_two.json.return_value = {
        "Copyright": "second-fetch",
        "Object": {"Content": f"Erstellt am 13:22\n{content}"},
    }
    response_two.raise_for_status.return_value = None
    client_instance: MagicMock = MagicMock()
    # Each run: metadata/table then data/table.
    client_instance.post.side_effect = [meta, response_one, meta, response_two]
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
        assert rows[0].guid == "12411-0001:upd:31.12.2024"
        assert "Bevölkerung Deutschland" in rows[0].title
    finally:
        session.close()


def test_genesis_skips_when_content_hash_matches_previous_source_revision() -> None:
    session, repository = _repository()
    content: str = "2024;110.1"
    meta_empty: MagicMock = MagicMock()
    meta_empty.json.return_value = {"Object": {}}
    meta_empty.raise_for_status.return_value = None
    data_one: MagicMock = MagicMock()
    data_one.json.return_value = {
        "Object": {"Content": f"Erstellt am A\n{content}"},
    }
    data_one.raise_for_status.return_value = None
    data_two: MagicMock = MagicMock()
    data_two.json.return_value = {
        "Object": {"Content": f"Erstellt am B\n{content}"},
    }
    data_two.raise_for_status.return_value = None
    client_instance: MagicMock = MagicMock()
    client_instance.post.side_effect = [meta_empty, data_one, meta_empty, data_two]
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
                Settings(genesis_dataset_codes="61111-0002", genesis_api_token="token"),
            )
            assert service.run().fetched == 1
            assert service.run().fetched == 0
        assert len(list(session.execute(select(RawNewsItem)).scalars())) == 1
    finally:
        session.close()
