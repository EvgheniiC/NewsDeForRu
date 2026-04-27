from pydantic import BaseModel, ConfigDict, Field, field_validator


def _llm_string(v: str) -> str:
    t: str = v.strip()
    if not t:
        msg: str = "String field must be non-empty after trim"
        raise ValueError(msg)
    return t


class LLMNewsOutput(BaseModel):
    """Structured LLM result aligned with the publication pipeline and DB model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    title: str = Field(..., min_length=1, max_length=500)
    one_sentence_summary: str = Field(..., min_length=1, max_length=2000)
    plain_language: str = Field(..., min_length=1, max_length=8000)
    impact_owner: str = Field(..., min_length=1, max_length=4000)
    impact_tenant: str = Field(..., min_length=1, max_length=4000)
    impact_buyer: str = Field(..., min_length=1, max_length=4000)
    action_items: str = Field(..., min_length=1, max_length=4000)
    bonus_block: str = Field(..., min_length=1, max_length=2000)
    spoiler: str = Field(..., min_length=1, max_length=2000)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    @field_validator(
        "title",
        "one_sentence_summary",
        "plain_language",
        "impact_owner",
        "impact_tenant",
        "impact_buyer",
        "action_items",
        "bonus_block",
        "spoiler",
        mode="before",
    )
    @classmethod
    def _non_empty_strings(cls, v: object) -> object:
        if not isinstance(v, str):
            return v
        return _llm_string(v)

    @classmethod
    def system_prompt_addendum(cls) -> str:
        """Text appended to the system instruction so the model knows exact keys and types."""
        return (
            "Return exactly one JSON object (no markdown, no extra text) with these keys: "
            "title, one_sentence_summary, plain_language, impact_owner, impact_tenant, "
            "impact_buyer, action_items, bonus_block, spoiler, confidence_score. "
            "All string values must be in Russian. confidence_score is a number from 0 to 1."
        )


def fallback_after_validation_failure(
    title: str, summary: str, failure_reason: str
) -> LLMNewsOutput:
    """Deterministic, schema-valid copy when the model output cannot be validated."""
    tech: str = f"(JSON не прошёл проверку: {failure_reason[:180]})"
    de_hint: str = (summary.strip() or title.strip())[:400]
    return LLMNewsOutput(
        title="Перевод и сводка не сформированы — требуется ручная проверка"[:500],
        one_sentence_summary=(
            "Автоматическая обработка не дала валидный ответ. "
            "Сформируйте краткое изложение на русском вручную, либо перезапустите с LLM_PROVIDER=openai. "
            "Полный оригинал — на немецком по ссылке из новости."
        )[:2000],
        plain_language=(
            "Если коротко: ответ ИИ нельзя было надёжно разобрать. "
            f"Оригинал (фрагмент, нем.): {de_hint}. " + tech
        )[:8000],
        impact_owner="Владельцу стоит проверить сроки и потенциальные расходы заранее.",
        impact_tenant="Арендатору важно уточнить, как изменения повлияют на платежи и договор.",
        impact_buyer="Покупателю нужно заложить в бюджет новые требования и возможные субсидии.",
        action_items="- Проверьте текущий статус\n- Изучите официальные субсидии",
        bonus_block="Редакция отметила ошибку в ответе ИИ; материал уйдёт на ручную проверку.",
        spoiler="Политический компромисс мог смягчить первоначальный вариант реформы.",
        confidence_score=0.12,
    )
