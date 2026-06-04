"""Lazy fetch, extract, and translate full article text for mobile readers."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.core.http_tls import httpx_verify_arg
from app.models.news import PipelineStatus, ProcessedNews
from app.repositories.news_repository import NewsRepository
from app.services.article_text_extraction import extract_article_text_from_html

logger: logging.Logger = logging.getLogger(__name__)


class FullArticleUnavailableError(Exception):
    """Raised when full article cannot be produced (config, fetch, or translation)."""


class FullArticleService:
    def __init__(self, db_session: Session, app_settings: Settings | None = None) -> None:
        self._db: Session = db_session
        self._settings: Settings = app_settings or settings
        self._repo: NewsRepository = NewsRepository(db_session)

    def _openai_model(self) -> str:
        dedicated: str = self._settings.openai_full_article_model.strip()
        return dedicated or self._settings.openai_model

    def _require_openai(self) -> str:
        if self._settings.llm_provider != "openai":
            raise FullArticleUnavailableError(
                "Full article translation requires LLM_PROVIDER=openai."
            )
        key: str = self._settings.openai_api_key.strip()
        if not key:
            raise FullArticleUnavailableError("OPENAI_API_KEY is not configured.")
        return key

    def _fetch_page_html(self, page_url: str) -> str:
        if not self._settings.full_article_fetch_enabled:
            raise FullArticleUnavailableError("Article page fetch is disabled.")
        page: str = page_url.strip()
        if not page.startswith(("http://", "https://")):
            raise FullArticleUnavailableError("Invalid source URL.")
        timeout: httpx.Timeout = httpx.Timeout(self._settings.full_article_fetch_timeout_seconds)
        headers: dict[str, str] = {"User-Agent": self._settings.rss_user_agent}
        with httpx.Client(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            verify=httpx_verify_arg(self._settings),
        ) as client:
            response: httpx.Response = client.get(page)
            response.raise_for_status()
            content: bytes = response.content
            max_bytes: int = self._settings.full_article_max_response_bytes
            if len(content) > max_bytes:
                content = content[:max_bytes]
        return content.decode("utf-8", errors="ignore")

    def _build_source_text(self, item: ProcessedNews) -> str:
        max_extract: int = self._settings.full_article_max_extract_chars
        html: str = self._fetch_page_html(item.source_url)
        extracted: str = extract_article_text_from_html(
            html,
            max_chars=max_extract,
        )
        raw = item.raw_item
        if len(extracted) >= 400:
            return extracted
        fallback_parts: list[str] = []
        if raw is not None:
            title: str = raw.title.strip()
            summary: str = raw.summary.strip()
            if title:
                fallback_parts.append(title)
            if summary:
                fallback_parts.append(summary)
        if extracted:
            fallback_parts.append(extracted)
        combined: str = "\n\n".join(fallback_parts).strip()
        if not combined:
            raise FullArticleUnavailableError(
                "Could not extract article text from the source page."
            )
        if len(combined) > max_extract:
            combined = combined[:max_extract].rstrip() + "…"
        return combined

    def _translate_to_russian(self, german_text: str, *, title_hint: str) -> str:
        api_key: str = self._require_openai()
        base: str = self._settings.openai_base_url.rstrip("/")
        model: str = self._openai_model()
        system: str = (
            "You translate German news articles into Russian for readers in Germany. "
            "Preserve facts, names, numbers, and paragraph breaks. "
            "Do not add commentary or information that is not in the source. "
            "Output only the Russian translation as plain text (no JSON, no markdown fences)."
        )
        user: str = (
            f"Заголовок материала (контекст): {title_hint}\n\n"
            f"Текст статьи на немецком:\n{german_text}"
        )
        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        headers: dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        timeout: httpx.Timeout = httpx.Timeout(120.0)
        max_retries: int = max(0, self._settings.openai_request_retries)
        last_error: Exception | None = None
        with httpx.Client(
            base_url=f"{base}/",
            headers=headers,
            timeout=timeout,
            verify=httpx_verify_arg(self._settings),
        ) as client:
            for attempt in range(max_retries + 1):
                try:
                    response: httpx.Response = client.post("chat/completions", json=body)
                    response.raise_for_status()
                    data: Any = response.json()
                    content: str = str(data["choices"][0]["message"]["content"]).strip()
                    if not content:
                        raise FullArticleUnavailableError("OpenAI returned empty translation.")
                    max_stored: int = self._settings.full_article_max_stored_chars
                    if len(content) > max_stored:
                        content = content[:max_stored].rstrip() + "…"
                    return content
                except httpx.HTTPStatusError as e:
                    last_error = e
                    code: int = e.response.status_code
                    if attempt < max_retries and code in (429, 500, 502, 503, 504):
                        time.sleep(0.8 * (attempt + 1))
                        continue
                    raise FullArticleUnavailableError(
                        f"OpenAI translation failed (HTTP {code})."
                    ) from e
                except (httpx.HTTPError, KeyError, IndexError, TypeError) as e:
                    last_error = e
                    break
        raise FullArticleUnavailableError(
            f"OpenAI translation failed: {last_error!s}"[:240]
        ) from last_error

    def get_or_create_full_article_ru(self, news_id: int) -> tuple[str, bool]:
        """
        Return Russian full article text and whether it was already cached.

        Only published items are eligible.
        """
        item: ProcessedNews | None = self._repo.get_processed_by_id_with_raw(news_id)
        if item is None or item.publication_status != PipelineStatus.PUBLISHED:
            raise FullArticleUnavailableError("News item not found.")
        cached: str | None = item.full_article_ru
        if cached is not None and cached.strip():
            return cached.strip(), True

        self._db.refresh(item)
        if item.full_article_ru is not None and item.full_article_ru.strip():
            return item.full_article_ru.strip(), True

        title_hint: str = item.title.strip() or (item.raw_item.title.strip() if item.raw_item else "")
        german_text: str = self._build_source_text(item)
        russian: str = self._translate_to_russian(german_text, title_hint=title_hint)
        saved: bool = self._repo.save_full_article_ru_if_empty(news_id, russian)
        if not saved:
            again: ProcessedNews | None = self._repo.get_processed_by_id(news_id)
            if again is not None and again.full_article_ru and again.full_article_ru.strip():
                return again.full_article_ru.strip(), True
        return russian, False
