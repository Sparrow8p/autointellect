def test_brands_are_public_and_sorted(client):
    response = client.get("/api/reference/brands")  # без токена
    assert response.status_code == 200
    names = [b["name"] for b in response.json()]
    assert "Hyundai" in names
    assert names == sorted(names)
    assert set(response.json()[0]) == {"id", "name"}


def test_models_of_brand(client):
    response = client.get("/api/reference/models", params={"brand": "Hyundai"})
    assert response.status_code == 200
    models = response.json()
    assert "Solaris" in [m["name"] for m in models]
    assert {m["brand"] for m in models} == {"Hyundai"}


def test_models_without_brand_returns_all(client):
    response = client.get("/api/reference/models")
    assert response.status_code == 200
    assert len(response.json()) == 79
    assert {"Hyundai", "Kia"} <= {m["brand"] for m in response.json()}


def test_models_of_unknown_brand_is_404(client):
    response = client.get("/api/reference/models", params={"brand": "Несуществующая"})
    assert response.status_code == 404


def test_regions(client):
    response = client.get("/api/reference/regions")
    assert response.status_code == 200
    regions = response.json()
    assert len(regions) == 89
    names = [r["name"] for r in regions]
    assert "Московская область" in names
    assert set(regions[0]) == {"id", "name"}  # коэффициент наружу не отдаём
