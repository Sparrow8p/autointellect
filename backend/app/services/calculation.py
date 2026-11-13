from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Car
from app.services.estimate import Estimate, estimate_repair
from app.services.scenarios import Scenarios, build_scenarios, middle_repair_cost


@dataclass
class FullCalculation:
    estimate: Estimate  # диапазон ремонта и список работ
    scenarios: Scenarios  # цена после ремонта, 3 сценария, рекомендация


def calculate(
    db: Session, car: Car, *, problem_text: str, car_price: int, years: int = 1
) -> FullCalculation:
    """Полный расчёт: стоимость ремонта по тексту -> цена после ремонта -> сценарии.

    В сценариях берётся середина диапазона стоимости ремонта (между б/у и новыми запчастями).
    """
    settings = get_settings()
    estimate = estimate_repair(
        db,
        region_name=car.region,
        problem_text=problem_text,
        hourly_rate=settings.labor_rate_per_hour,
    )
    scenarios = build_scenarios(
        car_price,
        middle_repair_cost(estimate.min_price, estimate.max_price),
        years=years,
        running_costs_rate=Decimal(str(settings.annual_running_costs_rate)),
    )
    return FullCalculation(estimate=estimate, scenarios=scenarios)
