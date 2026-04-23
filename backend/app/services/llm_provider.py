from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMNewsOutput:
    title: str
    one_sentence_summary: str
    plain_language: str
    impact_owner: str
    impact_tenant: str
    impact_buyer: str
    action_items: str
    bonus_block: str
    spoiler: str
    confidence_score: float


class LLMProvider(ABC):
    @abstractmethod
    def process_news(self, title: str, summary: str) -> LLMNewsOutput:
        raise NotImplementedError


class StubLLMProvider(LLMProvider):
    def process_news(self, title: str, summary: str) -> LLMNewsOutput:
        simplified: str = summary.strip() or "Новость обработана и упрощена."
        return LLMNewsOutput(
            title=title[:120],
            one_sentence_summary=simplified[:220],
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
