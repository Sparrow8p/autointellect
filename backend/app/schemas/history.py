from datetime import datetime

from pydantic import BaseModel


class HistoryCar(BaseModel):
    id: int
    brand: str
    model: str
    year: int


class HistoryItem(BaseModel):
    id: int
    created_at: datetime
    car: HistoryCar
    problem_text: str | None
    repair_min: int
    repair_max: int
    price_as_is: int
    price_after_repair: int
    recommendation: str
