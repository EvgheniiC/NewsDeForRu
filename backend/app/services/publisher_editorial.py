from __future__ import annotations

PUBLISHER_EDITORIAL_SOURCE_NAMES: dict[str, str] = {
    "die_zeit": "ZEIT",
    "spiegel": "SPIEGEL",
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


def publisher_editorial_instructions(source_key: str | None, *, sensitive: bool) -> str:
    """Build strict instructions for an independent, attributed moderation draft."""
    source_name: str = publisher_source_name(source_key)
    sensitive_rules: str = ""
    if sensitive:
        sensitive_rules = (
            "Это сообщение о насилии или угрозе общественной безопасности. "
            "Не используй кликбейт и графические подробности. Не называй подозреваемого "
            "преступником до решения суда. Не предполагай мотив, гражданство, религию, "
            "миграционный статус, психическое состояние или терроризм. Сохраняй оговорки "
            "«по данным», «предположительно», «подозреваемый» и явно отмечай неизвестное. "
        )
    return (
        f"Входные данные — RSS-анонс издателя {source_name}, а не официальный первоисточник. "
        "Создай самостоятельный редакционный черновик на русском языке только по явно "
        "указанным проверяемым фактам. Не переводи и не перефразируй текст предложение за "
        "предложением; не сохраняй исходную структуру, заголовок, стиль или уникальные выводы. "
        "Не добавляй факты, контекст, цитаты или причинно-следственные связи, которых нет во "
        "входных данных. Атрибутируй спорные и предварительные сведения формулировкой "
        f"«по данным {source_name}». Если данных недостаточно, снизь confidence_score и прямо "
        "укажи, что сведения требуют проверки по полиции, прокуратуре, пожарной службе, суду "
        "или другому официальному источнику. "
        f"{sensitive_rules}"
        "Материал всегда является черновиком для ручной модерации."
    )
