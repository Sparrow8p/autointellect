from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CarCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900)
    mileage: int = Field(ge=0, le=5_000_000)  # км
    # Название региона из справочника GET /api/reference/regions.
    region: str = Field(min_length=1, max_length=100)

    @field_validator("year")
    @classmethod
    def year_not_in_far_future(cls, value: int) -> int:
        # +1: в конце года уже продают автомобили следующего модельного года.
        if value > date.today().year + 1:
            raise ValueError("year is in the future")
        return value


class CarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    year: int
    mileage: int
    region: str
