from datetime import datetime

from pydantic import BaseModel


class PartRead(BaseModel):
    id: int
    brand: str | None  # None — универсальная деталь
    name: str
    oem: str
    manufacturer: str | None
    price: int  # ₽
    condition: str  # new / used
    region: str | None
    shop: str
    url: str | None
    collected_at: datetime


class VinResult(BaseModel):
    vin: str
    brand: str | None  # None — марку по VIN определить не удалось, фильтра по марке нет


class PartSearchResponse(BaseModel):
    total: int  # всего найдено (без учёта limit и offset)
    items: list[PartRead]
    vin: VinResult | None = None  # заполнено, если в запросе был VIN
