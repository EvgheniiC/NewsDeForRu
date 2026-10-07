"""Rules for how a news card may be written and published.

1. Licensed source. The source has written permission or an open licence.
   The card cites that source and may be auto-published when the usual
   quality gates pass.
2. Unlicensed publisher with a primary source, for example BILD. The publisher
   item is only a signal that something happened. The card is a short original
   draft based on the primary source, cites only that source, and may be
   auto-published when the usual quality gates pass.
3. Unlicensed publisher without a primary source. The card must not invent a
   source and always goes to moderation.
"""

from enum import StrEnum

from app.services.publisher_editorial import is_publisher_editorial_source


class NewsOriginMode(StrEnum):
    """Which of the three origin rules applies to one item."""

    LICENSED_SOURCE = "licensed_source"
    INDEPENDENT_PRIMARY = "independent_primary"
    MISSING_PRIMARY = "missing_primary"


def has_verified_licence(
    *,
    rights_verified: bool,
    licence: str | None,
    licence_url: str | None,
) -> bool:
    """Whether the source may be cited and published under rule 1."""
    return bool(
        rights_verified
        and (licence or "").strip()
        and (licence_url or "").strip()
    )


def resolve_news_origin_mode(
    *,
    source_key: str | None,
    rights_verified: bool,
    licence: str | None,
    licence_url: str | None,
    has_primary_source: bool,
) -> NewsOriginMode | None:
    """Return the origin rule, or None when a non-publisher item lacks a licence.

    None is not a fourth editorial mode. The publication service holds those
    items for a missing licence. Unlicensed publisher items never return None.
    """
    if has_verified_licence(
        rights_verified=rights_verified,
        licence=licence,
        licence_url=licence_url,
    ):
        return NewsOriginMode.LICENSED_SOURCE
    if not is_publisher_editorial_source(source_key):
        return None
    if has_primary_source:
        return NewsOriginMode.INDEPENDENT_PRIMARY
    return NewsOriginMode.MISSING_PRIMARY
