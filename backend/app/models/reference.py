from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Region(Base):
    __tablename__ = "regions"
    __table_args__ = (CheckConstraint("coefficient > 0", name="coefficient_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    # Множитель стоимости работ в регионе (1.0 — базовая цена).
    coefficient: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.0"))


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class CarModel(Base):
    __tablename__ = "car_models"
    __table_args__ = (UniqueConstraint("brand_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
