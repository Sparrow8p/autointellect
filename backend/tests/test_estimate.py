import pytest

URL = "/api/calculations/estimate"


def make_car(client, headers, region):
    payload = {
        "brand": "Hyundai",
        "model": "Solaris",
        "year": 2018,
        "mileage": 85000,
        "region": region,
    }
    response = client.post("/api/cars", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


def test_estimate_in_moscow_region(client, auth_headers):
    car_id = make_car(client, auth_headers, "Московская область")  # коэффициент 1.3
    response = client.post(
        URL, json={"car_id": car_id, "problem_text": "Стучит подвеска"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recognized"] is True
    assert body["region_coefficient"] == 1.3
    # «стучит» -> стойка стабилизатора (16), амортизатор (17), шаровая опора (20)
    assert [w["id"] for w in body["works"]] == [16, 17, 20]
    assert [w["min_price"] for w in body["works"]] == [3580, 7500, 4920]
    assert [w["max_price"] for w in body["works"]] == [4580, 9900, 6120]
    assert body["min_price"] == 16000
    assert body["max_price"] == 20600
    assert "стуч" in body["matched_keywords"]


def test_estimate_depends_on_region(client, auth_headers):
    moscow = make_car(client, auth_headers, "Московская область")
    kazan = make_car(client, auth_headers, "Республика Татарстан")  # коэффициент 1.0
    text = {"problem_text": "Стучит подвеска"}

    msk = client.post(URL, json={"car_id": moscow, **text}, headers=auth_headers).json()
    ktm = client.post(URL, json={"car_id": kazan, **text}, headers=auth_headers).json()

    assert (ktm["min_price"], ktm["max_price"]) == (13900, 18500)
    assert msk["min_price"] > ktm["min_price"]
    assert msk["max_price"] > ktm["max_price"]
    assert ktm["min_price"] <= ktm["max_price"]


def test_unrecognized_problem_falls_back_to_diagnostics(client, auth_headers):
    car_id = make_car(client, auth_headers, "Республика Татарстан")
    response = client.post(
        URL, json={"car_id": car_id, "problem_text": "абракадабра"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recognized"] is False
    assert [w["name"] for w in body["works"]] == ["Компьютерная диагностика"]
    assert (body["min_price"], body["max_price"]) == (2000, 2000)


def test_estimate_of_foreign_car_is_404(client, auth_headers, other_auth_headers):
    car_id = make_car(client, auth_headers, "Москва")
    response = client.post(
        URL, json={"car_id": car_id, "problem_text": "стучит"}, headers=other_auth_headers
    )
    assert response.status_code == 404


def test_estimate_requires_token(client):
    response = client.post(URL, json={"car_id": 1, "problem_text": "стучит"})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {"problem_text": "стучит"},  # нет car_id
        {"car_id": 1},  # нет текста
        {"car_id": 1, "problem_text": " "},  # пустой текст
        {"car_id": 1, "problem_text": "а" * 2001},  # слишком длинный
    ],
)
def test_estimate_validates_input(client, auth_headers, payload):
    assert client.post(URL, json=payload, headers=auth_headers).status_code == 422
