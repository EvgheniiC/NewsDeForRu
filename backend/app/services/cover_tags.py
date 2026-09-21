"""Closed illustration tags for topic-cover folders (independent of feed filters)."""

from __future__ import annotations

from typing import Final

from app.models.news import CoverTag, NewsTopic

DEFAULT_COVER_TAG_BY_TOPIC: Final[dict[NewsTopic, CoverTag]] = {
    NewsTopic.POLITICS: CoverTag.GOVERNMENT,
    NewsTopic.ECONOMY: CoverTag.MONEY,
    NewsTopic.LIFE: CoverTag.FAMILY,
}

COVER_TAGS_BY_TOPIC: Final[dict[NewsTopic, tuple[CoverTag, ...]]] = {
    NewsTopic.POLITICS: (
        CoverTag.GOVERNMENT,
        CoverTag.ELECTIONS,
        CoverTag.EU,
        CoverTag.SECURITY,
    ),
    NewsTopic.ECONOMY: (
        CoverTag.MONEY,
        CoverTag.JOBS,
        CoverTag.ENERGY,
        CoverTag.CONSTRUCTION,
        CoverTag.TRANSPORT,
    ),
    NewsTopic.LIFE: (
        CoverTag.HEALTH,
        CoverTag.EDUCATION,
        CoverTag.SPORT,
        CoverTag.FAMILY,
        CoverTag.WEATHER,
        CoverTag.CULTURE,
    ),
}

_EXACT_SYNONYMS: Final[dict[str, CoverTag]] = {
    "government": CoverTag.GOVERNMENT,
    "gov": CoverTag.GOVERNMENT,
    "bundestag": CoverTag.GOVERNMENT,
    "cabinet": CoverTag.GOVERNMENT,
    "ministerium": CoverTag.GOVERNMENT,
    "regierung": CoverTag.GOVERNMENT,
    "politics": CoverTag.GOVERNMENT,
    "elections": CoverTag.ELECTIONS,
    "election": CoverTag.ELECTIONS,
    "wahl": CoverTag.ELECTIONS,
    "wahlen": CoverTag.ELECTIONS,
    "voting": CoverTag.ELECTIONS,
    "eu": CoverTag.EU,
    "europa": CoverTag.EU,
    "europe": CoverTag.EU,
    "brussels": CoverTag.EU,
    "security": CoverTag.SECURITY,
    "defence": CoverTag.SECURITY,
    "defense": CoverTag.SECURITY,
    "military": CoverTag.SECURITY,
    "police": CoverTag.SECURITY,
    "war": CoverTag.SECURITY,
    "money": CoverTag.MONEY,
    "finance": CoverTag.MONEY,
    "finanz": CoverTag.MONEY,
    "inflation": CoverTag.MONEY,
    "tax": CoverTag.MONEY,
    "steuern": CoverTag.MONEY,
    "bank": CoverTag.MONEY,
    "economy": CoverTag.MONEY,
    "jobs": CoverTag.JOBS,
    "job": CoverTag.JOBS,
    "labor": CoverTag.JOBS,
    "labour": CoverTag.JOBS,
    "arbeit": CoverTag.JOBS,
    "unemployment": CoverTag.JOBS,
    "energy": CoverTag.ENERGY,
    "strom": CoverTag.ENERGY,
    "gas": CoverTag.ENERGY,
    "klima": CoverTag.ENERGY,
    "construction": CoverTag.CONSTRUCTION,
    "housing": CoverTag.CONSTRUCTION,
    "bauen": CoverTag.CONSTRUCTION,
    "wohnung": CoverTag.CONSTRUCTION,
    "miete": CoverTag.CONSTRUCTION,
    "transport": CoverTag.TRANSPORT,
    "bahn": CoverTag.TRANSPORT,
    "traffic": CoverTag.TRANSPORT,
    "mobility": CoverTag.TRANSPORT,
    "health": CoverTag.HEALTH,
    "gesundheit": CoverTag.HEALTH,
    "krankenkasse": CoverTag.HEALTH,
    "hospital": CoverTag.HEALTH,
    "education": CoverTag.EDUCATION,
    "schule": CoverTag.EDUCATION,
    "school": CoverTag.EDUCATION,
    "university": CoverTag.EDUCATION,
    "sport": CoverTag.SPORT,
    "sports": CoverTag.SPORT,
    "fussball": CoverTag.SPORT,
    "fußball": CoverTag.SPORT,
    "family": CoverTag.FAMILY,
    "life": CoverTag.FAMILY,
    "alltag": CoverTag.FAMILY,
    "weather": CoverTag.WEATHER,
    "wetter": CoverTag.WEATHER,
    "storm": CoverTag.WEATHER,
    "culture": CoverTag.CULTURE,
    "kultur": CoverTag.CULTURE,
    "kunst": CoverTag.CULTURE,
}

