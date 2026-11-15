import pytest

from tests.helpers import make_car

SAVE = "/api/history/save"
LIST = "/api/history"


def save(client, headers, car_id, car_price=400_000, text="Стучит подвеска", **extra):
    payload = {"car_id": car_id, "problem_text": text, "car_price": car_price, **extra}
    return client.post(SAVE, json=payload, headers=headers)


def test_history_is_empty_for_new_user(client, auth_headers):
    response = client.get(LIST, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_save_returns_stored_calculation(client, auth_headers):
    car_id = make_car(client, auth_headers)
    response = save(client, auth_headers, car_id)
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert body["car"] == {"id": car_id, "brand": "Hyundai", "model": "Solaris", "year": 2018}
    assert body["problem_text"] == "Стучит подвеска"
    assert body["repair_min"] == 13_900
    assert body["repair_max"] == 18_500
    assert body["price_as_is"] == 400_000
    assert body["price_after_repair"] == 470_000
    assert body["recommendation"] == "Ремонт окупится. Выгода: 53 800 ₽"


def test_saved_calculation_appears_in_list(client, auth_headers):
    car_id = make_car(client, auth_headers)
    saved = save(client, auth_headers, car_id).json()
    listed = client.get(LIST, headers=auth_headers).json()
    assert listed == [saved]


def test_history_is_newest_first(client, auth_headers):
    car_id = make_car(client, auth_headers)
    first = save(client, auth_headers, car_id, text="Стучит подвеска").json()
    second = save(client, auth_headers, car_id, text="Замена масла").json()
    assert [item["id"] for item in client.get(LIST, headers=auth_headers).json()] == [
        second["id"],
        first["id"],
    ]


def test_pagination(client, auth_headers):
    car_id = make_car(client, auth_headers)
    ids = [save(client, auth_headers, car_id).json()["id"] for _ in range(3)]
    newest_first = list(reversed(ids))

    page = client.get(LIST, params={"limit": 2}, headers=auth_headers).json()
    assert [i["id"] for i in page] == newest_first[:2]
    rest = client.get(LIST, params={"limit": 2, "offset": 2}, headers=auth_headers).json()
    assert [i["id"] for i in rest] == newest_first[2:]


def test_history_is_private(client, auth_headers, other_auth_headers):
    car_id = make_car(client, auth_headers)
    save(client, auth_headers, car_id)
    assert client.get(LIST, headers=other_auth_headers).json() == []


def test_cannot_save_for_foreign_car(client, auth_headers, other_auth_headers):
    car_id = make_car(client, auth_headers)
    assert save(client, other_auth_headers, car_id).status_code == 404
    assert client.get(LIST, headers=auth_headers).json() == []


def test_server_ignores_client_supplied_numbers(client, auth_headers):
    car_id = make_car(client, auth_headers)
    response = save(
        client,
        auth_headers,
        car_id,
        price_after_repair=99_999_999,
        recommendation="Ремонт окупится. Выгода: 1 000 000 ₽",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["price_after_repair"] == 470_000
    assert body["recommendation"] == "Ремонт окупится. Выгода: 53 800 ₽"


@pytest.mark.parametrize(("method", "path"), [("get", LIST), ("post", SAVE)])
def test_history_requires_token(client, method, path):
    kwargs = {"json": {"car_id": 1, "problem_text": "стучит", "car_price": 1000}}
    kwargs = kwargs if method == "post" else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_invalid_pagination_is_rejected(client, auth_headers, params):
    assert client.get(LIST, params=params, headers=auth_headers).status_code == 422


@pytest.mark.parametrize("override", [{"car_price": 0}, {"problem_text": ""}])
def test_invalid_save_is_rejected(client, auth_headers, override):
    car_id = make_car(client, auth_headers)
    payload = {"car_id": car_id, "problem_text": "стучит", "car_price": 400_000, **override}
    assert client.post(SAVE, json=payload, headers=auth_headers).status_code == 422
