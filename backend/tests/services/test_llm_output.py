from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.schemas.llm_output import LLMNewsOutput, fallback_after_validation_failure
from app.services.llm_json import extract_json_string, parse_llm_news_json
from app.services.llm_provider import StubLLMProvider, create_llm_provider


def _valid_payload() -> dict[str, object]:
    return {
        "title": "Тест",
        "one_sentence_summary": "Коротко о новости.",
        "plain_language": "Пояснение простым языком.",
        "impact_owner": "а",
        "impact_tenant": "б",
        "impact_buyer": "в",
        "action_items": "- сделать",
        "bonus_block": "факт",
        "spoiler": "интрига",
        "confidence_score": 0.9,
    }


def test_parse_llm_news_json_accepts_minimal_object() -> None:
    s: str = json.dumps(_valid_payload(), ensure_ascii=True)
    out: LLMNewsOutput = parse_llm_news_json(s)
    assert out.title == "Тест"
    assert out.confidence_score == 0.9


def test_parse_llm_news_json_rejects_confidence_out_of_range() -> None:
    p: dict[str, object] = _valid_payload()
    p["confidence_score"] = 1.5
    s: str = json.dumps(p, ensure_ascii=True)
    with pytest.raises(ValidationError):
        parse_llm_news_json(s)


def test_parse_llm_news_json_rejects_empty_title_after_strip() -> None:
    p: dict[str, object] = _valid_payload()
    p["title"] = "   \n  "
    s: str = json.dumps(p, ensure_ascii=True)
    with pytest.raises(ValidationError):
        parse_llm_news_json(s)


def test_extract_json_string_code_fence() -> None:
    raw: str = 'Prefix\n```json\n{"a":1}\n```\n'
    assert '"a":1' in extract_json_string(raw)


def test_stub_llm_provider_returns_valid_model() -> None:
    p: LLMNewsOutput = StubLLMProvider().process_news("  Title  ", "  Summary  ")
    assert p.title == "Title"
    assert p.one_sentence_summary.startswith("Summary")
    assert 0.0 <= p.confidence_score <= 1.0


def test_create_llm_provider_default_is_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "stub", raising=False)
    prov = create_llm_provider()
    assert isinstance(prov, StubLLMProvider)


def test_fallback_after_validation_failure_is_valid() -> None:
    f: LLMNewsOutput = fallback_after_validation_failure("T", "S", "reason")
    assert f.confidence_score < 0.2
    assert f.model_json_schema()["type"] == "object"
