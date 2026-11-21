from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession
from app.models import Part
from app.schemas.part import PartRead, PartSearchResponse, VinResult
from app.services.parts import MAX_PRICE, normalize_oem, normalize_text, parse_vin

router = APIRouter(prefix="/parts", tags=["parts"])


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


@router.get("", response_model=PartSearchResponse)
def search_parts(
    _current_user: CurrentUser,
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100, description="Часть названия")] = None,
    oem: Annotated[str | None, Query(max_length=50, description="Номер детали (OEM)")] = None,
    vin: Annotated[str | None, Query(max_length=17, description="VIN: подставит марку")] = None,
    min_price: Annotated[int | None, Query(ge=0, le=MAX_PRICE)] = None,
    max_price: Annotated[int | None, Query(ge=0, le=MAX_PRICE)] = None,
    condition: Literal["new", "used"] | None = None,
    region: Annotated[str | None, Query(max_length=100)] = None,
    sort: Literal["price_asc", "price_desc"] = "price_asc",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PartSearchResponse:
    """Поиск запчастей по названию, номеру (OEM) и VIN с фильтрами по цене, состоянию и региону.

    Все условия объединяются через «и». VIN определяет только марку (по его началу) и оставляет
    детали этой марки и универсальные; подбор по конкретной модификации требует платного каталога.
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise _unprocessable("min_price must not exceed max_price")

    conditions = []
    vin_result = None
    if vin is not None:
        try:
            info = parse_vin(vin)
        except ValueError as error:
            raise _unprocessable(str(error)) from error
        vin_result = VinResult(vin=info.vin, brand=info.brand)
        if info.brand is not None:
            conditions.append(or_(Part.brand == info.brand, Part.brand.is_(None)))
    if oem is not None:
        normalized_oem = normalize_oem(oem)
        if not normalized_oem:
            raise _unprocessable("oem must contain letters or digits")
        conditions.append(Part.oem == normalized_oem)
    if q is not None and normalize_text(q):
        conditions.append(Part.name_lower.contains(normalize_text(q), autoescape=True))
    if min_price is not None:
        conditions.append(Part.price >= min_price)
    if max_price is not None:
        conditions.append(Part.price <= max_price)
    if condition is not None:
        conditions.append(Part.condition == condition)
    if region is not None:
        conditions.append(Part.region == region)

    total = db.scalar(select(func.count()).select_from(Part).where(*conditions)) or 0
    order = Part.price.asc() if sort == "price_asc" else Part.price.desc()
    parts = db.scalars(
        select(Part).where(*conditions).order_by(order, Part.id).limit(limit).offset(offset)
    )
    return PartSearchResponse(
        total=total,
        items=[
            PartRead(
                id=part.id,
                brand=part.brand,
                name=part.name,
                oem=part.oem,
                manufacturer=part.manufacturer,
                price=int(part.price),
                condition=part.condition,
                region=part.region,
                shop=part.shop,
                url=part.url,
                collected_at=part.collected_at,
            )
            for part in parts
        ],
        vin=vin_result,
    )
