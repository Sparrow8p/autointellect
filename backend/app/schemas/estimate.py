from pydantic import BaseModel, ConfigDict, Field


class EstimateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    car_id: int
    problem_text: str = Field(min_length=2, max_length=2000)


class EstimateCheckRequest(EstimateRequest):
    # Сумма, которую назвали в СТО, ₽.
    sto_amount: int = Field(gt=0, le=10_000_000)


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


class EstimateCheckResponse(BaseModel):
    recognized: bool
    min_price: int
    max_price: int
    sto_amount: int
    verdict_code: str  # in_range / overpriced / underpriced — для логики на фронте
    verdict: str  # «В диапазоне» / «Завышено» / «Занижено» — для показа
    difference: int  # ₽ за границей диапазона: «+» выше max, «−» ниже min, 0 в диапазоне
    works: list[EstimateWork]
