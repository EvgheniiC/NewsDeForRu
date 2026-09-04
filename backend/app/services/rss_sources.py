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


def _publisher_rss(key: str, name: str, url: str) -> RSSSource:
    """Catalog publisher feed: text-only, no rights claim, German RSS hook."""
    return RSSSource(
        key=key,
        name=name,
        url=url,
        original_language="de",
        rights_verified=False,
        text_only=True,
    )


DEFAULT_RSS_SOURCES: tuple[RSSSource, ...] = (
    _publisher_rss(
        "tagesschau",
        "Tagesschau",
        "https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml",
    ),
    _publisher_rss("spiegel", "Spiegel", "https://www.spiegel.de/schlagzeilen/index.rss"),
    _publisher_rss("die_zeit", "Die Zeit", "https://newsfeed.zeit.de/news/index"),
    _publisher_rss("zdf", "ZDF", "https://www.zdfheute.de/rss/zdf/nachrichten"),
    _publisher_rss("welt", "WELT", "https://www.welt.de/feeds/latest.rss"),
    _publisher_rss("bild", "BILD", "https://www.bild.de/feed/alles.xml"),
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


def enabled_rss_sources(
    enabled_source_keys: str,
    *,
    allow_unverified: bool = False,
) -> tuple[RSSSource, ...]:
    """Return only explicitly enabled sources; an empty allowlist fails closed."""
    enabled_keys: frozenset[str] = parse_enabled_source_keys(enabled_source_keys)
    return tuple(
        source
        for source in DEFAULT_RSS_SOURCES
        if source.key.casefold() in enabled_keys
        and (source.rights_verified or allow_unverified)
    )


def allowed_rss_source_keys(
    enabled_source_keys: str,
    *,
    allow_unverified: bool = False,
) -> frozenset[str]:
    """Keys of RSS sources that may be ingested and shown publicly."""
    return frozenset(
        source.key
        for source in enabled_rss_sources(
            enabled_source_keys,
            allow_unverified=allow_unverified,
        )
    )


def is_source_allowed_for_publication(
    source_key: str | None,
    *,
    rights_verified: bool,
    enabled_source_keys: str,
    allow_unverified: bool = False,
) -> bool:
    """Whether an item from ``source_key`` may appear in the public feed / Telegram.

    Rules:
    - Official statistics sources are always allowed when verified.
    - Known RSS catalog keys require membership in ``RSS_ENABLED_SOURCE_KEYS``.
    - Catalog publishers also need ``rights_verified`` unless ``allow_unverified``.
    - Non-catalog keys (tests / other providers) only need ``rights_verified``.
    """
    if source_key is None:
        return False
    normalized: str = source_key.strip().casefold()
    if not normalized:
        return False
    if normalized in {key.casefold() for key in OFFICIAL_DATA_SOURCE_KEYS}:
        return rights_verified
    catalog: frozenset[str] = frozenset(key.casefold() for key in RSS_CATALOG_SOURCE_KEYS)
    if normalized in catalog:
        allowed: frozenset[str] = frozenset(
            key.casefold()
            for key in allowed_rss_source_keys(
                enabled_source_keys,
                allow_unverified=allow_unverified,
            )
        )
        if normalized not in allowed:
            return False
        return rights_verified or allow_unverified
    return rights_verified


def publication_allowed_sql_filter(
    enabled_source_keys: str,
    *,
    allow_unverified: bool = False,
) -> Any:
    """SQLAlchemy filter matching :func:`is_source_allowed_for_publication` for joins on Source."""
    allowed_rss: tuple[str, ...] = tuple(
        allowed_rss_source_keys(
            enabled_source_keys,
            allow_unverified=allow_unverified,
        )
    )
    catalog: tuple[str, ...] = tuple(RSS_CATALOG_SOURCE_KEYS)
    official: tuple[str, ...] = tuple(OFFICIAL_DATA_SOURCE_KEYS)

    visibility_parts: list[Any] = []
    if official:
        visibility_parts.append(
            and_(Source.source_key.in_(official), ProcessedNews.rights_verified.is_(True))
        )
    if allowed_rss:
        if allow_unverified:
            visibility_parts.append(Source.source_key.in_(allowed_rss))
        else:
            visibility_parts.append(
                and_(
                    Source.source_key.in_(allowed_rss),
                    ProcessedNews.rights_verified.is_(True),
                )
            )
    if catalog:
        visibility_parts.append(
            and_(
                ~Source.source_key.in_(catalog),
                ProcessedNews.rights_verified.is_(True),
            )
        )

    if not visibility_parts:
        return and_(ProcessedNews.rights_verified.is_(True), false())
    return or_(*visibility_parts)
