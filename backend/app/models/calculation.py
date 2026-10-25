from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Деньги храним как NUMERIC, а не float: никаких ошибок округления в сметах.
Money = Numeric(12, 2)


class Calculation(Base):
    __tablename__ = "calculations"
    __table_args__ = (
        CheckConstraint("repair_min >= 0 AND repair_max >= repair_min", name="repair_range"),
        CheckConstraint("price_as_is >= 0 AND price_after_repair >= 0", name="prices_non_negative"),
        # История расчётов пользователя: «последние N по дате».
        Index("ix_calculations_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"), index=True)
    # Может быть пустым: по ТЗ пользователь вправе загрузить только фото.
    problem_text: Mapped[str | None] = mapped_column(Text)
    repair_min: Mapped[Decimal] = mapped_column(Money)
    repair_max: Mapped[Decimal] = mapped_column(Money)
    price_as_is: Mapped[Decimal] = mapped_column(Money)
    price_after_repair: Mapped[Decimal] = mapped_column(Money)
    recommendation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
