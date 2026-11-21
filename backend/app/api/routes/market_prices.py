from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import MarketPrice
from app.schemas.market_price import MarketPriceResponse
from app.services.market_prices import BAND_SIZE, MAX_BAND, pick_price

router = APIRouter(prefix="/market-prices", tags=["market-prices"])


@router.get("", response_model=MarketPriceResponse)
def market_price(
    _current_user: CurrentUser,
    db: DbSession,
    brand: Annotated[str, Query(min_length=1, max_length=100)],
    model: Annotated[str, Query(min_length=1, max_length=100)],
    year: Annotated[int, Query(ge=1950, le=date.today().year + 1)],
    mileage: Annotated[int, Query(ge=0, le=2_000_000)],
) -> MarketPriceResponse:
    """Рыночная цена для автозаполнения поля «цена авто».

    Берётся та же корзина пробега (по 50 000 км) и ближайший год выпуска, но не дальше 2 лет.
    Если данных нет — 404, поле на фронте просто остаётся пустым.
    """
    rows = db.scalars(
        select(MarketPrice).where(MarketPrice.brand == brand, MarketPrice.model == model)
    ).all()
    picked = pick_price(rows, year, mileage)
    if picked is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No market price for this car"
        )
    row, exact_year = picked
    return MarketPriceResponse(
        price=int(row.price),
        samples=row.samples,
        year=row.year,
        exact_year=exact_year,
        mileage_from=row.mileage_band,
        mileage_to=None if row.mileage_band >= MAX_BAND else row.mileage_band + BAND_SIZE - 1,
        source=row.source,
        collected_at=row.collected_at,
    )
