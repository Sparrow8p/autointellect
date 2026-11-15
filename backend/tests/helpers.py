def make_car(client, headers, region="Республика Татарстан"):
    """Создаёт авто через API и возвращает его id. По умолчанию регион с коэффициентом 1.0."""
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