# Longer needles first so "krankenkasse" wins over "kasse".
_KEYWORD_NEEDLES: Final[tuple[tuple[str, CoverTag], ...]] = (
    ("krankenkasse", CoverTag.HEALTH),
    ("universit", CoverTag.EDUCATION),
    (" bundestag", CoverTag.GOVERNMENT),
    ("regierung", CoverTag.GOVERNMENT),
    ("minister", CoverTag.GOVERNMENT),
    ("парламент", CoverTag.GOVERNMENT),
    ("правительств", CoverTag.GOVERNMENT),
    ("бундестаг", CoverTag.GOVERNMENT),
    ("выбор", CoverTag.ELECTIONS),
    ("голосов", CoverTag.ELECTIONS),
    ("wahlen", CoverTag.ELECTIONS),
    ("election", CoverTag.ELECTIONS),
    ("евросоюз", CoverTag.EU),
    ("брюссел", CoverTag.EU),
    ("european", CoverTag.EU),
    ("безопасн", CoverTag.SECURITY),
    ("военн", CoverTag.SECURITY),
    ("полиц", CoverTag.SECURITY),
    ("bundeswehr", CoverTag.SECURITY),
    ("инфляц", CoverTag.MONEY),
    ("налог", CoverTag.MONEY),
    ("финанс", CoverTag.MONEY),
    ("безработ", CoverTag.JOBS),
    ("зарплат", CoverTag.JOBS),
    ("энерг", CoverTag.ENERGY),
    ("стройк", CoverTag.CONSTRUCTION),
    ("жиль", CoverTag.CONSTRUCTION),
    ("аренд", CoverTag.CONSTRUCTION),
    ("транспорт", CoverTag.TRANSPORT),
    ("железн", CoverTag.TRANSPORT),
    ("здоров", CoverTag.HEALTH),
    ("образован", CoverTag.EDUCATION),
    ("школ", CoverTag.EDUCATION),
    ("спорт", CoverTag.SPORT),
    ("футбол", CoverTag.SPORT),
    ("погод", CoverTag.WEATHER),
    ("культур", CoverTag.CULTURE),
    ("семь", CoverTag.FAMILY),
    ("construction", CoverTag.CONSTRUCTION),
    ("housing", CoverTag.CONSTRUCTION),
    ("transport", CoverTag.TRANSPORT),
    ("education", CoverTag.EDUCATION),
    ("security", CoverTag.SECURITY),
    ("weather", CoverTag.WEATHER),
    ("culture", CoverTag.CULTURE),
    ("energy", CoverTag.ENERGY),
    ("health", CoverTag.HEALTH),
    ("sport", CoverTag.SPORT),
    ("jobs", CoverTag.JOBS),
    ("europa", CoverTag.EU),
)


def _topic_from_unknown(topic: object) -> NewsTopic:
    if isinstance(topic, NewsTopic):
        return topic
    if topic is None:
        return NewsTopic.LIFE
    raw: str = str(topic).strip().casefold()
    for item in NewsTopic:
        if raw == item.value:
            return item
    return NewsTopic.LIFE


def default_cover_tag_for_topic(topic: NewsTopic | str | object) -> CoverTag:
    topic_enum: NewsTopic = _topic_from_unknown(topic)
    return DEFAULT_COVER_TAG_BY_TOPIC.get(topic_enum, CoverTag.FAMILY)


def coerce_cover_tag(value: object, topic: object) -> CoverTag:
    """Map LLM / moderator drift onto a closed CoverTag, else the topic default."""
    fallback: CoverTag = default_cover_tag_for_topic(topic)
    if value is None:
        return fallback
    s: str = str(value).strip().casefold()
    if not s:
        return fallback
    exact: CoverTag | None = _EXACT_SYNONYMS.get(s)
    if exact is not None:
        return exact
    for tag in CoverTag:
        if s == tag.value:
            return tag
    padded: str = f" {s} "
    for needle, tag in _KEYWORD_NEEDLES:
        if needle in s or needle in padded:
            return tag
    return fallback
