from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.llm_output import LLMNewsOutput, fallback_after_validation_failure
from app.services.llm_json import build_repair_user_message, parse_llm_news_json
from app.services.llm_provider import LLMProvider

logger: logging.Logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProvider):
    """OpenAI Chat Completions with json_object, then Pydantic validation and one repair pass."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key: str = api_key
        self._model: str = model
        self._base: str = base_url.rstrip("/")
        self._client: httpx.Client = httpx.Client(
            base_url=f"{self._base}/",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0),
        )

    def close(self) -> None:
        self._client.close()

    def _chat(self, messages: list[dict[str, str]]) -> str:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.35,
            "response_format": {"type": "json_object"},
        }
        max_retries: int = max(0, settings.openai_request_retries)
        for attempt in range(max_retries + 1):
            try:
                r: httpx.Response = self._client.post("chat/completions", json=body)
                r.raise_for_status()
                data: Any = r.json()
                try:
                    return str(data["choices"][0]["message"]["content"])
                except (KeyError, IndexError, TypeError) as e:
                    msg: str = "Unexpected OpenAI response shape"
                    raise ValueError(msg) from e
            except httpx.HTTPStatusError as e:
                code: int = e.response.status_code
                if (
                    attempt < max_retries
                    and code
                    in (
                        429,
                        500,
                        502,
                        503,
                        504,
                    )
                ):
                    time.sleep(0.8 * (attempt + 1))
                    continue
                raise
        raise RuntimeError("OpenAI: chat request could not be completed")

    def _process_news_inner(self, title: str, summary: str) -> LLMNewsOutput:
        system: str = (
            "You are an editor. Rewrite German news for Russian-speaking readers in Germany. "
            "Output only valid JSON, no surrounding prose. " + LLMNewsOutput.system_prompt_addendum()
        )
        user: str = (
            f"Оригинальный заголовок:\n{title}\n\n"
            f"Оригинальное краткое описание:\n{summary}\n"
        )
        first_messages: list[dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        content: str = self._chat(first_messages)
        try:
            return parse_llm_news_json(content)
        except (ValueError, TypeError, ValidationError) as e1:
            logger.warning("LLM first JSON parse/validation failed: %s", e1)
            repair: str = build_repair_user_message(str(e1), content)
            second_messages: list[dict[str, str]] = [
                *first_messages,
                {"role": "assistant", "content": content},
                {"role": "user", "content": repair},
            ]
            try:
                content2: str = self._chat(second_messages)
                return parse_llm_news_json(content2)
            except (ValueError, TypeError, ValidationError) as e2:
                logger.error("LLM failed after repair: %s", e2)
                return fallback_after_validation_failure(title, summary, str(e2))

    def process_news(self, title: str, summary: str) -> LLMNewsOutput:
        try:
            return self._process_news_inner(title, summary)
        except (httpx.HTTPError, httpx.RequestError) as e:
            logger.warning("OpenAI transport error, using validation fallback: %s", e)
            return fallback_after_validation_failure(
                title, summary, f"OpenAI request failed: {e!s}"[:200]
            )
        except Exception as e:
            logger.exception("OpenAI processing failed, using validation fallback: %s", e)
            return fallback_after_validation_failure(
                title, summary, f"OpenAI error: {e!s}"[:200]
            )
