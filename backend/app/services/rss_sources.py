from dataclasses import dataclass


@dataclass(frozen=True)
class RSSSource:
    key: str
    name: str
    url: str


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
)


def enabled_rss_sources(enabled_source_keys: str) -> tuple[RSSSource, ...]:
    """Return only explicitly enabled sources; an empty allowlist fails closed."""
    enabled_keys: frozenset[str] = frozenset(
        key.strip().casefold() for key in enabled_source_keys.split(",") if key.strip()
    )
    return tuple(source for source in DEFAULT_RSS_SOURCES if source.key.casefold() in enabled_keys)
