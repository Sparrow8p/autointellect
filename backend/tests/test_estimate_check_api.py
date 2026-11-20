import pytest

from tests.helpers import make_car

URL = "/api/calculations/check-estimate"

# «Стучит подвеска» в регионе с коэффициентом 1.0: диапазон 13 900 – 18 500 ₽.


def request(client, headers, car_id, sto_amount, text="Стучит подвеска"):
    payload = {"car_id": car_id, "problem_text": text, "sto_amount": sto_amount}
    return client.post(URL, json=payload, headers=headers)


def test_amount_in_range(client, auth_headers):
    car_id = make_car(client, auth_headers)
    response = request(client, auth_headers, car_id, 16_000)
    assert response.status_code == 200
    body = response.json()
    assert (body["min_price"], body["max_price"]) == (13_900, 18_500)
    assert body["sto_amount"] == 16_000
    assert (body["verdict_code"], body["verdict"], body["difference"]) == (
        "in_range",
        "В диапазоне",
        0,
    )
    assert [w["id"] for w in body["works"]] == [16, 17, 20]
    assert body["recognized"] is True


def test_overpriced(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = request(client, auth_headers, car_id, 25_000).json()
    assert (body["verdict_code"], body["verdict"], body["difference"]) == (
        "overpriced",
        "Завышено",
        6_500,
    )


def test_underpriced(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = request(client, auth_headers, car_id, 9_000).json()
    assert (body["verdict_code"], body["verdict"], body["difference"]) == (
        "underpriced",
        "Занижено",
        -4_900,
    )


def test_region_changes_range(client, auth_headers):
    car_id = make_car(client, auth_headers, region="Московская область")  # коэффициент 1.3
    # В Московской области диапазон 16 000 – 20 600 ₽, в Татарстане 19 000 ещё было бы завышено.
    body = request(client, auth_headers, car_id, 19_000).json()
    assert (body["min_price"], body["max_price"]) == (16_000, 20_600)
    assert body["verdict_code"] == "in_range"


def test_unrecognized_problem_is_checked_against_diagnostics(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = request(client, auth_headers, car_id, 2_000, text="абракадабра").json()
    assert body["recognized"] is False
    assert body["verdict_code"] == "in_range"


def test_foreign_car_is_404(client, auth_headers, other_auth_headers):
    car_id = make_car(client, auth_headers)
    assert request(client, other_auth_headers, car_id, 16_000).status_code == 404


def test_requires_token(client):
    payload = {"car_id": 1, "problem_text": "стучит", "sto_amount": 1000}
    assert client.post(URL, json=payload).status_code == 401


@pytest.mark.parametrize("override", [{"sto_amount": 0}, {"sto_amount": -1}, {"sto_amount": 10**8}])
def test_invalid_amount_is_rejected(client, auth_headers, override):
    car_id = make_car(client, auth_headers)
    payload = {"car_id": car_id, "problem_text": "стучит", **override}
    assert client.post(URL, json=payload, headers=auth_headers).status_code == 422


def test_missing_amount_is_rejected(client, auth_headers):
    car_id = make_car(client, auth_headers)
    payload = {"car_id": car_id, "problem_text": "стучит"}
    assert client.post(URL, json=payload, headers=auth_headers).status_code == 422
