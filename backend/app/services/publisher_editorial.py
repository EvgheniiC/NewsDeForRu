from __future__ import annotations

PUBLISHER_EDITORIAL_SOURCE_NAMES: dict[str, str] = {
    "bild": "BILD",
    "die_zeit": "ZEIT",
    "spiegel": "SPIEGEL",
    "tagesschau": "Tagesschau",
    "welt": "WELT",
    "zdf": "ZDF heute",
}

PUBLISHER_EDITORIAL_SOURCE_KEYS: frozenset[str] = frozenset(
    PUBLISHER_EDITORIAL_SOURCE_NAMES
)

_SENSITIVE_INCIDENT_TERMS: tuple[str, ...] = (
    "amok",
    "anschlag",
    "attacke",
    "explosion",
    "kampf",
    "messer",
    "mord",
    "schlägerei",
    "schiesserei",
    "schießerei",
    "spreng",
    "stich",
    "töt",
    "überfahr",
)


def normalize_source_key(source_key: str | None) -> str:
    """Return a stable source key for source-aware editorial rules."""
    return (source_key or "").strip().casefold()


def is_publisher_editorial_source(source_key: str | None) -> bool:
    """Whether a source requires the publisher-specific editorial workflow."""
    return normalize_source_key(source_key) in PUBLISHER_EDITORIAL_SOURCE_KEYS


def publisher_source_name(source_key: str | None) -> str:
    """Return a human-readable publisher name without trusting model input."""
    normalized: str = normalize_source_key(source_key)
    return PUBLISHER_EDITORIAL_SOURCE_NAMES.get(normalized, normalized or "источник")


def is_sensitive_incident(title: str, summary: str) -> bool:
    """Detect violence and major public-safety incidents in German RSS text."""
    text: str = f"{title}\n{summary}".casefold()
    return any(term in text for term in _SENSITIVE_INCIDENT_TERMS)


def publisher_editorial_instructions(
    source_key: str | None,
    *,
    sensitive: bool,
) -> str:
    """Build instructions for an unlicensed publisher draft.

    The publisher has not sent written permission. The card names no source,
    contains no link, and stays a moderation draft. The title stays as short as
    a licensed card. The body is a little longer: four or five connected
    sentences instead of the two or three used for a licensed summary.
    """
    source_name: str = publisher_source_name(source_key)
    sensitive_rules: str = ""
    if sensitive:
        sensitive_rules = (
            "Это сообщение о насилии или угрозе общественной безопасности. "
            "Не используй кликбейт и графические подробности. Не называй подозреваемого "
            "преступником до решения суда. Не предполагай мотив, гражданство, религию, "
            "миграционный статус, психическое состояние или терроризм. Сохраняй оговорки "
            "«предположительно» и «подозреваемый» и явно отмечай неизвестное. "
        )
    return (
        f"Входные данные — RSS-анонс издателя {source_name}, а не разрешение на цитирование. "
        "Создай самостоятельный редакционный черновик на русском языке только по явно "
        "указанным проверяемым фактам. Не переводи и не перефразируй текст предложение за "
        "предложением; не сохраняй исходную структуру, стиль или уникальные выводы. "
        "Не добавляй факты, контекст, цитаты или причинно-следственные связи, которых нет во "
        "входных данных. Не называй СМИ, полицию, партию, ведомство или другой источник. "
        "Не пиши «по данным», «сообщает» и «источник». Не вставляй ссылки и адреса сайтов. "
        "Заголовок оставь одной короткой строкой, без второго предложения. "
        "one_sentence_summary — 4–5 связных предложений: что произошло, кого это касается "
        "и что из этого следует. Это чуть подробнее, чем краткая сводка лицензированного "
        "источника из 2–3 предложений, но не статья. Порядок фактов должен быть логичным. "
        "plain_language — те же факты простым языком, двумя короткими абзацами, не короче "
        "one_sentence_summary. "
        "Если данных недостаточно, снизь confidence_score и прямо напиши, что сведения неполные. "
        f"{sensitive_rules}"
        "Карточка всегда остаётся черновиком для ручной модерации."
    )
