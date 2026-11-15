from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Work(Base):
    """Работа из базы нормо-часов."""

    __tablename__ = "works"
    __table_args__ = (
        CheckConstraint("hours >= 0", name="hours_non_negative"),
        CheckConstraint("part_price >= 0", name="part_price_non_negative"),
    )

    # id задаётся явно: он совпадает с ID в исходной таблице нормо-часов.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    hours: Mapped[Decimal] = mapped_column(Numeric(5, 2))  # нормо-часы
    part_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # средняя цена запчасти, ₽
    category: Mapped[str] = mapped_column(String(50), index=True)


class WorkKeyword(Base):
    """Ключевое слово из описания проблемы -> работа или целая категория работ.

    keyword — основа слова в нижнем регистре, без «ё» (например, «подвеск»);
    несколько слов через пробел означают «все эти слова есть в тексте».
    Ровно одно из полей work_id / category должно быть заполнено.
    """

    __tablename__ = "work_keywords"
    __table_args__ = (
        CheckConstraint("(work_id IS NULL) <> (category IS NULL)", name="one_target"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(100), index=True)
    work_id: Mapped[int | None] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"))
    category: Mapped[str | None] = mapped_column(String(50))
