"""Сверка суммы от СТО с расчётным диапазоном (чистая логика, без базы)."""

from dataclasses import dataclass

IN_RANGE = "in_range"
OVERPRICED = "overpriced"
UNDERPRICED = "underpriced"

VERDICT_TEXT = {
    IN_RANGE: "В диапазоне",
    OVERPRICED: "Завышено",
    UNDERPRICED: "Занижено",
}


@dataclass(frozen=True)
class CheckResult:
    code: str  # in_range / overpriced / underpriced
    text: str  # «В диапазоне» / «Завышено» / «Занижено»
    # Насколько сумма вышла за границу, ₽: «+» выше max, «−» ниже min, 0 — в диапазоне.
    difference: int


def check_amount(amount: int, min_price: int, max_price: int) -> CheckResult:
    """Границы диапазона входят в «В диапазоне»."""
    if min_price > max_price:
        raise ValueError("min_price must not exceed max_price")
    if amount > max_price:
        return CheckResult(OVERPRICED, VERDICT_TEXT[OVERPRICED], amount - max_price)
    if amount < min_price:
        return CheckResult(UNDERPRICED, VERDICT_TEXT[UNDERPRICED], amount - min_price)
    return CheckResult(IN_RANGE, VERDICT_TEXT[IN_RANGE], 0)
