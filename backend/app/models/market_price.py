from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketPrice(Base):
    """Средняя (медианная) цена авто на рынке: марка, модель, год, корзина пробега."""

    __tablename__ = "market_prices"
    __table_args__ = (
        UniqueConstraint("brand", "model", "year", "mileage_band", "source"),
        CheckConstraint("price > 0", name="price_positive"),
        CheckConstraint("samples > 0", name="samples_positive"),
        Index("ix_market_prices_brand_model", "brand", "model"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Названия — как в справочнике марок и моделей (brands / car_models), чтобы совпадали с cars.
    brand: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int]
    mileage_band: Mapped[int]  # нижняя граница корзины пробега, км (0, 50000, ... 250000)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # медиана, ₽
    samples: Mapped[int]  # сколько объявлений учтено
    source: Mapped[str] = mapped_column(String(50))  # drom / manual
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
