"""Запись рыночных цен в базу: обновляет существующую строку или добавляет новую."""

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MarketPrice
from app.services.market_prices import Aggregate


def upsert_prices(
    db: Session, brand: str, model: str, rows: Iterable[Aggregate], source: str
) -> int:
    """Сохраняет строки (год, корзина, медиана, число объявлений); возвращает их количество."""
    count = 0
    for row in rows:
        existing = db.scalar(
            select(MarketPrice).where(
                MarketPrice.brand == brand,
                MarketPrice.model == model,
                MarketPrice.year == row.year,
                MarketPrice.mileage_band == row.mileage_band,
                MarketPrice.source == source,
            )
        )
        if existing is None:
            db.add(
                MarketPrice(
                    brand=brand,
                    model=model,
                    year=row.year,
                    mileage_band=row.mileage_band,
                    price=Decimal(row.price),
                    samples=row.samples,
                    source=source,
                )
            )
        else:
            existing.price = Decimal(row.price)
            existing.samples = row.samples
            existing.collected_at = datetime.now(UTC)
        count += 1
    db.commit()
    return count
