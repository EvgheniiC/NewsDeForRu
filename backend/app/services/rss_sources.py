from dataclasses import dataclass


@dataclass(frozen=True)
class RSSSource:
    key: str
    name: str
    url: str


DEFAULT_RSS_SOURCES: tuple[RSSSource, ...] = (
    RSSSource(key="tagesschau", name="Tagesschau", url="https://www.tagesschau.de/xml/rss2"),
    RSSSource(key="spiegel", name="Spiegel", url="https://www.spiegel.de/schlagzeilen/index.rss"),
    RSSSource(key="die_zeit", name="Die Zeit", url="https://newsfeed.zeit.de/news/index"),
    RSSSource(key="zdf", name="ZDF", url="https://www.zdf.de/nachrichten/heute-sendungen/rss.xml"),
    RSSSource(key="welt", name="WELT", url="https://www.welt.de/feeds/latest.rss"),
)
