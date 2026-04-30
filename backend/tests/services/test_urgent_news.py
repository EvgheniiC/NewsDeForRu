from __future__ import annotations

from app.schemas.llm_output import LLMNewsOutput
from app.services.urgent_news import ev_is_urgent_news


def test_ev_is_urgent_news_default_false() -> None:
    llm: LLMNewsOutput = LLMNewsOutput(
        title="Т",
        one_sentence_summary="К",
        plain_language="П",
        impact_presentation="multi",
        impact_unified="",
        impact_owner="a",
        impact_tenant="b",
        impact_buyer="c",
        action_items="- x",
        bonus_block="b",
        spoiler="s",
        topic="life",
        confidence_score=0.5,
        importance_score=5,
    )
    assert ev_is_urgent_news("t", "s", llm) is False
