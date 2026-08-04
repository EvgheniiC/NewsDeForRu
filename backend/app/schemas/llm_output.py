from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NewsTopicLiteral = Literal["politics", "economy", "life"]


def _coerce_topic_for_llm(value: object) -> NewsTopicLiteral:
    """
    Map model drift (Russian/German labels) onto schema literals politics | economy | life.
    """
    if value is None:
        return "life"
    s: str = str(value).strip().casefold()
    if not s:
        return "life"
    if s in {"politics", "politic", "political"}:
        return "politics"
    if s in {"economy", "economic", "economics", "finance", "business"}:
        return "economy"
    if s in {"life", "lifestyle", "society", "culture"}:
        return "life"
    if s in {"politik", "innenpolitik", "außenpolitik", "aussenpolitik"}:
        return "politics"
    if s in {"wirtschaft", "ökonomie", "oekonomie", "finanzen"}:
        return "economy"
    if s in {"leben", "alltag", "gesellschaft"}:
        return "life"
    if any(
        marker in s
        for marker in (
            "политик",
            "выбор",
            "правительств",
            "министр",
            "парламент",
            "бундестаг",
            "законопроект",
            "дипломат",
            "внешнеполит",
            "государств",
        )
    ):
        return "politics"
    if any(
        marker in s
        for marker in (
            "экономик",
            "финанс",
            "бизнес",
            "рынок",
            "инфляц",
            "акци",
            "компани",
            "налог",
            "бюджет",
            "валют",
        )
    ):
        return "economy"
    if any(
        marker in s
        for marker in (
            "жизн",
            "быт",
            "здоров",
            "образован",
            "семь",
            "жиль",
            "страхов",
            "потребит",
            "спорт",
            "культур",
        )
    ):
        return "life"
    return "life"


def _coerce_is_positive(value: object) -> bool:
    """Normalize LLM drift (strings, ints) onto a strict boolean."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    s: str = str(value).strip().casefold()
    if s in {"true", "1", "yes", "да", "positiv", "positive"}:
        return True
    if s in {"false", "0", "no", "нет", "negativ", "negative"}:
        return False
    return False


ImpactPresentationLiteral = Literal["multi", "single", "none"]

# LLMs sometimes return JSON string placeholders instead of real text.
_FORBIDDEN_LLM_TOKENS: frozenset[str] = frozenset(
    {
        "None",
        "null",
        "NULL",
        "N/A",
        "n/a",
        "<none>",
        "undefined",
    }
)

_FORBIDDEN_FEED_SNIPPET_TOKENS_CF: frozenset[str] = frozenset(
    x.casefold() for x in _FORBIDDEN_LLM_TOKENS
)


def meaningful_feed_text(value: str) -> str:
    """
    Return stripped RSS/HTML text, or empty if it is only a null placeholder.

    Some feeds emit the literal word "None" (or "null") when the description
    is missing; treat that as no snippet so we do not prefix it as a German draft.
    """
    t: str = value.strip()
    if not t:
        return ""
    if t.casefold() in _FORBIDDEN_FEED_SNIPPET_TOKENS_CF:
        return ""
    return t


def _llm_string(v: str) -> str:
    t: str = v.strip()
    if not t:
        msg: str = "String field must be non-empty after trim"
        raise ValueError(msg)
    if t in _FORBIDDEN_LLM_TOKENS:
        msg2: str = "String field must not be a null placeholder (e.g. None, null, N/A)"
        raise ValueError(msg2)
    return t


def _optional_llm_string(v: str) -> str:
    """Like :func:`_llm_string` but allows empty (for optional editorial slots)."""
    t: str = v.strip()
    if not t:
        return ""
    if t in _FORBIDDEN_LLM_TOKENS:
        return ""
    return t


def coerce_llm_news_dict_before_validate(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Fix common LLM JSON mistakes before :class:`LLMNewsOutput` validation.

    Normalizes optional strings and maps topic synonyms onto politics/economy/life.
    Missing core Russian fields remain invalid so publisher text is never substituted.
    """
    out: dict[str, Any] = dict(data)

    def _txt(key: str) -> str:
        v: object | None = out.get(key)
        if v is None:
            return ""
        return str(v).strip()

    title_v: str = _txt("title")
    out["title"] = title_v[:500]

    osum: str = _txt("one_sentence_summary")
    out["one_sentence_summary"] = osum[:2000]

    plain: str = _txt("plain_language")
    out["plain_language"] = plain[:8000]

    act: str = _txt("action_items")
    out["action_items"] = _optional_llm_string(act)[:4000]

    bonus: str = _txt("bonus_block")
    out["bonus_block"] = bonus[:2000]

    spoil: str = _txt("spoiler")
    out["spoiler"] = spoil[:2000]

    out["topic"] = _coerce_topic_for_llm(out.get("topic"))
    out["is_positive"] = _coerce_is_positive(out.get("is_positive"))
    return out


