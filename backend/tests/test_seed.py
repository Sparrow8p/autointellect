from decimal import Decimal

from sqlalchemy import func, select

from app.db.seed import seed_reference_data
from app.models import Brand, CarModel, Region, Work, WorkKeyword


def _count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_seed_loads_all_reference_data(session_factory):
    with session_factory() as db:
        assert _count(db, Work) == 30
        assert _count(db, WorkKeyword) == 74
        assert _count(db, Region) == 89
        assert _count(db, Brand) == 18
        assert _count(db, CarModel) == 79


def test_work_matches_source_table(session_factory):
    with session_factory() as db:
        work = db.get(Work, 17)
        assert work.name == "Замена амортизатора (1 шт)"
        assert work.hours == Decimal("1.5")
        assert work.part_price == Decimal("6000")
        assert work.category == "Подвеска"


def test_seed_is_idempotent(session_factory):
    with session_factory() as db:
        seed_reference_data(db)
        seed_reference_data(db)
        assert _count(db, Work) == 30
        assert _count(db, WorkKeyword) == 74
        assert _count(db, Region) == 89
        assert _count(db, CarModel) == 79


def test_seed_does_not_overwrite_manual_changes(session_factory):
    with session_factory() as db:
        region = db.scalar(select(Region).where(Region.name == "Москва"))
        region.coefficient = Decimal("1.5")
        db.commit()

        seed_reference_data(db)

        db.expire_all()
        region = db.scalar(select(Region).where(Region.name == "Москва"))
        assert region.coefficient == Decimal("1.5")
