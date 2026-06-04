"""Extract readable German article text from HTML pages."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Final

_MAX_HTML_CHARS: Final[int] = 600_000
_BLOCK_TAGS: Final[frozenset[str]] = frozenset(
    {"p", "h1", "h2", "h3", "h4", "li", "blockquote", "figcaption"}
)
_SKIP_TAGS: Final[frozenset[str]] = frozenset(
    {"script", "style", "noscript", "svg", "nav", "footer", "header", "aside", "form"}
)
_CONTAINER_TAGS: Final[frozenset[str]] = frozenset({"article", "main"})


def _normalize_whitespace(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line: str = re.sub(r"\s+", " ", raw_line).strip()
        if line:
            lines.append(line)
    return "\n\n".join(lines)


class _ArticleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth: int = 0
        self._container_depth: int = 0
        self._in_container: bool = False
        self._block_depth: int = 0
        self._chunk: list[str] = []
        self._blocks: list[str] = []
        self._container_blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t: str = tag.lower()
        if t in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        if t in _CONTAINER_TAGS:
            self._container_depth += 1
            self._in_container = True
        if t in _BLOCK_TAGS:
            self._block_depth += 1

    def handle_endtag(self, tag: str) -> None:
        t: str = tag.lower()
        if t in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if self._skip_depth > 0:
            return
        if t in _BLOCK_TAGS and self._block_depth > 0:
            self._block_depth -= 1
            self._flush_block()
        if t in _CONTAINER_TAGS and self._container_depth > 0:
            self._container_depth -= 1
            if self._container_depth == 0:
                self._in_container = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0 or self._block_depth == 0:
            return
        piece: str = data.strip()
        if piece:
            self._chunk.append(piece)

    def _flush_block(self) -> None:
        if not self._chunk:
            return
        block: str = " ".join(self._chunk).strip()
        self._chunk = []
        if len(block) < 2:
            return
        self._blocks.append(block)
        if self._in_container:
            self._container_blocks.append(block)

    def finish_parse(self) -> None:
        self._flush_block()

    def best_text(self) -> str:
        chosen: list[str] = self._container_blocks if len(self._container_blocks) >= 2 else self._blocks
        return _normalize_whitespace("\n\n".join(chosen))


def extract_article_text_from_html(html: str, *, max_chars: int) -> str:
    """Return main article plain text from HTML, capped to max_chars."""
    parser: _ArticleTextParser = _ArticleTextParser()
    try:
        parser.feed(html[:_MAX_HTML_CHARS])
        parser.close()
    except Exception:
        return ""
    parser.finish_parse()
    text: str = parser.best_text()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "…"
    return text
