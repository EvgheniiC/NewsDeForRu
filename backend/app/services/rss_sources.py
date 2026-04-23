from dataclasses import dataclass


@dataclass(frozen=True)
class RSSSource:
    name: str
    url: str


DEFAULT_RSS_SOURCES: tuple[RSSSource, ...] = (
    RSSSource(name="Tagesschau", url="https://www.tagesschau.de/xml/rss2"),
    RSSSource(name="Spiegel", url="https://www.spiegel.de/schlagzeilen/index.rss"),
    RSSSource(name="Die Zeit", url="https://newsfeed.zeit.de/news/index"),
    RSSSource(name="ZDF", url="https://www.zdf.de/nachrichten/heute-sendungen/rss.xml"),
    RSSSource(name="WELT", url="https://www.welt.de/feeds/latest.rss"),
)
