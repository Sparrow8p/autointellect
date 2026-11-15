from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_user_car
from app.models import Car, Region
from app.schemas.car import CarCreate, CarRead

router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("", response_model=list[CarRead])
def list_cars(current_user: CurrentUser, db: DbSession) -> list[Car]:
    query = select(Car).where(Car.user_id == current_user.id).order_by(Car.id)
    return list(db.scalars(query))


@router.post("", response_model=CarRead, status_code=status.HTTP_201_CREATED)
def create_car(payload: CarCreate, current_user: CurrentUser, db: DbSession) -> Car:
    # Регион нужен для расчёта (у каждого свой коэффициент), поэтому только из справочника.
    if db.scalar(select(Region.id).where(Region.name == payload.region)) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unknown region: choose one from GET /api/reference/regions",
        )
    car = Car(user_id=current_user.id, **payload.model_dump())
    db.add(car)
    db.commit()
    db.refresh(car)
    return car


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(car_id: int, current_user: CurrentUser, db: DbSession) -> None:
    car = get_user_car(db, current_user, car_id)
    db.delete(car)
    db.commit()
