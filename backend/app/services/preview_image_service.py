"""Resolve article preview image URLs: optional Open Graph fetch after RSS."""

from __future__ import annotations

import logging
from html.parser import HTMLParser
from typing import Final
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import Settings

logger: logging.Logger = logging.getLogger(__name__)

_MAX_URL_LEN: Final[int] = 1024
_HTML_HEAD_CHARS: Final[int] = 600_000


def normalize_image_url(page_url: str, raw: str, *, max_len: int = _MAX_URL_LEN) -> str:
    """Make a possibly relative image URL absolute; drop invalid or overlong values."""
    s: str = raw.strip()
    if not s:
        return ""
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    if s.startswith("//"):
        s = "https:" + s
    parsed = urlparse(s)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return s
    page: str = page_url.strip()
    if not page.startswith(("http://", "https://")):
        return ""
    joined: str = urljoin(page, s)
    jp = urlparse(joined)
    if jp.scheme in ("http", "https") and jp.netloc:
        return joined[:max_len]
    return ""


class _OgMetaImageParser(HTMLParser):
    """Extract first og:image or twitter:image meta content (attribute order agnostic)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.image_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.image_url is not None or tag != "meta":
            return
        ad: dict[str, str] = {str(k).lower(): str(v or "") for k, v in attrs}
        content: str = (ad.get("content") or "").strip()
        if not content:
            return
        prop: str = (ad.get("property") or "").lower()
        name: str = (ad.get("name") or "").lower()
        if prop in ("og:image", "og:image:url", "og:image:secure_url"):
            self.image_url = content
        elif name in ("twitter:image", "twitter:image:src"):
            self.image_url = content


def parse_og_image_url_from_html(html: str) -> str:
    """Return first Open Graph / Twitter image URL from HTML head/body snippet."""
    parser: _OgMetaImageParser = _OgMetaImageParser()
    try:
        parser.feed(html[:_HTML_HEAD_CHARS])
        parser.close()
    except Exception:
        return ""
    return (parser.image_url or "").strip()


def fetch_open_graph_image_url(
    client: httpx.Client,
    page_url: str,
    *,
    max_response_bytes: int,
) -> str:
    """GET the article page and parse og:image; empty string on failure."""
    page: str = page_url.strip()
    if not page.startswith(("http://", "https://")):
        return ""
    try:
        response: httpx.Response = client.get(page_url)
        response.raise_for_status()
        content: bytes = response.content
        if len(content) > max_response_bytes:
            content = content[:max_response_bytes]
        text: str = content.decode("utf-8", errors="ignore")
    except httpx.HTTPError as e:
        logger.debug("OG image fetch HTTP error for %s: %s", page_url, e)
        return ""
    except Exception:
        logger.exception("OG image fetch failed for %s", page_url)
        return ""
    raw_img: str = parse_og_image_url_from_html(text)
    return normalize_image_url(page_url, raw_img)


def resolve_preview_image_url(
    *,
    article_url: str,
    rss_image_url: str | None,
    client: httpx.Client | None,
    settings: Settings,
) -> str | None:
    """Prefer RSS image; optionally fetch Open Graph when RSS has none."""
    rss: str = normalize_image_url(article_url, rss_image_url or "")
    if rss:
        return rss
    if (
        not settings.og_image_fetch_enabled
        or client is None
        or not article_url.strip().startswith(("http://", "https://"))
    ):
        return None
    og: str = fetch_open_graph_image_url(
        client,
        article_url.strip(),
        max_response_bytes=settings.og_image_max_response_bytes,
    )
    return og or None
