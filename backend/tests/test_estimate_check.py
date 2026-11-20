import pytest

from app.services.estimate_check import check_amount


def test_amount_inside_range():
    result = check_amount(15_000, 13_900, 18_500)
    assert (result.code, result.text, result.difference) == ("in_range", "В диапазоне", 0)


def test_range_borders_are_inside():
    assert check_amount(13_900, 13_900, 18_500).code == "in_range"
    assert check_amount(18_500, 13_900, 18_500).code == "in_range"


def test_amount_above_range_is_overpriced():
    result = check_amount(20_000, 13_900, 18_500)
    assert (result.code, result.text, result.difference) == ("overpriced", "Завышено", 1_500)


def test_amount_below_range_is_underpriced():
    result = check_amount(10_000, 13_900, 18_500)
    assert (result.code, result.text, result.difference) == ("underpriced", "Занижено", -3_900)


def test_one_ruble_outside_is_not_in_range():
    assert check_amount(18_501, 13_900, 18_500).code == "overpriced"
    assert check_amount(13_899, 13_900, 18_500).code == "underpriced"


def test_broken_range_is_rejected():
    with pytest.raises(ValueError):
        check_amount(1_000, 2_000, 1_000)
