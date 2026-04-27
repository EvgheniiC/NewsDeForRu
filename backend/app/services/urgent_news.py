"""Breaking / urgent news detection (pipeline hook)."""

from __future__ import annotations

from app.schemas.llm_output import LLMNewsOutput


def ev_is_urgent_news(
    raw_title: str,
    raw_summary: str,
    llm: LLMNewsOutput,
) -> bool:
    """
    Return True if this item should appear under the "⚡ Срочно" feed filter.

    TODO EV: Replace with a real policy (editorial rules, model scores, source tags,
    external news wires, or manual flags). The default is conservative (never urgent).
    """
    _ = (raw_title, raw_summary, llm)
    return False


__all__ = ["ev_is_urgent_news"]
