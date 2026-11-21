from dataclasses import dataclass

import pytest

from app.services.market_prices import Aggregate, Listing, aggregate, mileage_band, pick_price


def test_mileage_band_boundaries():
    assert mileage_band(0) == 0
    assert mileage_band(49_999) == 0
    assert mileage_band(50_000) == 50_000
    assert mileage_band(85_000) == 50_000
    assert mileage_band(249_999) == 200_000
    assert mileage_band(250_000) == 250_000
    assert mileage_band(900_000) == 250_000  # последняя корзина «и больше»


def test_negative_mileage_is_rejected():
    with pytest.raises(ValueError):
        mileage_band(-1)


def test_aggregate_takes_median_per_year_and_band():
    listings = [
        Listing(price=1_000_000, mileage=60_000, year=2018),
        Listing(price=1_200_000, mileage=70_000, year=2018),
        Listing(price=5_000_000, mileage=80_000, year=2018),  # выброс не тянет медиану вверх
        Listing(price=900_000, mileage=120_000, year=2018),
        Listing(price=950_000, mileage=130_000, year=2018),
        Listing(price=970_000, mileage=140_000, year=2018),
    ]
    assert aggregate(listings) == [
        Aggregate(year=2018, mileage_band=50_000, price=1_200_000, samples=3),
        Aggregate(year=2018, mileage_band=100_000, price=950_000, samples=3),
    ]


def test_aggregate_drops_groups_with_too_few_samples():
    listings = [Listing(1_000_000, 60_000, 2018), Listing(1_100_000, 65_000, 2018)]
    assert aggregate(listings) == []
    assert len(aggregate(listings, min_samples=2)) == 1


def test_aggregate_rounds_even_count_median_half_up():
    listings = [Listing(p, 10_000, 2020) for p in (100, 101, 102, 103)]  # медиана 101,5
    assert aggregate(listings)[0].price == 102


def test_aggregate_separates_years():
    listings = [Listing(100, 10_000, y) for y in (2019, 2019, 2019, 2020, 2020, 2020)]
    assert [a.year for a in aggregate(listings)] == [2019, 2020]


@dataclass(frozen=True)
class Row:
    year: int
    mileage_band: int
    samples: int = 10


def test_pick_price_exact_match():
    rows = [Row(2018, 50_000), Row(2017, 50_000)]
    assert pick_price(rows, 2018, 85_000) == (rows[0], True)


def test_pick_price_uses_nearest_year_up_to_two_years():
    rows = [Row(2016, 50_000)]
    assert pick_price(rows, 2018, 85_000) == (rows[0], False)
    assert pick_price(rows, 2019, 85_000) is None  # три года разницы — слишком далеко


def test_pick_price_requires_same_mileage_band():
    assert pick_price([Row(2018, 100_000)], 2018, 85_000) is None


def test_pick_price_prefers_more_samples_at_same_distance():
    few, many = Row(2017, 50_000, samples=3), Row(2019, 50_000, samples=30)
    assert pick_price([few, many], 2018, 60_000) == (many, False)


def test_pick_price_without_rows():
    assert pick_price([], 2018, 85_000) is None
