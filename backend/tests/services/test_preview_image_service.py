from __future__ import annotations

from unittest.mock import MagicMock

from app.core.config import Settings
from app.services.preview_image_service import (
    fetch_open_graph_image_url,
    normalize_image_url,
    parse_og_image_url_from_html,
    resolve_preview_image_url,
)


def test_normalize_image_url_protocol_relative() -> None:
    assert (
        normalize_image_url("https://example.com/a", "//cdn.test/x.png")
        == "https://cdn.test/x.png"
    )


def test_normalize_image_url_relative_path() -> None:
    assert (
        normalize_image_url("https://example.com/news/article", "/static/p.jpg")
        == "https://example.com/static/p.jpg"
    )


def test_parse_og_image_content_before_property() -> None:
    html: str = '<meta content="https://x.com/a.png" property="og:image" />'
    assert parse_og_image_url_from_html(html) == "https://x.com/a.png"


def test_parse_og_image_property_before_content() -> None:
    html: str = '<meta property="og:image" content="https://x.com/b.png"/>'
    assert parse_og_image_url_from_html(html) == "https://x.com/b.png"


def test_parse_twitter_image_meta() -> None:
    html: str = '<meta name="twitter:image" content="https://x.com/c.png" />'
    assert parse_og_image_url_from_html(html) == "https://x.com/c.png"


def test_fetch_open_graph_resolves_relative_image() -> None:
    client: MagicMock = MagicMock()
    response: MagicMock = MagicMock()
    response.raise_for_status = MagicMock()
    response.content = b'<meta property="og:image" content="/files/p.png"/>'
    client.get = MagicMock(return_value=response)

    out: str = fetch_open_graph_image_url(
        client,
        "https://news.example/article",
        max_response_bytes=50_000,
    )
    assert out == "https://news.example/files/p.png"


def test_resolve_prefers_rss_when_present() -> None:
    cfg: Settings = Settings(og_image_fetch_enabled=True)
    assert (
        resolve_preview_image_url(
            article_url="https://example.com/p",
            rss_image_url="https://img.example/i.jpg",
            client=None,
            settings=cfg,
        )
        == "https://img.example/i.jpg"
    )


def test_resolve_returns_none_without_rss_and_no_fetch() -> None:
    cfg: Settings = Settings(og_image_fetch_enabled=False)
    assert (
        resolve_preview_image_url(
            article_url="https://example.com/p",
            rss_image_url=None,
            client=None,
            settings=cfg,
        )
        is None
    )