class LLMNewsOutput(BaseModel):
    """Structured LLM result aligned with the publication pipeline and DB model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    title: str = Field(..., min_length=1, max_length=500)
    one_sentence_summary: str = Field(..., min_length=1, max_length=2000)
    plain_language: str = Field(..., min_length=1, max_length=8000)
    impact_presentation: ImpactPresentationLiteral = Field(
        default="multi",
        description="multi = three audience angles; single = one takeaway; none = no impact block.",
    )
    impact_unified: str = Field(default="", max_length=4000)
    impact_owner: str = Field(default="", max_length=4000)
    impact_tenant: str = Field(default="", max_length=4000)
    impact_buyer: str = Field(default="", max_length=4000)
    action_items: str = Field(default="", max_length=4000)
    bonus_block: str = Field(default="", max_length=2000)
    spoiler: str = Field(default="", max_length=2000)
    topic: NewsTopicLiteral = Field(
        ...,
        description="Primary category: politics, economy, or everyday life in Germany.",
    )
    is_positive: bool = Field(
        ...,
        description=(
            "True only when the story is clearly uplifting, constructive, or reports a genuine "
            "improvement — not merely neutral or mixed news."
        ),
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    importance_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="How important this story is for people living in Germany (1=trivial, 10=critical).",
    )

    @field_validator(
        "title",
        "one_sentence_summary",
        "plain_language",
        mode="before",
    )
    @classmethod
    def _non_empty_core_strings(cls, v: object) -> object:
        if not isinstance(v, str):
            return v
        return _llm_string(v)

    @field_validator("action_items", "bonus_block", "spoiler", mode="before")
    @classmethod
    def _optional_editorial_strings(cls, v: object) -> object:
        if not isinstance(v, str):
            return v
        return _optional_llm_string(v)

    @model_validator(mode="before")
    @classmethod
    def _normalize_impact_in_dict(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d: dict[str, Any] = dict(data)
        p: str = str(d.get("impact_presentation", "multi"))
        if p not in ("multi", "single", "none"):
            perr: str = f"impact_presentation must be 'multi', 'single', or 'none', got {p!r}"
            raise ValueError(perr)
        for k in ("impact_unified", "impact_owner", "impact_tenant", "impact_buyer"):
            if d.get(k) is None:
                d[k] = ""
        o: str = str(d.get("impact_owner", "")).strip()
        t: str = str(d.get("impact_tenant", "")).strip()
        b: str = str(d.get("impact_buyer", "")).strip()
        u: str = str(d.get("impact_unified", "")).strip()
        if p == "multi":
            d["impact_owner"] = _llm_string(o)
            d["impact_tenant"] = _llm_string(t)
            d["impact_buyer"] = _llm_string(b)
            if u:
                msg: str = "impact_unified must be empty when impact_presentation is 'multi'"
                raise ValueError(msg)
            d["impact_unified"] = ""
        elif p == "single":
            d["impact_unified"] = _llm_string(u)
            if o or t or b:
                msg2: str = "impact_owner, impact_tenant, impact_buyer must be empty when 'single'"
                raise ValueError(msg2)
            d["impact_owner"] = ""
            d["impact_tenant"] = ""
            d["impact_buyer"] = ""
        else:
            if o or t or b or u:
                msg3: str = "All impact fields must be empty when impact_presentation is 'none'"
                raise ValueError(msg3)
            d["impact_unified"] = ""
            d["impact_owner"] = ""
            d["impact_tenant"] = ""
            d["impact_buyer"] = ""
        d["impact_presentation"] = p
        return d

    @classmethod
    def system_prompt_addendum(cls) -> str:
        """Text appended to the system instruction so the model knows exact keys and types."""
        return (
            "Return exactly one JSON object (no markdown, no extra text) with these keys: "
            "title, one_sentence_summary, plain_language, impact_presentation, impact_unified, "
            "impact_owner, impact_tenant, impact_buyer, action_items, bonus_block, spoiler, "
            "topic, is_positive, confidence_score, importance_score. "
            "topic MUST be the English token exactly one of: politics, economy, life — "
            "never Russian (e.g. экономика) or German words; pick the story's main angle.\n"
            "Rubric: politics = government, political parties, elections, parliament/Bundestag, "
            "laws in legislative process, ministers, foreign policy, state institutions, diplomacy. "
            "economy = business and markets, companies, stocks, inflation, interest rates, "
            "labor market or trade in macro/business context, major economic policy, industry. "
            "life = practical impact on residents' daily life (housing as tenant, health insurance, "
            "family/school, local rules, consumer tips) when the main frame is 'what it means for you "
            "day to day' rather than political process or business cycle. Do not default to life when "
            "the story is clearly political or business/economic news.\n"
            "is_positive MUST be a JSON boolean true or false (not a string). "
            "Set true ONLY when the core of the story is clearly good news, an improvement, "
            "or something genuinely uplifting for residents: new social programs or subsidies, "
            "price cuts or expanded benefits, scientific/medical breakthroughs that help people, "
            "successful rescues, infrastructure or environmental improvements, charitable or "
            "heartwarming human-interest stories with a constructive outcome. "
            "Set false for disasters, crime, scandals, conflicts, protests, layoffs, mixed "
            "stories (both upside and downside), routine neutral announcements, and anything "
            "where the dominant tone is negative or merely informational.\n"
            "impact_presentation must be one of: multi, single, none.\n"
            "- Use multi when the story has three clearly different affected groups or standpoints and "
            "all three are worth showing together (e.g. fuel: station owner vs driver vs state budget). "
            "Then fill impact_owner, impact_tenant, impact_buyer with three self-contained Russian "
            "angles (key names are schema slots only) and set impact_unified to an empty string \"\".\n"
            "- Use single for speeches, quotes, foreign policy commentary, or analysis where one "
            "unified 'what this means' paragraph is right — one short or medium paragraph in Russian. "
            "Set impact_presentation to single, put that text in impact_unified, and set impact_owner, "
            "impact_tenant, impact_buyer to \"\".\n"
            "- Use none when the summary and plain_language already cover meaning and a separate impact "
            "section would be redundant (rare). Set all four impact string fields to \"\".\n"
            "All other string values must be in Russian. confidence_score is a number from 0 to 1.\n"
            "importance_score is an integer from 1 to 10: how important this news is for residents "
            "of Germany (laws, economy, safety, major public life changes = higher; local trivia = lower). "
            "action_items lists concrete reader steps in Russian (bullet lines starting with \"- \"); "
            "use an empty string \"\" when the story has no actionable checklist (pure commentary, "
            "no practical steps — do not invent generic «check official sources» filler). "
            "bonus_block and spoiler may be empty strings \"\" when there is no separate editorial angle "
            "or hook beyond plain_language (no filler text)."
        )


VALIDATION_FALLBACK_TITLE: str = "Материал требует ручной проверки"
VALIDATION_FALLBACK_SUMMARY: str = (
    "Автоматическая обработка не сформировала надёжную русскоязычную сводку."
)


def fallback_after_validation_failure() -> LLMNewsOutput:
    """Return a safe review-only result without publisher text or invented claims."""
    return LLMNewsOutput(
        title=VALIDATION_FALLBACK_TITLE,
        one_sentence_summary=VALIDATION_FALLBACK_SUMMARY,
        plain_language=(
            "Публикация отложена до повторной обработки или проверки редактором."
        ),
        impact_presentation="none",
        impact_unified="",
        impact_owner="",
        impact_tenant="",
        impact_buyer="",
        action_items="",
        bonus_block="",
        spoiler="",
        topic="life",
        is_positive=False,
        confidence_score=0.0,
        importance_score=1,
    )


def is_validation_fallback(output: LLMNewsOutput) -> bool:
    """True when output is the empty placeholder (no usable Russian news card)."""
    return (
        output.title == VALIDATION_FALLBACK_TITLE
        and output.one_sentence_summary == VALIDATION_FALLBACK_SUMMARY
        and output.confidence_score == 0.0
    )
