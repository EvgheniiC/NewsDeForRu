"""Pick a non-media primary-source link out of a publisher RSS item."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

_ANCHOR_RE: re.Pattern[str] = re.compile(
    r"""<a\b[^>]*\bhref\s*=\s*(["'])(?P<href>.*?)\1[^>]*>(?P<label>.*?)</a>""",
    re.IGNORECASE | re.DOTALL,
)
_BARE_URL_RE: re.Pattern[str] = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_TAG_RE: re.Pattern[str] = re.compile(r"<[^>]+>")

_MAX_URL_LEN: int = 1024
_MAX_NAME_LEN: int = 256

_GENERIC_LABELS: frozenset[str] = frozenset(
    {
        "hier",
        "here",
        "mehr",
        "weiter",
        "link",
        "quelle",
        "source",
        "artikel",
        "article",
        "website",
        "webseite",
        "original",
        "pdf",
        "mehr dazu",
    }
)

# Another outlet is still a retelling, not a primary source.
_MEDIA_SUFFIXES: tuple[str, ...] = (
    "zeit.de",
    "welt.de",
    "spiegel.de",
    "tagesschau.de",
    "zdf.de",
    "zdfheute.de",
    "bild.de",
    "faz.net",
    "sueddeutsche.de",
    "focus.de",
    "n-tv.de",
    "t-online.de",
    "rnd.de",
    "stern.de",
    "handelsblatt.com",
    "tagesspiegel.de",
    "dw.com",
    "reuters.com",
    "bbc.com",
    "bbc.co.uk",
    "theguardian.com",
    "nytimes.com",
    "merkur.de",
    "waz.de",
    "ksta.de",
    "rp-online.de",
    "haz.de",
    "abendblatt.de",
    "morgenpost.de",
    "berliner-zeitung.de",
    "taz.de",
    "nzz.ch",
    "srf.ch",
)

_SKIP_SUFFIXES: tuple[str, ...] = (
    "facebook.com",
    "fb.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "t.co",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "linkedin.com",
    "pinterest.com",
    "whatsapp.com",
    "wa.me",
    "t.me",
    "telegram.me",
    "reddit.com",
    "google.com",
    "google.de",
    "doubleclick.net",
    "taboola.com",
    "outbrain.com",
)

_OFFICIAL_HOST_SUFFIXES: tuple[str, ...] = (
    "bund.de",
    "cdu.de",
    "csu.de",
    "spd.de",
    "gruene.de",
    "die-gruenen.de",
    "fdp.de",
    "afd.de",
    "die-linke.de",
    "bsw.de",
    "bsw-vg.de",
    "europa.eu",
)
_OFFICIAL_HOST_PARTS: tuple[str, ...] = (
    "polizei",
    "bundespolizei",
    "bundesregierung",
    "bundestag",
    "bundesrat",
    "landtag",
    "justiz",
    "gericht",
    "staatsanwaltschaft",
    "ministerium",
    "feuerwehr",
    "rathaus",
)


@dataclass(frozen=True)
class PrimarySourceLink:
    url: str
    name: str


def _host(url: str) -> str:
    host: str = (urlparse(url).hostname or "").casefold()
    if host.startswith("www."):
        return host[4:]
    return host


def _host_is(host: str, suffix: str) -> bool:
    return host == suffix or host.endswith("." + suffix)


def _host_is_any(host: str, suffixes: tuple[str, ...]) -> bool:
    return any(_host_is(host, suffix) for suffix in suffixes)


def _clean_label(raw: str) -> str:
    text: str = html.unescape(_TAG_RE.sub(" ", raw))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 2 or len(text) > 80:
        return ""
    if text.casefold() in _GENERIC_LABELS or text.casefold().startswith("http"):
        return ""
    return text


def _is_official_host(host: str) -> bool:
    if _host_is_any(host, _OFFICIAL_HOST_SUFFIXES):
        return True
    return any(part in host for part in _OFFICIAL_HOST_PARTS)


def _name_from_host(url: str) -> str:
    host: str = _host(url)
    return host or "Источник"


def extract_primary_source(summary_html: str, publisher_url: str) -> PrimarySourceLink | None:
    """Return one primary-source link, or None when the item does not name one clearly.

    Publisher pages, other news sites, and social links are ignored. Several
    unofficial external links are treated as ambiguous and also return None.
    """
    publisher_host: str = _host(publisher_url)
    official: list[PrimarySourceLink] = []
    other: list[PrimarySourceLink] = []
    seen: set[str] = set()

    def consider(raw_url: str, label: str) -> None:
        absolute: str = html.unescape(raw_url).strip()
        absolute = urljoin(publisher_url, absolute)
        absolute = absolute.split("#", 1)[0].strip().rstrip(").,;")
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return
        host: str = _host(absolute)
        if not host or (publisher_host and _host_is(host, publisher_host)):
            return
        if _host_is_any(host, _SKIP_SUFFIXES) or _host_is_any(host, _MEDIA_SUFFIXES):
            return
        if absolute in seen:
            return
        seen.add(absolute)
        name: str = label or _name_from_host(absolute)
        link: PrimarySourceLink = PrimarySourceLink(
            url=absolute[:_MAX_URL_LEN],
            name=name[:_MAX_NAME_LEN],
        )
        if _is_official_host(host):
            official.append(link)
            return
        other.append(link)

    for match in _ANCHOR_RE.finditer(summary_html or ""):
        consider(match.group("href"), _clean_label(match.group("label")))

    plain: str = _TAG_RE.sub(" ", summary_html or "")
    for match in _BARE_URL_RE.finditer(plain):
        consider(match.group(0), "")

    if official:
        return official[0]
    if len(other) == 1:
        return other[0]
    return None
