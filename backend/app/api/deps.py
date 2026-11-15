from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Car, User

# auto_error=False: отсутствие заголовка обрабатываем сами и всегда отдаём 401.
# Схема HTTPBearer даёт кнопку Authorize в Swagger (/docs).
bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_user_car(db: Session, user: User, car_id: int) -> Car:
    """Авто пользователя или 404. Чужое авто неотличимо от несуществующего."""
    car = db.scalar(select(Car).where(Car.id == car_id, Car.user_id == user.id))
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    return car
