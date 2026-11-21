from datetime import datetime

from pydantic import BaseModel


class MarketPriceResponse(BaseModel):
    price: int  # ₽, подсказка для поля «цена авто»
    samples: int  # на скольких объявлениях основана цена
    year: int  # год, по которому найдена цена (может отличаться от запрошенного)
    exact_year: bool  # False — взят ближайший год, цена приблизительная
    mileage_from: int  # корзина пробега, км
    mileage_to: int | None  # None — «и больше»
    source: str
    collected_at: datetime
