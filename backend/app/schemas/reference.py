from pydantic import BaseModel, ConfigDict


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CarModelRead(BaseModel):
    id: int
    name: str
    brand: str


class RegionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
