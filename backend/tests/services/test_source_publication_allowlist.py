from __future__ import annotations

from app.services.rss_sources import (
    allowed_rss_source_keys,
    is_source_allowed_for_publication,
    is_source_eligible_for_processing,
)


def test_pending_permission_source_stays_blocked() -> None:
    assert not is_source_allowed_for_publication(
        "ausnews",
        rights_verified=True,
        enabled_source_keys="ausnews",
        allow_unverified=True,
    )
    assert allowed_rss_source_keys("ausnews", allow_unverified=True) == frozenset()


def test_allowed_rss_source_keys_fail_closed() -> None:
    assert allowed_rss_source_keys("") == frozenset()
    assert allowed_rss_source_keys("welt,die_zeit") == frozenset()
    assert allowed_rss_source_keys("destatis") == frozenset({"destatis"})


def test_allowed_rss_source_keys_google_test_keeps_unlicensed_publishers_private() -> None:
    assert allowed_rss_source_keys(
        "welt,die_zeit,zdf,bild",
        allow_unverified=True,
    ) == frozenset()


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


def test_unlicensed_publishers_are_drafted_but_not_public() -> None:
    for source_key in ("die_zeit", "welt", "zdf", "bild"):
        assert not is_source_allowed_for_publication(
            source_key,
            rights_verified=False,
            enabled_source_keys=f"{source_key},bild",
            allow_unverified=True,
        )
        assert is_source_eligible_for_processing(
            source_key,
            rights_verified=False,
            enabled_source_keys=source_key,
            allow_unverified=True,
        )


def test_google_test_does_not_publish_unverified_catalog() -> None:
    assert not is_source_allowed_for_publication(
        "die_zeit",
        rights_verified=False,
        enabled_source_keys="die_zeit,bild",
        allow_unverified=True,
    )
    assert not is_source_allowed_for_publication(
        "bild",
        rights_verified=False,
        enabled_source_keys="die_zeit,bild",
        allow_unverified=True,
    )
    assert is_source_eligible_for_processing(
        "bild",
        rights_verified=False,
        enabled_source_keys="die_zeit,bild",
        allow_unverified=True,
    )
    assert not is_source_eligible_for_processing(
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
