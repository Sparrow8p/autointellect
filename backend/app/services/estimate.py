from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Region, Work, WorkKeyword
from app.services.parsing import parse_problem, select_works
from app.services.pricing import work_price_range

# Если по тексту ничего не распознано, предлагаем начать с диагностики.
FALLBACK_WORK_NAME = "Компьютерная диагностика"


@dataclass
class WorkLine:
    work: Work
    min_price: int
    max_price: int


@dataclass
class Estimate:
    recognized: bool
    keywords: list[str]
    region_coefficient: Decimal
    lines: list[WorkLine]

    @property
    def min_price(self) -> int:
        return sum(line.min_price for line in self.lines)

    @property
    def max_price(self) -> int:
        return sum(line.max_price for line in self.lines)


def estimate_repair(
    db: Session, *, region_name: str, problem_text: str, hourly_rate: int
) -> Estimate:
    coefficient = db.scalar(select(Region.coefficient).where(Region.name == region_name))
    if coefficient is None:
        coefficient = Decimal("1.0")  # регион не из справочника — базовая цена

    rules = db.scalars(select(WorkKeyword)).all()
    all_works = db.scalars(select(Work).order_by(Work.id)).all()

    parsed = parse_problem(problem_text, rules)
    works = select_works(parsed, all_works)
    recognized = bool(works)
    if not recognized:
        works = [work for work in all_works if work.name == FALLBACK_WORK_NAME]

    lines = []
    for work in works:
        low, high = work_price_range(work.hours, work.part_price, hourly_rate, coefficient)
        lines.append(WorkLine(work=work, min_price=low, max_price=high))

    return Estimate(
        recognized=recognized,
        keywords=parsed.keywords,
        region_coefficient=Decimal(str(coefficient)),
        lines=lines,
    )
