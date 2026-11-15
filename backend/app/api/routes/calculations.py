from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, get_user_car
from app.core.config import get_settings
from app.schemas.estimate import EstimateRequest, EstimateResponse, EstimateWork
from app.schemas.scenarios import (
    PriceAfterRepairRequest,
    PriceAfterRepairResponse,
    RepairAndKeep,
    RepairAndSell,
    RepairRange,
    ScenariosBlock,
    ScenariosRequest,
    ScenariosResponse,
    SellAsIs,
)
from app.services.calculation import calculate
from app.services.estimate import WorkLine, estimate_repair
from app.services.scenarios import price_after_repair

router = APIRouter(prefix="/calculations", tags=["calculations"])


def _works(lines: list[WorkLine]) -> list[EstimateWork]:
    return [
        EstimateWork(
            id=line.work.id,
            name=line.work.name,
            category=line.work.category,
            hours=float(line.work.hours),
            min_price=line.min_price,
            max_price=line.max_price,
        )
        for line in lines
    ]


@router.post("/estimate", response_model=EstimateResponse)
def estimate(
    payload: EstimateRequest, current_user: CurrentUser, db: DbSession
) -> EstimateResponse:
    """Диапазон стоимости ремонта по описанию проблемы. Ничего не сохраняет."""
    car = get_user_car(db, current_user, payload.car_id)
    result = estimate_repair(
        db,
        region_name=car.region,
        problem_text=payload.problem_text,
        hourly_rate=get_settings().labor_rate_per_hour,
    )
    return EstimateResponse(
        recognized=result.recognized,
        min_price=result.min_price,
        max_price=result.max_price,
        region_coefficient=float(result.region_coefficient),
        matched_keywords=result.keywords,
        works=_works(result.lines),
    )


@router.post("/price-after-repair", response_model=PriceAfterRepairResponse)
def price_after_repair_endpoint(
    payload: PriceAfterRepairRequest, _current_user: CurrentUser
) -> PriceAfterRepairResponse:
    """Цена авто после ремонта по текущей цене и стоимости ремонта (формула без базы)."""
    growth, price_after = price_after_repair(payload.car_price, payload.repair_cost)
    return PriceAfterRepairResponse(
        car_price=payload.car_price,
        repair_cost=payload.repair_cost,
        repair_share_percent=round(payload.repair_cost / payload.car_price * 100, 2),
        price_growth_percent=round(float(growth * 100), 2),
        price_growth=price_after - payload.car_price,
        price_after_repair=price_after,
    )


@router.post("/scenarios", response_model=ScenariosResponse)
def scenarios(
    payload: ScenariosRequest, current_user: CurrentUser, db: DbSession
) -> ScenariosResponse:
    """Три сценария (продать как есть / ремонт и продажа / ремонт и эксплуатация)
    и рекомендация. Ничего не сохраняет — для сохранения есть POST /api/history/save."""
    car = get_user_car(db, current_user, payload.car_id)
    result = calculate(
        db,
        car,
        problem_text=payload.problem_text,
        car_price=payload.car_price,
        years=payload.years,
    )
    est, sc = result.estimate, result.scenarios
    return ScenariosResponse(
        recognized=est.recognized,
        matched_keywords=est.keywords,
        region_coefficient=float(est.region_coefficient),
        works=_works(est.lines),
        repair=RepairRange(
            min_price=est.min_price, max_price=est.max_price, repair_cost=sc.repair_cost
        ),
        scenarios=ScenariosBlock(
            sell_as_is=SellAsIs(value=sc.sell_as_is, recommended=not sc.repair_recommended),
            repair_and_sell=RepairAndSell(
                repair_cost=sc.repair_cost,
                price_after_repair=sc.price_after_repair,
                price_growth_percent=round(float(sc.growth * 100), 2),
                value=sc.repair_and_sell,
                recommended=sc.repair_recommended,
            ),
            repair_and_keep=RepairAndKeep(
                repair_cost=sc.repair_cost,
                running_costs=sc.running_costs,
                years=sc.years,
                value=sc.repair_and_keep,
            ),
        ),
        profit=sc.profit,
        recommendation=sc.recommendation,
    )
