from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_AMOUNT = 10_000_000


class ServiceWorkIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0, le=MAX_AMOUNT)  # ₽


class ServiceRecordCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    car_id: int
    service_date: date
    mileage: int | None = Field(default=None, ge=0, le=2_000_000)  # км
    sto_name: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=2000)
    works: list[ServiceWorkIn] = Field(min_length=1, max_length=50)

    @field_validator("service_date")
    @classmethod
    def not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("service_date must not be in the future")
        return value

    @field_validator("sto_name", "note")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        return value or None


class ServiceWorkRead(BaseModel):
    name: str
    price: int


class ServiceRecordRead(BaseModel):
    id: int
    car_id: int
    service_date: date
    mileage: int | None
    sto_name: str | None
    note: str | None
    works: list[ServiceWorkRead]
    total: int  # сумма работ, считается на сервере
    has_receipt: bool
    created_at: datetime
