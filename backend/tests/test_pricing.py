from decimal import Decimal

from app.services.pricing import to_rubles, work_price_range


def test_range_uses_used_and_new_parts():
    # работа 0.5 ч × 2000 × 1.3 = 1300; запчасть 3000: б/у 60% = 1800, новая 100% = 3000
    assert work_price_range(0.5, 3000, 2000, 1.3) == (3100, 4300)


def test_region_coefficient_does_not_change_parts_price():
    base_min, base_max = work_price_range(1, 4000, 2000, 1.0)
    msk_min, msk_max = work_price_range(1, 4000, 2000, 1.3)
    assert (msk_min - base_min, msk_max - base_max) == (600, 600)  # только работа: 2000 × 0.3


def test_work_without_parts_has_equal_min_and_max():
    assert work_price_range(1, 0, 2000, 1.0) == (2000, 2000)


def test_float_hours_are_not_distorted():
    # 0.1 + 0.2 как float неточны; считаем через Decimal
    assert work_price_range(0.3, 0, 1000, 1) == (300, 300)


def test_rounding_is_half_up_not_bankers():
    assert to_rubles(Decimal("0.5")) == 1
    assert to_rubles(Decimal("1.5")) == 2
    assert to_rubles(Decimal("2.5")) == 3
    assert to_rubles(Decimal("2.4")) == 2


def test_accepts_decimals_from_database():
    result = work_price_range(Decimal("1.50"), Decimal("6000.00"), 2000, Decimal("1.30"))
    # работа 1.5 × 2000 × 1.3 = 3900; б/у 3600, новая 6000
    assert result == (7500, 9900)
