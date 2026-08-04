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


def test_openai_open_dataset_summary_adds_key_figures_hint() -> None:
    provider: OpenAILLMProvider = OpenAILLMProvider(
        api_key="k",
        model="m",
        base_url="https://api.openai.com/v1",
    )
    captured: list[list[dict[str, str]]] = []
    valid_json: str = (
        '{"title":"Тест","one_sentence_summary":"Кратко.","plain_language":"Пояснение.",'
        '"impact_presentation":"none","impact_unified":"","impact_owner":"",'
        '"impact_tenant":"","impact_buyer":"","action_items":"","bonus_block":"",'
        '"spoiler":"","topic":"life","is_positive":false,"confidence_score":0.7,'
        '"importance_score":5}'
    )

    def _fake_chat(messages: list[dict[str, str]]) -> str:
        captured.append(messages)
        return valid_json

    with patch.object(provider, "_chat", side_effect=_fake_chat):
        provider.process_news(
            "GovData: Bevölkerung",
            "EDITOR NOTES (open dataset, not a news article):\nKey figures\nDataset URI: x",
        )

    assert captured
    user_content: str = captured[0][1]["content"]
    assert "открытый госдатасет" in user_content
    assert "Key figures" in user_content


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
