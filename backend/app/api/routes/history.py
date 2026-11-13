from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_user_car
from app.models import Calculation, Car
from app.schemas.history import HistoryCar, HistoryItem
from app.schemas.scenarios import SaveCalculationRequest
from app.services.calculation import calculate

router = APIRouter(prefix="/history", tags=["history"])


def _to_item(calc: Calculation, car: Car) -> HistoryItem:
    return HistoryItem(
        id=calc.id,
        created_at=calc.created_at,
        car=HistoryCar(id=car.id, brand=car.brand, model=car.model, year=car.year),
        problem_text=calc.problem_text,
        repair_min=int(calc.repair_min),
        repair_max=int(calc.repair_max),
        price_as_is=int(calc.price_as_is),
        price_after_repair=int(calc.price_after_repair),
        recommendation=calc.recommendation,
    )


@router.get("", response_model=list[HistoryItem])
def list_history(
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[HistoryItem]:
    """Сохранённые расчёты текущего пользователя, новые сверху."""
    query = (
        select(Calculation, Car)
        .join(Car, Calculation.car_id == Car.id)
        .where(Calculation.user_id == current_user.id)
        .order_by(Calculation.created_at.desc(), Calculation.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_to_item(calc, car) for calc, car in db.execute(query)]


@router.post("/save", response_model=HistoryItem, status_code=status.HTTP_201_CREATED)
def save_calculation(
    payload: SaveCalculationRequest, current_user: CurrentUser, db: DbSession
) -> HistoryItem:
    """Пересчитывает расчёт на сервере и сохраняет его в историю.

    Принимает только исходные данные (авто, текст проблемы, цена), а не готовые суммы:
    клиент не может сохранить произвольные числа.
    """
    car = get_user_car(db, current_user, payload.car_id)
    result = calculate(db, car, problem_text=payload.problem_text, car_price=payload.car_price)
    calc = Calculation(
        user_id=current_user.id,
        car_id=car.id,
        problem_text=payload.problem_text,
        repair_min=Decimal(result.estimate.min_price),
        repair_max=Decimal(result.estimate.max_price),
        price_as_is=Decimal(payload.car_price),
        price_after_repair=Decimal(result.scenarios.price_after_repair),
        recommendation=result.scenarios.recommendation,
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)  # подтягивает created_at, выставленный базой
    return _to_item(calc, car)
