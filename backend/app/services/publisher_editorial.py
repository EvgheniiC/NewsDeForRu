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
    primary_source_name: str | None = None,
    primary_source_url: str | None = None,
) -> str:
    """Build strict instructions for an independent moderation draft.

    When the RSS item links a primary source, the draft must follow that source
    instead of the publisher. When it does not, the draft must not name a source.
    """
    source_name: str = publisher_source_name(source_key)
    primary_name: str = (primary_source_name or "").strip()
    primary_url: str = (primary_source_url or "").strip()
    sensitive_rules: str = ""
    if sensitive:
        sensitive_rules = (
            "Это сообщение о насилии или угрозе общественной безопасности. "
            "Не используй кликбейт и графические подробности. Не называй подозреваемого "
            "преступником до решения суда. Не предполагай мотив, гражданство, религию, "
            "миграционный статус, психическое состояние или терроризм. Сохраняй оговорки "
            "«предположительно» и «подозреваемый» и явно отмечай неизвестное. "
        )
    if primary_url:
        cited_name: str = primary_name or primary_url
        origin_rules: str = (
            f"В анонсе есть ссылка на первичный источник: {cited_name} ({primary_url}). "
            "Напиши короткую собственную новость по явно указанным фактам этого первоисточника, "
            "а не сокращённый перевод или пересказ другого СМИ. "
            f"Не называй {source_name} и не пиши «по данным {source_name}». "
            f"Укажи первоисточник формулировкой «по данным {cited_name}», "
            "и только если это прямо сказано во входных данных. "
        )
    else:
        origin_rules = (
            "Ссылки на первичный источник во входных данных нет. "
            "Не указывай, на что опирается текст: не называй СМИ, полицию, партию, ведомство или другой источник. "
            "Не пиши «по данным», «сообщает» и «источник». "
        )
    uncertainty_rules: str = (
        "Если данных недостаточно, снизь confidence_score и прямо укажи, что сведения неполные. "
        if not primary_url
        else (
            "Если данных недостаточно, снизь confidence_score и прямо укажи, "
            "что сведения требуют проверки по первичному источнику. "
        )
    )
    return (
        f"Входные данные — RSS-анонс издателя {source_name}, а не официальный первоисточник. "
        "Создай самостоятельный редакционный черновик на русском языке только по явно "
        "указанным проверяемым фактам. Не переводи и не перефразируй текст предложение за "
        "предложением; не сохраняй исходную структуру, заголовок, стиль или уникальные выводы. "
        "Не добавляй факты, контекст, цитаты или причинно-следственные связи, которых нет во "
        f"входных данных. {origin_rules}{uncertainty_rules}"
        f"{sensitive_rules}"
        "Материал всегда является черновиком для ручной модерации."
    )
