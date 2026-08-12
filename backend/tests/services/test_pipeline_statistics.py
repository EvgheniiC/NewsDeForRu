from app.services.pipeline_service import has_concrete_statistic


def test_concrete_statistic_rejects_dates_without_statistical_values() -> None:
    assert not has_concrete_statistic(
        "Население Германии на 1 января распределено по группам.",
        "Данные показывают ситуацию на начало 2025 года.",
    )


def test_concrete_statistic_accepts_common_eurostat_values() -> None:
    assert has_concrete_statistic("Уровень безработицы составил 3,2%.")
    assert has_concrete_statistic("Индекс вырос до 120 пунктов.")
    assert has_concrete_statistic("Население составило 83 577 140 человек.")
