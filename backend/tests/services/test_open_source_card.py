from app.services.open_source_card import (
    figures_from_bonus,
    meaning_for_open_card,
    open_source_card_instructions,
)


def test_figures_stay_on_open_sources_and_off_publishers() -> None:
    bullets: str = "- 2,4 %\n- 83,6 млн"
    assert figures_from_bonus("eurostat", bullets) == bullets
    assert figures_from_bonus("destatis", bullets) == bullets
    assert figures_from_bonus("spiegel", bullets) == ""
    assert figures_from_bonus("bild", bullets) == ""
    assert figures_from_bonus("eurostat", "Без чисел в этом блоке.") == ""


def test_long_prose_bonus_is_not_relabelled_as_figures() -> None:
    prose: str = "В 2024 году " + ("контекст " * 40)
    assert figures_from_bonus("destatis", prose) == ""


def test_meaning_requires_single_impact_on_an_open_source() -> None:
    text: str = "Для жителей это означает более дорогую корзину."
    assert meaning_for_open_card("eurostat", "single", text) == text
    assert meaning_for_open_card("eurostat", "none", text) == ""
    assert meaning_for_open_card("welt", "single", text) == ""


def test_open_card_instructions_ask_for_a_longer_lead() -> None:
    instructions: str = open_source_card_instructions()
    assert "2–3 коротких предложения" in instructions
    assert "что это значит" in instructions
    assert "кого это касается сегодня" in instructions
    assert "Spiegel" not in instructions
