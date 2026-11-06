from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models import Brand, CarModel, Region
from app.schemas.reference import BrandRead, CarModelRead, RegionRead

# Справочники открыты без токена: они нужны для выпадающих списков на фронтенде.
router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/brands", response_model=list[BrandRead])
def list_brands(db: DbSession) -> list[Brand]:
    return list(db.scalars(select(Brand).order_by(Brand.name)))


@router.get("/models", response_model=list[CarModelRead])
def list_models(
    db: DbSession,
    brand: str | None = Query(default=None, description="Название марки; без него — все модели"),
) -> list[CarModelRead]:
    query = select(CarModel, Brand.name).join(Brand, CarModel.brand_id == Brand.id)
    if brand is not None:
        if db.scalar(select(Brand.id).where(Brand.name == brand)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        query = query.where(Brand.name == brand)
    rows = db.execute(query.order_by(Brand.name, CarModel.name))
    return [
        CarModelRead(id=model.id, name=model.name, brand=brand_name) for model, brand_name in rows
    ]


@router.get("/regions", response_model=list[RegionRead])
def list_regions(db: DbSession) -> list[Region]:
    return list(db.scalars(select(Region).order_by(Region.name)))
