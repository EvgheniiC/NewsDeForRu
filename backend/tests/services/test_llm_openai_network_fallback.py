from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from app.schemas.llm_output import LLMNewsOutput
from app.services.llm_openai_provider import OpenAILLMProvider


def test_openai_connect_error_uses_structured_fallback() -> None:
    provider: OpenAILLMProvider = OpenAILLMProvider(
        api_key="k",
        model="m",
        base_url="https://api.openai.com/v1",
    )
    with patch.object(
        provider._client,
        "post",
        side_effect=httpx.ConnectError("refused", request=MagicMock()),
    ):
        out: LLMNewsOutput = provider.process_news("Title", "Summary")
    serialized: str = out.model_dump_json()
    assert out.confidence_score == 0.0
    assert out.impact_presentation == "none"
    assert "Title" not in serialized
    assert "Summary" not in serialized


def test_incomplete_model_responses_never_publish_feed_text() -> None:
    provider: OpenAILLMProvider = OpenAILLMProvider(
        api_key="k",
        model="m",
        base_url="https://api.openai.com/v1",
    )
    incomplete_response: str = '{"title":"","confidence_score":0.99}'
    with patch.object(
        provider,
        "_chat",
        side_effect=[incomplete_response, incomplete_response],
    ):
        out: LLMNewsOutput = provider.process_news(
            "Streik legt Bahn lahm",
            "Die Regierung beschließt neue Maßnahmen.",
        )

    serialized: str = out.model_dump_json()
    assert out.confidence_score == 0.0
    assert "Streik" not in serialized
    assert "Regierung" not in serialized
    assert "Maßnahmen" not in serialized
