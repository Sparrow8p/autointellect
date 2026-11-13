from pydantic import BaseModel, ConfigDict, Field

from app.schemas.estimate import EstimateWork

MAX_CAR_PRICE = 100_000_000  # ₽, защита от опечаток вроде лишних нулей


class SaveCalculationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    car_id: int
    problem_text: str = Field(min_length=2, max_length=2000)
    car_price: int = Field(gt=0, le=MAX_CAR_PRICE, description="Текущая цена авто, ₽")


class ScenariosRequest(SaveCalculationRequest):
    years: int = Field(default=1, ge=1, le=3, description="Срок эксплуатации для сценария 3, лет")


class RepairRange(BaseModel):
    min_price: int  # с б/у запчастями
    max_price: int  # с новыми запчастями
    repair_cost: int  # середина диапазона — именно она участвует в сценариях


class SellAsIs(BaseModel):
    value: int  # цена авто
    recommended: bool  # True, если выгоднее продать как есть


class RepairAndSell(BaseModel):
    repair_cost: int
    price_after_repair: int
    price_growth_percent: float  # на сколько процентов выросла цена
    value: int  # цена после ремонта − стоимость ремонта
    recommended: bool  # True, если ремонт окупится


class RepairAndKeep(BaseModel):
    repair_cost: int
    running_costs: int  # расходы на владение за весь срок
    years: int
    value: int  # −(ремонт + расходы): это затраты, а не сумма продажи
    recommended: bool = False  # всегда False: сценарий не сравнивается с продажей


class PriceAfterRepairRequest(BaseModel):
    car_price: int = Field(gt=0, le=MAX_CAR_PRICE, description="Текущая цена авто, ₽")
    repair_cost: int = Field(gt=0, le=MAX_CAR_PRICE, description="Стоимость ремонта, ₽")


class PriceAfterRepairResponse(BaseModel):
    car_price: int
    repair_cost: int
    repair_share_percent: float  # какую часть цены авто составляет ремонт
    price_growth_percent: float  # на сколько процентов вырастет цена
    price_growth: int  # на сколько рублей вырастет цена
    price_after_repair: int


class ScenariosBlock(BaseModel):
    sell_as_is: SellAsIs
    repair_and_sell: RepairAndSell
    repair_and_keep: RepairAndKeep


class ScenariosResponse(BaseModel):
    # False — проблему распознать не удалось, ремонт посчитан как одна диагностика.
    recognized: bool
    matched_keywords: list[str]
    region_coefficient: float
    works: list[EstimateWork]
    repair: RepairRange
    scenarios: ScenariosBlock
    profit: int  # сценарий 2 − сценарий 1
    recommendation: str
