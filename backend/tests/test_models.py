import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Calculation, Car, User


def _make_user_and_car(db):
    user = User(email="u@example.com", password_hash="x")
    db.add(user)
    db.flush()
    car = Car(
        user_id=user.id,
        brand="Hyundai",
        model="Solaris",
        year=2018,
        mileage=85000,
        region="Московская область",
    )
    db.add(car)
    db.flush()
    return user, car


def _calc(user, car, **overrides):
    values = {
        "user_id": user.id,
        "car_id": car.id,
        "problem_text": "Удар в переднюю часть",
        "repair_min": 80000,
        "repair_max": 95000,
        "price_as_is": 980000,
        "price_after_repair": 1200000,
        "recommendation": "Ремонт целесообразен",
    }
    values.update(overrides)
    return Calculation(**values)


def test_calculation_is_saved_with_created_at(session_factory):
    with session_factory() as db:
        user, car = _make_user_and_car(db)
        calc = _calc(user, car)
        db.add(calc)
        db.commit()
        db.refresh(calc)
        assert calc.created_at is not None


def test_calculation_allows_photo_only_request(session_factory):
    with session_factory() as db:
        user, car = _make_user_and_car(db)
        db.add(_calc(user, car, problem_text=None))
        db.commit()


def test_repair_max_cannot_be_less_than_min(session_factory):
    with session_factory() as db:
        user, car = _make_user_and_car(db)
        db.add(_calc(user, car, repair_min=100000, repair_max=50000))
        with pytest.raises(IntegrityError):
            db.commit()


def test_car_mileage_cannot_be_negative(session_factory):
    with session_factory() as db:
        user = User(email="u@example.com", password_hash="x")
        db.add(user)
        db.flush()
        db.add(
            Car(
                user_id=user.id,
                brand="Kia",
                model="Rio",
                year=2020,
                mileage=-1,
                region="Москва",
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
