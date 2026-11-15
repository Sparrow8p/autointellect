from decimal import Decimal

import pytest

from app.services.scenarios import (
    build_scenarios,
    format_rubles,
    middle_repair_cost,
    price_after_repair,
    price_growth,
    recommendation_text,
)


def test_example_from_project_document():
    # авто 400 000 ₽, ремонт 50 000 ₽ -> после ремонта 470 000 ₽, выгода 20 000 ₽
    s = build_scenarios(400_000, 50_000)
    assert s.price_after_repair == 470_000
    assert s.sell_as_is == 400_000
    assert s.repair_and_sell == 420_000
    assert s.profit == 20_000
    assert s.repair_recommended is True
    assert s.recommendation == "Ремонт окупится. Выгода: 20 000 ₽"


def test_price_after_repair_standalone():
    assert price_after_repair(400_000, 50_000) == (Decimal("0.175"), 470_000)
    assert price_after_repair(1_000_000, 400_000) == (Decimal("0.0975"), 1_097_500)
    assert price_after_repair(100_000, 80_000) == (Decimal("0.02"), 102_000)


def test_price_after_repair_matches_scenarios():
    _, price = price_after_repair(250_000, 60_000)
    assert build_scenarios(250_000, 60_000).price_after_repair == price


def test_repair_recommended_flag_follows_profit():
    assert build_scenarios(400_000, 50_000).repair_recommended is True
    assert build_scenarios(1_000_000, 250_000).repair_recommended is False
    # нулевая выгода — не рекомендуем ремонт
    assert build_scenarios(1_000_000, 175_000).profit == 0
    assert build_scenarios(1_000_000, 175_000).repair_recommended is False


def test_cheap_repair_gives_full_growth():
    assert price_growth(1, 100_000) == Decimal("0.175")
    assert price_growth(30_000, 100_000) == Decimal("0.175")  # граница 30%


def test_expensive_repair_gives_almost_no_growth():
    assert price_growth(50_000, 100_000) == Decimal("0.02")  # граница 50%
    assert price_growth(90_000, 100_000) == Decimal("0.02")


def test_growth_declines_linearly_between_30_and_50_percent():
    assert price_growth(40_000, 100_000) == Decimal("0.0975")  # ровно посередине
    previous = Decimal("0.175")
    for repair in range(31_000, 50_000, 1_000):
        growth = price_growth(repair, 100_000)
        assert Decimal("0.02") < growth < previous  # строго убывает, без скачков
        previous = growth


def test_repair_that_costs_more_than_it_adds_is_not_recommended():
    # 25% цены: рост 17,5% меньше стоимости ремонта -> не окупится
    s = build_scenarios(1_000_000, 250_000)
    assert s.price_after_repair == 1_175_000
    assert s.repair_and_sell == 925_000
    assert s.profit == -75_000
    assert s.recommendation == "Выгоднее продать как есть"


def test_zero_profit_is_not_worth_it():
    assert recommendation_text(0) == "Выгоднее продать как есть"
    assert recommendation_text(1) == "Ремонт окупится. Выгода: 1 ₽"


def test_scenario_3_is_repair_plus_running_costs_as_negative():
    # расходы 8% цены в год: 400 000 × 0.08 × 2 года = 64 000
    s = build_scenarios(400_000, 50_000, years=2, running_costs_rate=Decimal("0.08"))
    assert s.running_costs == 64_000
    assert s.repair_and_keep == -(50_000 + 64_000)
    assert s.years == 2


def test_default_is_one_year_at_8_percent():
    s = build_scenarios(400_000, 50_000)
    assert (s.years, s.running_costs) == (1, 32_000)


def test_very_expensive_repair_is_a_clear_loss():
    s = build_scenarios(100_000, 80_000)
    assert s.price_after_repair == 102_000
    assert s.profit == 102_000 - 80_000 - 100_000
    assert s.recommendation == "Выгоднее продать как есть"


def test_middle_repair_cost():
    assert middle_repair_cost(13_900, 18_500) == 16_200
    assert middle_repair_cost(1, 2) == 2  # половинки округляются вверх


def test_format_rubles():
    assert format_rubles(20_000) == "20 000"
    assert format_rubles(1_234_567) == "1 234 567"
    assert format_rubles(950) == "950"


def test_price_must_be_positive():
    with pytest.raises(ValueError):
        build_scenarios(0, 1000)
