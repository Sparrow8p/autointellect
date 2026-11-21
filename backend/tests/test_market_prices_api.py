import pytest
from sqlalchemy import func, select

from app.models import MarketPrice
from app.services.market_price_store import upsert_prices
from app.services.market_prices import Aggregate

URL = "/api/market-prices"


@pytest.fixture()
def add_price(session_factory):
    def add(brand, model, year, band, price, samples=12, source="drom"):
        with session_factory() as db:
            upsert_prices(db, brand, model, [Aggregate(year, band, price, samples)], source)

    return add


def ask(client, headers, brand="Hyundai", model="Solaris", year=2018, mileage=85_000):
    params = {"brand": brand, "model": model, "year": year, "mileage": mileage}
    return client.get(URL, params=params, headers=headers)


def test_exact_match(client, auth_headers, add_price):
    add_price("Hyundai", "Solaris", 2018, 50_000, 800_000)
    response = ask(client, auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["price"] == 800_000
    assert body["samples"] == 12
    assert body["year"] == 2018
    assert body["exact_year"] is True
    assert (body["mileage_from"], body["mileage_to"]) == (50_000, 99_999)
    assert body["source"] == "drom"


def test_nearest_year_is_marked_as_approximate(client, auth_headers, add_price):
    add_price("Hyundai", "Solaris", 2017, 50_000, 700_000)
    body = ask(client, auth_headers).json()
    assert (body["year"], body["exact_year"], body["price"]) == (2017, False, 700_000)


def test_exact_year_wins_over_nearby_year(client, auth_headers, add_price):
    add_price("Hyundai", "Solaris", 2017, 50_000, 700_000)
    add_price("Hyundai", "Solaris", 2018, 50_000, 800_000)
    assert ask(client, auth_headers).json()["price"] == 800_000


def test_open_ended_last_band(client, auth_headers, add_price):
    add_price("Hyundai", "Solaris", 2018, 250_000, 400_000)
    body = ask(client, auth_headers, mileage=400_000).json()
    assert (body["mileage_from"], body["mileage_to"]) == (250_000, None)


def test_cyrillic_brand_name(client, auth_headers, add_price):
    add_price("Lada (ВАЗ)", "Granta", 2020, 0, 600_000)
    response = ask(
        client, auth_headers, brand="Lada (ВАЗ)", model="Granta", year=2020, mileage=10_000
    )
    assert response.json()["price"] == 600_000


@pytest.mark.parametrize(
    "query",
    [
        {"year": 2021},  # от ближайшего года (2018) больше двух лет
        {"mileage": 120_000},  # другая корзина пробега
        {"model": "Rio"},  # нет данных по модели
        {"brand": "Kia"},  # нет данных по марке
    ],
)
def test_no_data_is_404(client, auth_headers, add_price, query):
    add_price("Hyundai", "Solaris", 2018, 50_000, 800_000)
    assert ask(client, auth_headers, **query).status_code == 404


def test_requires_token(client):
    response = client.get(URL, params={"brand": "Kia", "model": "Rio", "year": 2018, "mileage": 1})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "params",
    [
        {"brand": "Kia", "model": "Rio", "year": 2018},  # нет пробега
        {"brand": "Kia", "model": "Rio", "year": 2018, "mileage": -1},
        {"brand": "Kia", "model": "Rio", "year": 1900, "mileage": 1},
        {"brand": "", "model": "Rio", "year": 2018, "mileage": 1},
    ],
)
def test_invalid_query_is_rejected(client, auth_headers, params):
    assert client.get(URL, params=params, headers=auth_headers).status_code == 422


def test_upsert_updates_instead_of_duplicating(session_factory):
    with session_factory() as db:
        upsert_prices(db, "Kia", "Rio", [Aggregate(2019, 0, 900_000, 5)], "drom")
        upsert_prices(db, "Kia", "Rio", [Aggregate(2019, 0, 950_000, 8)], "drom")
        upsert_prices(db, "Kia", "Rio", [Aggregate(2019, 0, 1, 1)], "manual")  # другой источник
        assert db.scalar(select(func.count()).select_from(MarketPrice)) == 2
        drom = db.scalar(select(MarketPrice).where(MarketPrice.source == "drom"))
        assert (int(drom.price), drom.samples) == (950_000, 8)
