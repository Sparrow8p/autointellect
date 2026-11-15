import pytest

CAR = {
    "brand": "Hyundai",
    "model": "Solaris",
    "year": 2018,
    "mileage": 85000,
    "region": "Московская область",
}


def test_list_is_empty_for_new_user(client, auth_headers):
    response = client.get("/api/cars", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_car(client, auth_headers):
    created = client.post("/api/cars", json=CAR, headers=auth_headers)
    assert created.status_code == 201
    body = created.json()
    assert isinstance(body["id"], int)
    assert {k: body[k] for k in CAR} == CAR
    assert "user_id" not in body

    listed = client.get("/api/cars", headers=auth_headers).json()
    assert [c["id"] for c in listed] == [body["id"]]


def test_create_strips_whitespace(client, auth_headers):
    response = client.post("/api/cars", json={**CAR, "brand": "  Kia  "}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["brand"] == "Kia"


def test_cars_are_private_to_their_owner(client, auth_headers, other_auth_headers):
    client.post("/api/cars", json=CAR, headers=auth_headers)
    assert client.get("/api/cars", headers=other_auth_headers).json() == []


def test_delete_own_car(client, auth_headers):
    car_id = client.post("/api/cars", json=CAR, headers=auth_headers).json()["id"]
    response = client.delete(f"/api/cars/{car_id}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get("/api/cars", headers=auth_headers).json() == []


def test_cannot_delete_foreign_car(client, auth_headers, other_auth_headers):
    car_id = client.post("/api/cars", json=CAR, headers=auth_headers).json()["id"]
    response = client.delete(f"/api/cars/{car_id}", headers=other_auth_headers)
    assert response.status_code == 404
    # у владельца авто на месте
    assert len(client.get("/api/cars", headers=auth_headers).json()) == 1


def test_delete_missing_car_is_404(client, auth_headers):
    assert client.delete("/api/cars/9999", headers=auth_headers).status_code == 404


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/cars"), ("post", "/api/cars"), ("delete", "/api/cars/1")],
)
def test_cars_require_token(client, method, path):
    kwargs = {"json": CAR} if method == "post" else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401


def test_unknown_region_is_rejected(client, auth_headers):
    response = client.post("/api/cars", json={**CAR, "region": "Атлантида"}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "override",
    [
        {"mileage": -1},
        {"year": 1800},
        {"year": 2200},
        {"brand": "   "},
        {"model": ""},
    ],
)
def test_invalid_car_is_rejected(client, auth_headers, override):
    response = client.post("/api/cars", json={**CAR, **override}, headers=auth_headers)
    assert response.status_code == 422


def test_missing_field_is_rejected(client, auth_headers):
    payload = {k: v for k, v in CAR.items() if k != "region"}
    assert client.post("/api/cars", json=payload, headers=auth_headers).status_code == 422
