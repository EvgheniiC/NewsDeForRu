from dataclasses import dataclass


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


def enabled_rss_sources(enabled_source_keys: str) -> tuple[RSSSource, ...]:
    """Return only explicitly enabled sources; an empty allowlist fails closed."""
    enabled_keys: frozenset[str] = frozenset(
        key.strip().casefold() for key in enabled_source_keys.split(",") if key.strip()
    )
    return tuple(
        source
        for source in DEFAULT_RSS_SOURCES
        if source.rights_verified and source.key.casefold() in enabled_keys
    )
