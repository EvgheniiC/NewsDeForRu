from __future__ import annotations

import json
import re
from json import JSONDecodeError
from typing import Any

from app.schemas.llm_output import LLMNewsOutput

_FENCE_RE: re.Pattern[str] = re.compile(
    r"```(?:json)?\s*([\s\S]*?)\s*```",
    re.IGNORECASE,
)


def extract_json_string(raw: str) -> str:
    """Strip optional markdown code fences; otherwise take first {...} span."""
    t: str = raw.strip()
    m: re.Match[str] | None = _FENCE_RE.search(t)
    if m:
        t = m.group(1).strip()
    if t.lstrip().startswith("{"):
        return t
    start: int = t.find("{")
    end: int = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1]
    return t


def parse_llm_news_json(text: str) -> LLMNewsOutput:
    """Parse model output into a validated :class:`LLMNewsOutput`."""
    s: str = extract_json_string(text)
    try:
        data: Any = json.loads(s)
    except JSONDecodeError as e:
        msg: str = f"Invalid JSON: {e}"
        raise ValueError(msg) from e
    if not isinstance(data, dict):
        omsg: str = "JSON root must be an object"
        raise TypeError(omsg)
    return LLMNewsOutput.model_validate(data)


def build_repair_user_message(validation_error: str, raw_snippet: str) -> str:
    """User message for a second attempt after validation failure."""
    err: str = validation_error
    if len(raw_snippet) > 6_000:
        raw_snippet = raw_snippet[:6_000] + "…(truncated)"
    return (
        "The previous JSON was invalid. Fix the structure and values so they match the schema. "
        f"Errors:\n{err}\n\n"
        f"Invalid output (string form):\n{raw_snippet}\n\n"
        "Reply with one corrected JSON object only, no code fences, no text around it."
    )
