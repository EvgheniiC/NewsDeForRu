"""Fail-closed license classification for open-data catalogues (GovData, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LicenseVerdict(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LicenseClassification:
    verdict: LicenseVerdict
    canonical_name: str
    licence_url: str


# (aliases substring-matched on normalized text, display name, default URI)
_ALLOWED_LICENCES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (
        ("cc0", "cc-zero", "cc0-1.0", "cc0 1.0", "creative commons zero", "/publicdomain/zero/"),
        "CC0 1.0",
        "https://creativecommons.org/publicdomain/zero/1.0/",
    ),
    (
        (
            "cc-by-4.0",
            "cc-by-3.0",
            "cc by 4.0",
            "cc by 3.0",
            "creativecommons.org/licenses/by/4.0",
            "creativecommons.org/licenses/by/3.0",
            "licenses/by/4.0",
            "licenses/by/3.0",
        ),
        "CC BY",
        "https://creativecommons.org/licenses/by/4.0/",
    ),
    (
        (
            "dl-de-zero-2.0",
            "dl-de/zero-2.0",
            "dl-de zero 2.0",
            "dl-de-zero_2_0",
            "datenlizenz deutschland - zero - version 2.0",
            "govdata.de/dl-de/zero-2-0",
            "dcat-ap.de/def/licenses/dl-zero-de/2.0",
            "licenses/dl-zero-de/2.0",
        ),
        "DL-DE Zero 2.0",
        "https://www.govdata.de/dl-de/zero-2-0",
    ),
    (
        (
            "dl-de-by-2.0",
            "dl-de/by-2.0",
            "dl-de by 2.0",
            "dl-de-by_2_0",
            "datenlizenz deutschland - namensnennung - version 2.0",
            "govdata.de/dl-de/by-2-0",
            "dcat-ap.de/def/licenses/dl-by-de/2.0",
            "licenses/dl-by-de/2.0",
        ),
        "DL-DE BY 2.0",
        "https://www.govdata.de/dl-de/by-2-0",
    ),
)

_RESTRICTED_MARKERS: tuple[str, ...] = (
    "by-nc",
    "by-nd",
    "by-sa",
    "-nc-",
    "-nd-",
    "/nc/",
    "/nd/",
    "noncommercial",
    "non-commercial",
    "noderiv",
    "no derivatives",
    "all rights reserved",
    "other-closed",
    "notspecified",
    "not specified",
    "proprietary",
)


def _normalize(raw: str) -> str:
    text: str = raw.strip().lower().replace("_", "-")
    text = text.replace("—", "-").replace("–", "-")
    while "  " in text:
        text = text.replace("  ", " ")
    return text


def classify_license(
    *,
    license_id: str | None = None,
    license_title: str | None = None,
    license_url: str | None = None,
) -> LicenseClassification:
    """Classify a resource/package licence. Fail closed for unknown or restricted terms."""
    parts: list[str] = [
        part for part in (license_id, license_title, license_url) if part and part.strip()
    ]
    if not parts:
        return LicenseClassification(
            verdict=LicenseVerdict.UNKNOWN,
            canonical_name="",
            licence_url="",
        )

    normalized: str = _normalize(" | ".join(parts))
    display: str = (license_title or license_id or "").strip()
    url: str = (license_url or "").strip()

    for marker in _RESTRICTED_MARKERS:
        if marker in normalized:
            return LicenseClassification(
                verdict=LicenseVerdict.BLOCKED,
                canonical_name=display or "restricted",
                licence_url=url,
            )

    for aliases, canonical, default_url in _ALLOWED_LICENCES:
        if any(alias in normalized for alias in aliases):
            return LicenseClassification(
                verdict=LicenseVerdict.ALLOWED,
                canonical_name=canonical,
                licence_url=url or default_url,
            )

    # Generic CC BY id/title without NC/ND/SA suffix.
    compact: str = normalized.replace(" ", "")
    if compact in {"cc-by", "ccby"} or "|cc-by|" in f"|{compact}|" or compact.endswith("|cc-by"):
        return LicenseClassification(
            verdict=LicenseVerdict.ALLOWED,
            canonical_name="CC BY",
            licence_url=url or "https://creativecommons.org/licenses/by/4.0/",
        )
    if "cc-by" in normalized or "cc by" in normalized:
        return LicenseClassification(
            verdict=LicenseVerdict.ALLOWED,
            canonical_name="CC BY",
            licence_url=url or "https://creativecommons.org/licenses/by/4.0/",
        )

    return LicenseClassification(
        verdict=LicenseVerdict.UNKNOWN,
        canonical_name=display,
        licence_url=url,
    )
