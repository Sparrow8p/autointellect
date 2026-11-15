from pydantic import BaseModel, ConfigDict, Field


class EstimateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    car_id: int
    problem_text: str = Field(min_length=2, max_length=2000)


class EstimateWork(BaseModel):
    id: int
    name: str
    category: str
    hours: float
    min_price: int
    max_price: int


class EstimateResponse(BaseModel):
    # False — проблему распознать не удалось, в расчёт попала только диагностика.
    recognized: bool
    min_price: int  # ₽, целое
    max_price: int  # ₽, целое
    region_coefficient: float
    matched_keywords: list[str]
    works: list[EstimateWork]
