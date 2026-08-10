from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, false, or_

from app.models.news import ProcessedNews, Source
from app.services.relevance_filter_service import OFFICIAL_DATA_SOURCE_KEYS


@dataclass(frozen=True)
class RSSSource:
    key: str
    name: str
    url: str
    licence: str | None = None
    licence_url: str | None = None
    copyright_holder: str | None = None
    original_language: str | None = None
    changes_notice: str | None = None
    rights_verified: bool = False
    text_only: bool = True


DEFAULT_RSS_SOURCES: tuple[RSSSource, ...] = (
    RSSSource(
        key="tagesschau",
        name="Tagesschau",
        url="https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml",
    ),
    RSSSource(key="spiegel", name="Spiegel", url="https://www.spiegel.de/schlagzeilen/index.rss"),
    RSSSource(key="die_zeit", name="Die Zeit", url="https://newsfeed.zeit.de/news/index"),
    RSSSource(key="zdf", name="ZDF", url="https://www.zdfheute.de/rss/zdf/nachrichten"),
    RSSSource(key="welt", name="WELT", url="https://www.welt.de/feeds/latest.rss"),
    RSSSource(
        key="destatis",
        name="Statistisches Bundesamt (Destatis)",
        url="https://www.destatis.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/Aktuell.xml?nn=3624",
        licence="Destatis general reuse terms",
        licence_url="https://www.destatis.de/DE/Service/Impressum/copyright-allgemein.html",
        copyright_holder="Statistisches Bundesamt (Destatis)",
        original_language="de",
        changes_notice=(
            "Неофициальный перевод и AI-суммаризация; текст сокращён и изменён. "
            "Оригинал Destatis имеет приоритет."
        ),
        rights_verified=True,
    ),
    RSSSource(
        key="ec_press_corner",
        name="European Commission Press Corner",
        url="https://ec.europa.eu/commission/presscorner/api/rss?language=en&pagesize=20",
        licence="CC BY 4.0",
        licence_url="https://commission.europa.eu/legal-notice_en",
        copyright_holder="European Union",
        original_language="en",
        changes_notice=(
            "Неофициальный перевод и AI-суммаризация; текст сокращён и изменён. "
            "При расхождениях действует оригинал."
        ),
        rights_verified=True,
    ),
)

RSS_CATALOG_SOURCE_KEYS: frozenset[str] = frozenset(source.key for source in DEFAULT_RSS_SOURCES)


def parse_enabled_source_keys(enabled_source_keys: str) -> frozenset[str]:
    """Parse comma-separated ``RSS_ENABLED_SOURCE_KEYS`` into a casefolded set."""
    return frozenset(
        key.strip().casefold() for key in enabled_source_keys.split(",") if key.strip()
    )


def enabled_rss_sources(enabled_source_keys: str) -> tuple[RSSSource, ...]:
    """Return only explicitly enabled sources; an empty allowlist fails closed."""
    enabled_keys: frozenset[str] = parse_enabled_source_keys(enabled_source_keys)
    return tuple(
        source
        for source in DEFAULT_RSS_SOURCES
        if source.rights_verified and source.key.casefold() in enabled_keys
    )


def allowed_rss_source_keys(enabled_source_keys: str) -> frozenset[str]:
    """Keys of RSS sources that may be ingested and shown publicly."""
    return frozenset(source.key for source in enabled_rss_sources(enabled_source_keys))


def is_source_allowed_for_publication(
    source_key: str | None,
    *,
    rights_verified: bool,
    enabled_source_keys: str,
) -> bool:
    """Whether an item from ``source_key`` may appear in the public feed / Telegram.

    Rules:
    - ``rights_verified`` is required.
    - Official statistics sources are always allowed when verified.
    - Known RSS catalog keys require membership in ``RSS_ENABLED_SOURCE_KEYS``.
    - Non-catalog keys (tests / other providers) only need ``rights_verified``.
    """
    if source_key is None or not rights_verified:
        return False
    normalized: str = source_key.strip().casefold()
    if not normalized:
        return False
    if normalized in {key.casefold() for key in OFFICIAL_DATA_SOURCE_KEYS}:
        return True
    catalog: frozenset[str] = frozenset(key.casefold() for key in RSS_CATALOG_SOURCE_KEYS)
    if normalized in catalog:
        allowed: frozenset[str] = frozenset(
            key.casefold() for key in allowed_rss_source_keys(enabled_source_keys)
        )
        return normalized in allowed
    return True


def publication_allowed_sql_filter(enabled_source_keys: str) -> Any:
    """SQLAlchemy filter matching :func:`is_source_allowed_for_publication` for joins on Source."""
    allowed_rss: tuple[str, ...] = tuple(allowed_rss_source_keys(enabled_source_keys))
    catalog: tuple[str, ...] = tuple(RSS_CATALOG_SOURCE_KEYS)
    official: tuple[str, ...] = tuple(OFFICIAL_DATA_SOURCE_KEYS)

    visibility_parts: list[Any] = []
    if official:
        visibility_parts.append(Source.source_key.in_(official))
    if allowed_rss:
        visibility_parts.append(Source.source_key.in_(allowed_rss))
    if catalog:
        visibility_parts.append(~Source.source_key.in_(catalog))

    if not visibility_parts:
        return and_(ProcessedNews.rights_verified.is_(True), false())
    return and_(ProcessedNews.rights_verified.is_(True), or_(*visibility_parts))
