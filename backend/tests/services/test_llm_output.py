from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.schemas.llm_output import LLMNewsOutput, fallback_after_validation_failure
from app.schemas.news import normalize_one_sentence_for_api
from app.services.llm_json import extract_json_string, parse_llm_news_json
from app.services.llm_provider import StubLLMProvider, create_llm_provider


def _valid_payload() -> dict[str, object]:
    return {
        "title": "Тест",
        "one_sentence_summary": "Коротко о новости.",
        "plain_language": "Пояснение простым языком.",
        "impact_presentation": "multi",
        "impact_unified": "",
        "impact_owner": "а",
        "impact_tenant": "б",
        "impact_buyer": "в",
        "action_items": "- сделать",
        "bonus_block": "факт",
        "spoiler": "интрига",
        "topic": "life",
        "confidence_score": 0.9,
        "importance_score": 7,
    }


def test_parse_llm_news_json_accepts_minimal_object() -> None:
    s: str = json.dumps(_valid_payload(), ensure_ascii=True)
    out: LLMNewsOutput = parse_llm_news_json(s)
    assert out.title == "Тест"
    assert out.impact_presentation == "multi"
    assert out.confidence_score == 0.9


def test_parse_llm_news_json_accepts_single_presentation() -> None:
    p: dict[str, object] = _valid_payload()
    p["impact_presentation"] = "single"
    p["impact_unified"] = "Один абзац о значении для читателя."
    p["impact_owner"] = ""
    p["impact_tenant"] = ""
    p["impact_buyer"] = ""
    out: LLMNewsOutput = parse_llm_news_json(json.dumps(p, ensure_ascii=True))
    assert out.impact_presentation == "single"
    assert "Один абзац" in out.impact_unified


def test_parse_llm_news_json_accepts_none_presentation() -> None:
    p: dict[str, object] = _valid_payload()
    p["impact_presentation"] = "none"
    p["impact_unified"] = ""
    p["impact_owner"] = ""
    p["impact_tenant"] = ""
    p["impact_buyer"] = ""
    out: LLMNewsOutput = parse_llm_news_json(json.dumps(p, ensure_ascii=True))
    assert out.impact_presentation == "none"


def test_parse_llm_news_json_rejects_multi_with_unified_text() -> None:
    p: dict[str, object] = _valid_payload()
    p["impact_unified"] = "лишнее"
    with pytest.raises(ValidationError):
        parse_llm_news_json(json.dumps(p, ensure_ascii=True))


def test_parse_llm_news_json_rejects_confidence_out_of_range() -> None:
    p: dict[str, object] = _valid_payload()
    p["confidence_score"] = 1.5
    s: str = json.dumps(p, ensure_ascii=True)
    with pytest.raises(ValidationError):
        parse_llm_news_json(s)


def test_parse_llm_news_json_rejects_string_none_placeholder() -> None:
    p: dict[str, object] = _valid_payload()
    p["one_sentence_summary"] = "None"
    s: str = json.dumps(p, ensure_ascii=True)
    with pytest.raises(ValidationError):
        parse_llm_news_json(s)


def test_parse_llm_news_json_fills_empty_title_from_raw_feed() -> None:
    p: dict[str, object] = _valid_payload()
    p["title"] = "   \n  "
    s: str = json.dumps(p, ensure_ascii=True)
    out: LLMNewsOutput = parse_llm_news_json(s, raw_title="Streik legt Bahn lahm")
    assert "Streik" in out.title


def test_parse_llm_news_json_placeholder_when_title_blank_and_no_raw() -> None:
    p: dict[str, object] = _valid_payload()
    p["title"] = ""
    out: LLMNewsOutput = parse_llm_news_json(json.dumps(p, ensure_ascii=True))
    assert out.title.startswith("Заголовок не получен")


def test_parse_llm_news_json_coerces_russian_topic_economy() -> None:
    p: dict[str, object] = _valid_payload()
    p["topic"] = "экономика"
    out: LLMNewsOutput = parse_llm_news_json(json.dumps(p, ensure_ascii=True))
    assert out.topic == "economy"


def test_parse_llm_news_json_coerces_german_topic_wirtschaft() -> None:
    p: dict[str, object] = _valid_payload()
    p["topic"] = "Wirtschaft"
    out: LLMNewsOutput = parse_llm_news_json(json.dumps(p, ensure_ascii=True))
    assert out.topic == "economy"


def test_parse_llm_news_json_fills_empty_action_only_bonus_spoiler_optional() -> None:
    p: dict[str, object] = _valid_payload()
    p["action_items"] = ""
    p["bonus_block"] = "   "
    p["spoiler"] = ""
    out: LLMNewsOutput = parse_llm_news_json(json.dumps(p, ensure_ascii=True))
    assert "источникам" in out.action_items
    assert out.bonus_block == ""
    assert out.spoiler == ""


def test_parse_llm_news_json_ignores_placeholder_raw_summary_for_draft() -> None:
    p: dict[str, object] = _valid_payload()
    p["one_sentence_summary"] = ""
    p["plain_language"] = ""
    out: LLMNewsOutput = parse_llm_news_json(
        json.dumps(p, ensure_ascii=True),
        raw_summary="None",
    )
    assert "Краткая сводка не была возвращена моделью" in out.one_sentence_summary
    assert "Черновик из описания фида" not in out.one_sentence_summary


def test_parse_llm_news_json_fills_summary_plain_from_raw_feed() -> None:
    p: dict[str, object] = _valid_payload()
    p["one_sentence_summary"] = ""
    p["plain_language"] = ""
    raw_sum: str = "Die Regierung beschließt neue Maßnahmen."
    out: LLMNewsOutput = parse_llm_news_json(
        json.dumps(p, ensure_ascii=True),
        raw_summary=raw_sum,
    )
    assert "Maßnahmen" in out.one_sentence_summary or "нем." in out.one_sentence_summary
    assert "немецкий" in out.plain_language.lower() or "Maßnahmen" in out.plain_language


def test_extract_json_string_code_fence() -> None:
    raw: str = 'Prefix\n```json\n{"a":1}\n```\n'
    assert '"a":1' in extract_json_string(raw)


def test_stub_llm_provider_returns_valid_model() -> None:
    p: LLMNewsOutput = StubLLMProvider().process_news("  Title  ", "  Summary  ")
    assert p.title.startswith("Новость из Германии")
    assert "русском" in p.one_sentence_summary
    assert "LLM_PROVIDER=openai" in p.one_sentence_summary
    assert 0.0 <= p.confidence_score <= 1.0
    assert 1 <= p.importance_score <= 10


def test_create_llm_provider_default_is_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "stub", raising=False)
    prov = create_llm_provider()
    assert isinstance(prov, StubLLMProvider)


def test_normalize_one_sentence_replaces_string_none_placeholder() -> None:
    assert "Сводка" in normalize_one_sentence_for_api("None")
    assert normalize_one_sentence_for_api("  Нормальный текст. ") == "Нормальный текст."


def test_fallback_after_validation_failure_is_valid() -> None:
    f: LLMNewsOutput = fallback_after_validation_failure("T", "S", "reason")
    assert f.confidence_score < 0.2
    assert f.impact_presentation == "single"
    assert f.impact_unified
    assert f.impact_owner == ""
    assert 1 <= f.importance_score <= 10
    assert f.model_json_schema()["type"] == "object"
