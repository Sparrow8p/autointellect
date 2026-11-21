"""Рыночные цены авто: корзины пробега, медиана по объявлениям, выбор цены для автозаполнения.

Чистая логика, без базы и сети.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from statistics import median
from typing import Protocol

BAND_SIZE = 50_000  # км; корзины пробега: 0–49 999, 50 000–99 999, ...
MAX_BAND = 250_000  # последняя корзина «250 000 км и больше»
MIN_SAMPLES = 3  # меньше объявлений в корзине — цена ненадёжна, не сохраняем
MAX_YEAR_GAP = 2  # насколько можно отличаться по году при автозаполнении


@dataclass(frozen=True)
class Listing:
    """Одно объявление о продаже."""

    price: int  # ₽
    mileage: int  # км
    year: int


@dataclass(frozen=True)
class Aggregate:
    year: int
    mileage_band: int  # нижняя граница корзины, км
    price: int  # медиана, ₽
    samples: int  # сколько объявлений


class PriceRow(Protocol):
    year: int
    mileage_band: int
    samples: int


def mileage_band(mileage: int) -> int:
    """Нижняя граница корзины пробега: 85 000 -> 50 000, 400 000 -> 250 000."""
    if mileage < 0:
        raise ValueError("mileage must not be negative")
    return min(mileage // BAND_SIZE * BAND_SIZE, MAX_BAND)


def aggregate(listings: Iterable[Listing], min_samples: int = MIN_SAMPLES) -> list[Aggregate]:
    """Медиана цены по каждой паре (год, корзина пробега). Медиана устойчива к выбросам."""
    groups: dict[tuple[int, int], list[int]] = defaultdict(list)
    for item in listings:
        groups[(item.year, mileage_band(item.mileage))].append(item.price)

    result = []
    for (year, band), prices in sorted(groups.items()):
        if len(prices) < min_samples:
            continue
        middle = Decimal(str(median(prices))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        result.append(Aggregate(year, band, int(middle), len(prices)))
    return result


def pick_price[R: PriceRow](rows: Sequence[R], year: int, mileage: int) -> tuple[R, bool] | None:
    """Строка для автозаполнения: та же корзина пробега и ближайший год (не дальше 2 лет).

    Возвращает (строка, точный_ли_год) или None, если подходящих данных нет.
    """
    band = mileage_band(mileage)
    candidates = [r for r in rows if r.mileage_band == band and abs(r.year - year) <= MAX_YEAR_GAP]
    if not candidates:
        return None
    best = min(candidates, key=lambda r: (abs(r.year - year), -r.samples))
    return best, best.year == year
