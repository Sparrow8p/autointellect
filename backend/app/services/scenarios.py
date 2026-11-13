"""Цена после ремонта, три сценария и рекомендация. Чистые функции без БД.

Цена после ремонта = цена авто × (1 + рост), где рост зависит от доли ремонта в цене:

    ремонт ≤ 30% цены   -> рост 17,5%   (середина вилки 15–20%)
    ремонт ≥ 50% цены   -> рост 2%      («почти не растёт»)
    между 30% и 50%     -> линейный спад от 17,5% до 2% (без скачка)

Пример из проектного документа: авто 400 000 ₽, ремонт 50 000 ₽ -> после ремонта
470 000 ₽ (+17,5%), выгода 20 000 ₽.

Сценарии (целые рубли):
    1. Продажа как есть          = цена авто
    2. Ремонт -> продажа         = цена после ремонта − стоимость ремонта
    3. Ремонт -> эксплуатация    = −(стоимость ремонта + расходы на владение за период)
       Это затраты, а не сумма продажи, поэтому с сценарием 1 он не сравнивается.

Рекомендация: «Ремонт окупится…», если сценарий 2 больше сценария 1, иначе «Выгоднее продать».
"""

from dataclasses import dataclass
from decimal import Decimal

from app.services.pricing import to_rubles

CHEAP_REPAIR_LIMIT = Decimal("0.30")  # ремонт до 30% цены авто
EXPENSIVE_REPAIR_LIMIT = Decimal("0.50")  # ремонт от 50% цены авто
MAX_GROWTH = Decimal("0.175")  # рост цены при дешёвом ремонте
MIN_GROWTH = Decimal("0.02")  # рост цены при дорогом ремонте

SELL_AS_IS_TEXT = "Выгоднее продать как есть"


@dataclass(frozen=True)
class Scenarios:
    car_price: int
    repair_cost: int  # стоимость ремонта, принятая в расчёт
    growth: Decimal  # доля роста цены (0.175 = +17,5%)
    price_after_repair: int
    sell_as_is: int  # сценарий 1
    repair_and_sell: int  # сценарий 2
    years: int
    running_costs: int  # расходы на владение за весь период
    repair_and_keep: int  # сценарий 3 (отрицательное число — затраты)
    profit: int  # сценарий 2 − сценарий 1
    repair_recommended: bool  # True — рекомендуется сценарий 2, False — сценарий 1
    recommendation: str


def middle_repair_cost(min_price: int, max_price: int) -> int:
    """Середина диапазона стоимости ремонта (между б/у и новыми запчастями)."""
    return to_rubles((Decimal(min_price) + Decimal(max_price)) / 2)


def price_growth(repair_cost: int, car_price: int) -> Decimal:
    ratio = Decimal(repair_cost) / Decimal(car_price)
    if ratio <= CHEAP_REPAIR_LIMIT:
        return MAX_GROWTH
    if ratio >= EXPENSIVE_REPAIR_LIMIT:
        return MIN_GROWTH
    share = (ratio - CHEAP_REPAIR_LIMIT) / (EXPENSIVE_REPAIR_LIMIT - CHEAP_REPAIR_LIMIT)
    return MAX_GROWTH - (MAX_GROWTH - MIN_GROWTH) * share


def price_after_repair(car_price: int, repair_cost: int) -> tuple[Decimal, int]:
    """Цена авто после ремонта. Возвращает (рост в долях, цена в целых рублях)."""
    if car_price <= 0:
        raise ValueError("car_price must be positive")
    growth = price_growth(repair_cost, car_price)
    return growth, to_rubles(Decimal(car_price) * (1 + growth))


def format_rubles(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def recommendation_text(profit: int) -> str:
    if profit > 0:
        return f"Ремонт окупится. Выгода: {format_rubles(profit)} ₽"
    return SELL_AS_IS_TEXT


def build_scenarios(
    car_price: int,
    repair_cost: int,
    *,
    years: int = 1,
    running_costs_rate: Decimal = Decimal("0.08"),
) -> Scenarios:
    """car_price и repair_cost — целые рубли; running_costs_rate — доля цены авто в год."""
    growth, price_after = price_after_repair(car_price, repair_cost)
    running_costs = to_rubles(Decimal(car_price) * running_costs_rate * years)

    sell_as_is = car_price
    repair_and_sell = price_after - repair_cost
    profit = repair_and_sell - sell_as_is
    return Scenarios(
        car_price=car_price,
        repair_cost=repair_cost,
        growth=growth,
        price_after_repair=price_after,
        sell_as_is=sell_as_is,
        repair_and_sell=repair_and_sell,
        years=years,
        running_costs=running_costs,
        repair_and_keep=-(repair_cost + running_costs),
        profit=profit,
        repair_recommended=profit > 0,
        recommendation=recommendation_text(profit),
    )
