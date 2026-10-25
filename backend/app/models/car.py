from sqlalchemy import CheckConstraint, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Car(Base):
    __tablename__ = "cars"
    __table_args__ = (
        CheckConstraint("year >= 1900", name="year_min"),
        CheckConstraint("mileage >= 0", name="mileage_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    brand: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(SmallInteger)
    mileage: Mapped[int] = mapped_column(Integer)  # км
    region: Mapped[str] = mapped_column(String(100))
