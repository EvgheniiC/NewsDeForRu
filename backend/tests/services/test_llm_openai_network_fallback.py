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
    assert out.confidence_score == 0.12
    assert "OpenAI" in out.plain_language
