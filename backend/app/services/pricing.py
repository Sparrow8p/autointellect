"""Стоимость одной работы. Чистые функции без БД.

    работа  = часы × ставка нормо-часа × коэффициент региона
    min     = работа + цена запчасти × 0.6   (б/у или аналог)
    max     = работа + цена запчасти × 1.0   (новая оригинальная)

Запчасти региональный коэффициент не умножает. Результат — целые рубли.
"""

from decimal import ROUND_HALF_UP, Decimal

USED_PARTS_FACTOR = Decimal("0.6")
NEW_PARTS_FACTOR = Decimal("1.0")


def _dec(value: object) -> Decimal:
    # Через str: float 0.1 не превращается в 0.1000000000000000055...
    return value if isinstance(value, Decimal) else Decimal(str(value))


def to_rubles(value: Decimal) -> int:
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def work_price_range(
    hours: object,
    part_price: object,
    hourly_rate: object,
    region_coefficient: object,
) -> tuple[int, int]:
    labor = _dec(hours) * _dec(hourly_rate) * _dec(region_coefficient)
    parts = _dec(part_price)
    return (
        to_rubles(labor + parts * USED_PARTS_FACTOR),
        to_rubles(labor + parts * NEW_PARTS_FACTOR),
    )
