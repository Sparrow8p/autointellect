from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Email хранится в нижнем регистре (нормализуется в схеме), уникален.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Необязателен: регистрация идёт по email, телефон можно добавить позже.
    # UNIQUE в PostgreSQL допускает несколько NULL.
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
