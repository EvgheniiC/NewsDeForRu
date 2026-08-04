from __future__ import annotations

from app.services.tabular_digest import (
    build_open_dataset_summary,
    build_tabular_digest,
    ensure_open_dataset_key_figures,
    format_number,
    is_open_dataset_summary,
    parse_number,
)


def test_parse_number_de_and_en() -> None:
    assert parse_number("83,1") == 83.1
    assert parse_number("1.234,5") == 1234.5
    assert parse_number("1,234.5") == 1234.5
    assert parse_number("12 345") == 12345.0
    assert parse_number("n/a") is None
    assert parse_number("") is None


def test_format_number_compact() -> None:
    assert format_number(83100000.0) == "83 100 000"
    assert format_number(1.25) == "1.25"


def test_build_tabular_digest_csv_semicolon_with_change() -> None:
    csv_text: str = "year;population\n2020;83000000\n2021;83100000\n2022;83200000\n"
    digest: str = build_tabular_digest(csv_text)
    assert "Key figures" in digest
    assert "year, population" in digest
    assert "Rows in sample: 3" in digest
    assert "2022 | 83200000" in digest
    assert "population: last=" in digest
    assert "change=" in digest


def test_build_tabular_digest_json_array() -> None:
    text: str = (
        '[{"age":"0-14","value":11.2},{"age":"15-64","value":53.1},'
        '{"age":"65+","value":22.4}]'
    )
    digest: str = build_tabular_digest(text)
    assert "JSON array of objects" in digest
    assert "age, value" in digest
    assert "65+ | 22.4" in digest


def test_build_open_dataset_summary_includes_notes_and_digest() -> None:
    summary: str = build_open_dataset_summary(
        title="Bevölkerung",
        dataset_uri="https://www.govdata.de/daten/demo",
        resource_uri="https://publisher.example/data.csv",
        publisher="BMI",
        licence_name="DL-DE BY 2.0",
        licence_uri="https://example/license",
        body_text="year;value\n2020;1\n2021;2\n",
        max_body_chars=6000,
    )
    assert is_open_dataset_summary(summary)
    assert "EDITOR NOTES (open dataset" in summary
    assert "Key figures" in summary
    assert "Dataset: Bevölkerung" in summary
    assert "year;value" in summary


def test_is_open_dataset_summary_false_for_rss() -> None:
    assert not is_open_dataset_summary("Kurzmeldung aus Berlin über Mietrecht.")


def test_ensure_open_dataset_key_figures_backfills_legacy_summary() -> None:
    legacy: str = (
        "Dataset: Bevölkerung\n"
        "Dataset URI: https://www.govdata.de/daten/demo\n"
        "Resource URI: https://publisher.example/data.csv\n"
        "Publisher: BMI\n"
        "License: DL-DE BY 2.0\n"
        "License URI: n/a\n\n"
        "year;value\n2020;1\n2021;2\n"
    )
    enriched: str = ensure_open_dataset_key_figures(legacy)
    assert "Key figures" in enriched
    assert "year;value" in enriched
    assert ensure_open_dataset_key_figures(enriched) == enriched
