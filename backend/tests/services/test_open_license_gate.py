from __future__ import annotations

from app.services.open_license_gate import LicenseVerdict, classify_license


def test_classify_allows_open_licences() -> None:
    cases: tuple[tuple[dict[str, str], str], ...] = (
        ({"license_id": "cc-zero"}, "CC0 1.0"),
        ({"license_url": "https://creativecommons.org/publicdomain/zero/1.0/"}, "CC0 1.0"),
        ({"license_id": "cc-by-4.0"}, "CC BY"),
        ({"license_id": "CC-BY"}, "CC BY"),
        ({"license_url": "http://dcat-ap.de/def/licenses/dl-by-de/2.0"}, "DL-DE BY 2.0"),
        ({"license_url": "http://dcat-ap.de/def/licenses/cc-by"}, "CC BY"),
        (
            {"license_title": "Datenlizenz Deutschland – Namensnennung – Version 2.0"},
            "DL-DE BY 2.0",
        ),
        ({"license_url": "https://www.govdata.de/dl-de/zero-2-0"}, "DL-DE Zero 2.0"),
    )
    for kwargs, expected_name in cases:
        result = classify_license(**kwargs)
        assert result.verdict == LicenseVerdict.ALLOWED, kwargs
        assert result.canonical_name == expected_name
        assert result.licence_url


def test_classify_blocks_restricted_and_unknown() -> None:
    blocked = classify_license(license_id="cc-by-nc-4.0")
    assert blocked.verdict == LicenseVerdict.BLOCKED

    blocked_nd = classify_license(license_url="https://creativecommons.org/licenses/by-nd/4.0/")
    assert blocked_nd.verdict == LicenseVerdict.BLOCKED

    blocked_sa = classify_license(license_id="cc-by-sa-4.0")
    assert blocked_sa.verdict == LicenseVerdict.BLOCKED

    unknown = classify_license(license_id="my-custom-licence")
    assert unknown.verdict == LicenseVerdict.UNKNOWN

    empty = classify_license()
    assert empty.verdict == LicenseVerdict.UNKNOWN
