import pytest

URL = "/api/calculations/price-after-repair"


def test_cheap_repair_gives_full_growth(client, auth_headers):
    # пример из проектного документа: авто 400 000 ₽, ремонт 50 000 ₽ -> 470 000 ₽
    response = client.post(
        URL, json={"car_price": 400_000, "repair_cost": 50_000}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() == {
        "car_price": 400_000,
        "repair_cost": 50_000,
        "repair_share_percent": 12.5,
        "price_growth_percent": 17.5,
        "price_growth": 70_000,
        "price_after_repair": 470_000,
    }


def test_medium_repair_gives_reduced_growth(client, auth_headers):
    body = client.post(
        URL, json={"car_price": 1_000_000, "repair_cost": 400_000}, headers=auth_headers
    ).json()
    assert body["repair_share_percent"] == 40.0
    assert body["price_growth_percent"] == 9.75
    assert body["price_after_repair"] == 1_097_500


def test_expensive_repair_almost_does_not_raise_price(client, auth_headers):
    body = client.post(
        URL, json={"car_price": 100_000, "repair_cost": 80_000}, headers=auth_headers
    ).json()
    assert body["price_growth_percent"] == 2.0
    assert body["price_after_repair"] == 102_000


def test_requires_token(client):
    response = client.post(URL, json={"car_price": 400_000, "repair_cost": 50_000})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {"car_price": 0, "repair_cost": 1000},
        {"car_price": -1, "repair_cost": 1000},
        {"car_price": 400_000, "repair_cost": 0},
        {"car_price": 400_000, "repair_cost": -5},
        {"car_price": 100_000_001, "repair_cost": 1000},
        {"car_price": 400_000},  # нет repair_cost
        {"repair_cost": 1000},  # нет car_price
    ],
)
def test_invalid_input_is_rejected(client, auth_headers, payload):
    assert client.post(URL, json=payload, headers=auth_headers).status_code == 422
