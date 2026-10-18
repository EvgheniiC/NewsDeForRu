"""Longer cards for open statistical sources.

Destatis and Eurostat (and the other official datasets) may be paraphrased
freely. Publisher feeds that are still waiting for permission stay on the
short independent-draft rules and are not handled here.
"""

from __future__ import annotations

_OPEN_PARAPHRASE_SOURCE_KEYS: frozenset[str] = frozenset(
    {
        "destatis",
        "destatis_genesis",
        "eurostat",
        "govdata",
        "data_europa",
    }
)

_MAX_PROSE_FIGURES_CHARS: int = 240


def open_paraphrase_source_keys() -> tuple[str, ...]:
    """Stable key list for SQL filters. Same set as ``is_open_paraphrase_source``."""
    return tuple(sorted(_OPEN_PARAPHRASE_SOURCE_KEYS))


def is_open_paraphrase_source(source_key: str | None) -> bool:
    """True for licensed official statistics, not for publisher RSS."""
    return (source_key or "").strip().casefold() in _OPEN_PARAPHRASE_SOURCE_KEYS


def open_source_card_instructions() -> str:
    """User-message rules for a slightly longer open-source card."""
    return (
        "Это открытый официальный источник. Исходный текст можно пересказывать свободно: "
        "не переводи предложение за предложением и не сохраняй формулировки источника. "
        "Не выдумывай цифры, даты и факты, которых нет во входных данных.\n"
        "one_sentence_summary — не одно предложение, а 2–3 коротких предложения: "
        "что изменилось и главная цифра. Это суть карточки, не статья.\n"
        "bonus_block — короткий блок «цифры»: 2–4 строки, каждая начинается с \"- \" "
        "и содержит число из блока Key figures или из текста. "
        "Если конкретных чисел нет, bonus_block = \"\".\n"
        "impact_presentation обязательно \"single\". "
        "impact_unified — один короткий абзац «что это значит» для жителей Германии, "
        "только вывод из этих цифр, без домыслов. "
        "impact_owner, impact_tenant и impact_buyer оставь пустыми строками.\n"
        "spoiler оставь пустым.\n"
        "Если в релизе есть срок, правило с сегодняшнего дня, предупреждение или сбой, "
        "в impact_unified назови, кого это касается сегодня, и заполни action_items "
        "1–2 строками, каждая начинается с \"- \". "
        "Если конкретного шага на сегодня нет, action_items оставь пустым "
        "и не подставляй общее «проверьте официальный сайт».\n\n"
    )


def figures_from_bonus(source_key: str | None, bonus_block: str) -> str:
    """Return the figures block for an open source, or empty text otherwise."""
    if not is_open_paraphrase_source(source_key):
        return ""
    text: str = bonus_block.strip()
    if text == "" or not any(char.isdigit() for char in text):
        return ""
    lines: list[str] = [line.strip() for line in text.splitlines() if line.strip()]
    bulleted: bool = bool(lines) and all(line.startswith("- ") for line in lines)
    if not bulleted and len(text) > _MAX_PROSE_FIGURES_CHARS:
        return ""
    return text


def meaning_for_open_card(
    source_key: str | None,
    impact_presentation: str,
    impact_unified: str,
) -> str:
    """Return the single 'what this means' paragraph for an open source."""
    if not is_open_paraphrase_source(source_key):
        return ""
    if impact_presentation != "single":
        return ""
    return impact_unified.strip()
