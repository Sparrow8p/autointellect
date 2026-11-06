from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models import Car
from app.schemas.estimate import EstimateRequest, EstimateResponse, EstimateWork
from app.services.estimate import estimate_repair

router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("/estimate", response_model=EstimateResponse)
def estimate(
    payload: EstimateRequest, current_user: CurrentUser, db: DbSession
) -> EstimateResponse:
    """Диапазон стоимости ремонта по описанию проблемы. Ничего не сохраняет."""
    car = db.scalar(select(Car).where(Car.id == payload.car_id, Car.user_id == current_user.id))
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")

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
        works=[
            EstimateWork(
                id=line.work.id,
                name=line.work.name,
                category=line.work.category,
                hours=float(line.work.hours),
                min_price=line.min_price,
                max_price=line.max_price,
            )
            for line in result.lines
        ],
    )
