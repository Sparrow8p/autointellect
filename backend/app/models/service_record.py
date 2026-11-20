from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

Money = Numeric(12, 2)


class ServiceRecord(Base):
    """Одно обращение в СТО: дата, пробег, список работ (строки чека) и файл чека."""

    __tablename__ = "service_records"
    __table_args__ = (
        CheckConstraint("mileage IS NULL OR mileage >= 0", name="mileage_non_negative"),
        # Журнал авто: «по дате».
        Index("ix_service_records_car_id_service_date", "car_id", "service_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"))
    service_date: Mapped[date] = mapped_column(Date)
    mileage: Mapped[int | None] = mapped_column(Integer)  # км на момент обслуживания
    sto_name: Mapped[str | None] = mapped_column(String(200))
    note: Mapped[str | None] = mapped_column(Text)
    # Имя файла чека на диске (случайное, не исходное) и его тип; пусто, если чека нет.
    receipt_file: Mapped[str | None] = mapped_column(String(100))
    receipt_type: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    works: Mapped[list["ServiceWork"]] = relationship(
        back_populates="record", cascade="all, delete-orphan", order_by="ServiceWork.id"
    )


class ServiceWork(Base):
    """Строка чека: название работы или детали и её цена."""

    __tablename__ = "service_works"
    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("service_records.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Money)

    record: Mapped[ServiceRecord] = relationship(back_populates="works")
