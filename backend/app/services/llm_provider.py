from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.config import settings
from typing import Literal

from app.schemas.llm_output import LLMNewsOutput


class LLMProvider(ABC):
    @abstractmethod
    def process_news(self, title: str, summary: str) -> LLMNewsOutput:
        raise NotImplementedError


class StubLLMProvider(LLMProvider):
    def process_news(self, title: str, summary: str) -> LLMNewsOutput:
        # Do not pass German RSS text through as the published title/summary: the UI is Russian.
        # Stub has no translation model; we emit Russian placeholders. Use LLM_PROVIDER=openai to translate.
        key: int = abs(hash((title, summary)))
        roll: tuple[Literal["politics"], Literal["economy"], Literal["life"]] = (
            "politics",
            "economy",
            "life",
        )
        topic: Literal["politics", "economy", "life"] = roll[key % 3]
        if topic == "politics":
            return LLMNewsOutput(
                title=(f"Новость из Германии (черновик {key % 1_000_000:06d})")[:500],
                one_sentence_summary=(
                    "Краткое изложение на русском в этом режиме не строится из текста фида. "
                    "Для автоматического перевода с немецкого укажите LLM_PROVIDER=openai в окружении. "
                    "Полный оригинал — по ссылке в карточке."
                )[:2000],
                plain_language=(
                    "Если коротко: в режиме заглушки политическую оценку развернуть нельзя — см. оригинал."
                ),
                impact_presentation="none",
                impact_unified="",
                impact_owner="",
                impact_tenant="",
                impact_buyer="",
                action_items="- Проверьте текущий статус\n- Изучите официальные субсидии",
                bonus_block="В политике (stub) отдельный блок влияния скрыт — типично для речей и цитат.",
                spoiler="Политический компромисс смягчил первоначальный вариант реформы.",
                topic=topic,
                confidence_score=0.82,
            )
        if topic == "economy":
            return LLMNewsOutput(
                title=(f"Новость из Германии (черновик {key % 1_000_000:06d})")[:500],
                one_sentence_summary=(
                    "Краткое изложение на русском в этом режиме не строится из текста фида. "
                    "Для автоматического перевода с немецкого укажите LLM_PROVIDER=openai в окружении. "
                    "Полный оригинал — по ссылке в карточке."
                )[:2000],
                plain_language="Если коротко: экономическая новость в заглушке обобщена; детали — в оригинале.",
                impact_presentation="single",
                impact_unified=(
                    "В режиме stub один смысловой блок: проверьте, как сюжет касается рынка, налогов и быта — "
                    "детальный разбор даст только реальная LLM с немецкого текста."
                ),
                impact_owner="",
                impact_tenant="",
                impact_buyer="",
                action_items="- Проверьте текущий статус\n- Изучите официальные субсидии",
                bonus_block="В экономике (stub) используется один абзац «что значит» вместо трёх углов.",
                spoiler="Политический компромисс смягчил первоначальный вариант реформы.",
                topic=topic,
                confidence_score=0.82,
            )
        return LLMNewsOutput(
            title=(f"Новость из Германии (черновик {key % 1_000_000:06d})")[:500],
            one_sentence_summary=(
                "Краткое изложение на русском в этом режиме не строится из текста фида. "
                "Для автоматического перевода с немецкого укажите LLM_PROVIDER=openai в окружении. "
                "Полный оригинал — по ссылке в карточке."
            )[:2000],
            plain_language=(
                "Если коротко: это изменение повлияет на расходы и правила для жителей Германии."
            ),
            impact_presentation="multi",
            impact_unified="",
            impact_owner=(
                "С одной стороны, для поставщиков услуг и владельцев активов важно заранее оценить сроки и "
                "издержки."
            ),
            impact_tenant=(
                "С другой — для наёмщиков жилья: уточните, как это отразится на договоре и ежемесячных платежах."
            ),
            impact_buyer=(
                "Для потребителей и покупателей имеет смысл заложить в планы новые требования и возможные субсидии."
            ),
            action_items="- Проверьте текущий статус\n- Изучите официальные субсидии",
            bonus_block="В быту (stub) показан формат «три стороны» вместе.",
            spoiler="Политический компромисс смягчил первоначальный вариант реформы.",
            topic=topic,
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
