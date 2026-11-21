from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Part(Base):
    """Предложение запчасти из магазина: что за деталь, сколько стоит, где и в каком состоянии."""

    __tablename__ = "parts"
    __table_args__ = (
        # Одно предложение магазина (по ссылке или по ключу из CSV) хранится один раз.
        UniqueConstraint("shop", "offer_key"),
        CheckConstraint("price > 0", name="price_positive"),
        CheckConstraint("condition IN ('new', 'used')", name="condition_valid"),
        Index("ix_parts_oem", "oem"),
        Index("ix_parts_brand", "brand"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Марка авто, к которой подходит деталь; пусто: марка не указана или подходит нескольким.
    brand: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(300))
    # Название в нижнем регистре: поиск без учёта регистра одинаково работает и для кириллицы.
    name_lower: Mapped[str] = mapped_column(String(300))
    # Номер детали: только латиница и цифры, заглавными.
    oem: Mapped[str] = mapped_column(String(50))
    manufacturer: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # ₽
    condition: Mapped[str] = mapped_column(String(10))  # new / used
    region: Mapped[str | None] = mapped_column(String(100))  # регион магазина или склада
    shop: Mapped[str] = mapped_column(String(50))
    offer_key: Mapped[str] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(1000))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
