from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.config import settings
from app.schemas.llm_output import LLMNewsOutput


class LLMProvider(ABC):
    @abstractmethod
    def process_news(self, title: str, summary: str) -> LLMNewsOutput:
        raise NotImplementedError


class StubLLMProvider(LLMProvider):
    def process_news(self, title: str, summary: str) -> LLMNewsOutput:
        simplified: str = summary.strip() or "Новость обработана и упрощена."
        return LLMNewsOutput(
            title=title[:500],
            one_sentence_summary=simplified[:2000],
            plain_language=(
                "Если коротко: это изменение повлияет на расходы и правила для жителей Германии."
            ),
            impact_owner="Владельцу стоит проверить сроки и потенциальные расходы заранее.",
            impact_tenant="Арендатору важно уточнить, как изменения повлияют на платежи и договор.",
            impact_buyer="Покупателю нужно заложить в бюджет новые требования и возможные субсидии.",
            action_items="- Проверьте текущий статус\n- Изучите официальные субсидии",
            bonus_block="Одна цифра: итоговые расходы зависят от земли и типа жилья.",
            spoiler="Политический компромисс смягчил первоначальный вариант реформы.",
            confidence_score=0.82,
        )


def create_llm_provider() -> LLMProvider:
    name: str = settings.llm_provider
    if name == "stub":
        return StubLLMProvider()
    if name == "openai":
        key: str = settings.openai_api_key.strip()
        if not key:
            msg: str = "Set OPENAI_API_KEY (or openai_api_key) when LLM_PROVIDER=openai"
            raise ValueError(msg)
        from app.services.llm_openai_provider import OpenAILLMProvider

        return OpenAILLMProvider(
            api_key=key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
        )
    err: str = f"Unknown llm_provider: {name!r} (use stub or openai)"
    raise ValueError(err)


__all__ = [
    "LLMNewsOutput",
    "LLMProvider",
    "StubLLMProvider",
    "create_llm_provider",
]
