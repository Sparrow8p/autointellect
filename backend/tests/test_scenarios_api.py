import pytest

from tests.helpers import make_car

URL = "/api/calculations/scenarios"

# «Стучит подвеска» в регионе с коэффициентом 1.0: ремонт 13 900 – 18 500 ₽, середина 16 200 ₽.


def request(client, headers, car_id, car_price=400_000, text="Стучит подвеска", **extra):
    payload = {"car_id": car_id, "problem_text": text, "car_price": car_price, **extra}
    return client.post(URL, json=payload, headers=headers)


def test_repair_pays_off(client, auth_headers):
    car_id = make_car(client, auth_headers)
    response = request(client, auth_headers, car_id)
    assert response.status_code == 200
    body = response.json()

    assert body["recognized"] is True
    assert body["repair"] == {"min_price": 13_900, "max_price": 18_500, "repair_cost": 16_200}
    assert body["scenarios"]["sell_as_is"] == {"value": 400_000, "recommended": False}
    assert body["scenarios"]["repair_and_sell"] == {
        "repair_cost": 16_200,
        "price_after_repair": 470_000,  # +17,5%
        "price_growth_percent": 17.5,
        "value": 453_800,
        "recommended": True,  # рекомендуется ремонт
    }
    assert body["scenarios"]["repair_and_keep"] == {
        "repair_cost": 16_200,
        "running_costs": 32_000,  # 8% от 400 000 за 1 год
        "years": 1,
        "value": -48_200,
        "recommended": False,  # затраты, с продажей не сравнивается
    }
    assert body["profit"] == 53_800
    assert body["recommendation"] == "Ремонт окупится. Выгода: 53 800 ₽"
    assert [w["id"] for w in body["works"]] == [16, 17, 20]


def test_cheap_car_is_better_sold_as_is(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = request(client, auth_headers, car_id, car_price=60_000).json()
    assert body["scenarios"]["repair_and_sell"]["price_after_repair"] == 70_500
    assert body["profit"] == -5_700
    assert body["recommendation"] == "Выгоднее продать как есть"
    # рекомендация «продать как есть» помечает именно сценарий 1
    assert body["scenarios"]["sell_as_is"]["recommended"] is True
    assert body["scenarios"]["repair_and_sell"]["recommended"] is False
    assert body["scenarios"]["repair_and_keep"]["recommended"] is False


def test_years_change_running_costs(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = request(client, auth_headers, car_id, years=2).json()
    keep = body["scenarios"]["repair_and_keep"]
    assert (keep["years"], keep["running_costs"], keep["value"]) == (2, 64_000, -80_200)


def test_region_changes_repair_cost(client, auth_headers):
    car_id = make_car(client, auth_headers, region="Московская область")  # коэффициент 1.3
    body = request(client, auth_headers, car_id).json()
    assert body["repair"] == {"min_price": 16_000, "max_price": 20_600, "repair_cost": 18_300}
    assert body["scenarios"]["repair_and_sell"]["value"] == 470_000 - 18_300


def test_unrecognized_problem_still_returns_scenarios(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = request(client, auth_headers, car_id, text="абракадабра").json()
    assert body["recognized"] is False
    assert body["repair"]["repair_cost"] == 2_000  # одна диагностика
    assert body["scenarios"]["sell_as_is"]["value"] == 400_000


def test_foreign_car_is_404(client, auth_headers, other_auth_headers):
    car_id = make_car(client, auth_headers)
    assert request(client, other_auth_headers, car_id).status_code == 404


def test_requires_token(client):
    response = client.post(URL, json={"car_id": 1, "problem_text": "стучит", "car_price": 1000})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "override",
    [
        {"car_price": 0},
        {"car_price": -5},
        {"car_price": 100_000_001},
        {"years": 0},
        {"years": 4},
        {"problem_text": " "},
    ],
)
def test_invalid_input_is_rejected(client, auth_headers, override):
    car_id = make_car(client, auth_headers)
    payload = {"car_id": car_id, "problem_text": "стучит", "car_price": 400_000, **override}
    assert client.post(URL, json=payload, headers=auth_headers).status_code == 422


def test_missing_price_is_rejected(client, auth_headers):
    car_id = make_car(client, auth_headers)
    payload = {"car_id": car_id, "problem_text": "стучит"}
    assert client.post(URL, json=payload, headers=auth_headers).status_code == 422
