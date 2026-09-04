from __future__ import annotations

from app.services.rss_sources import (
    allowed_rss_source_keys,
    is_source_allowed_for_publication,
)


def test_allowed_rss_source_keys_fail_closed() -> None:
    assert allowed_rss_source_keys("") == frozenset()
    assert allowed_rss_source_keys("welt,die_zeit") == frozenset()
    assert allowed_rss_source_keys("destatis") == frozenset({"destatis"})


def test_allowed_rss_source_keys_google_test_includes_unverified() -> None:
    assert allowed_rss_source_keys(
        "welt,die_zeit,bild",
        allow_unverified=True,
    ) == frozenset({"welt", "die_zeit", "bild"})


def test_catalog_rss_requires_allowlist_and_rights() -> None:
    assert not is_source_allowed_for_publication(
        "welt",
        rights_verified=False,
        enabled_source_keys="destatis",
    )
    assert not is_source_allowed_for_publication(
        "welt",
        rights_verified=True,
        enabled_source_keys="destatis",
    )
    assert not is_source_allowed_for_publication(
        "die_zeit",
        rights_verified=True,
        enabled_source_keys="",
    )


def test_google_test_allows_listed_unverified_catalog() -> None:
    assert is_source_allowed_for_publication(
        "die_zeit",
        rights_verified=False,
        enabled_source_keys="die_zeit,bild",
        allow_unverified=True,
    )
    assert is_source_allowed_for_publication(
        "bild",
        rights_verified=False,
        enabled_source_keys="die_zeit,bild",
        allow_unverified=True,
    )
    assert not is_source_allowed_for_publication(
        "welt",
        rights_verified=False,
        enabled_source_keys="die_zeit,bild",
        allow_unverified=True,
    )


def test_enabled_verified_rss_is_allowed() -> None:
    assert is_source_allowed_for_publication(
        "destatis",
        rights_verified=True,
        enabled_source_keys="destatis,ec_press_corner",
    )


def test_official_data_allowed_when_verified() -> None:
    assert is_source_allowed_for_publication(
        "destatis_genesis",
        rights_verified=True,
        enabled_source_keys="",
    )
    assert not is_source_allowed_for_publication(
        "destatis_genesis",
        rights_verified=False,
        enabled_source_keys="",
    )


def test_non_catalog_source_needs_only_rights_verified() -> None:
    assert is_source_allowed_for_publication(
        "custom_provider",
        rights_verified=True,
        enabled_source_keys="",
    )
    assert not is_source_allowed_for_publication(
        "custom_provider",
        rights_verified=False,
        enabled_source_keys="",
    )
