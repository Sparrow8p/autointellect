from datetime import date, timedelta

import pytest

from app.core.config import get_settings
from tests.helpers import make_car

URL = "/api/service-records"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50
PDF = b"%PDF-1.7\n" + b"0" * 50


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Чеки в тестах пишутся во временную папку, а не в backend/uploads."""
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    return tmp_path


def payload(car_id, **extra):
    body = {
        "car_id": car_id,
        "service_date": "2026-05-03",
        "mileage": 92_000,
        "sto_name": "Автосервис",
        "works": [
            {"name": "Замена масла", "price": 3_500},
            {"name": "Диагностика подвески", "price": 1_500},
        ],
    }
    return {**body, **extra}


def create(client, headers, car_id, **extra):
    response = client.post(URL, json=payload(car_id, **extra), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def upload(client, headers, record_id, content=PNG, name="check.png"):
    return client.put(
        f"{URL}/{record_id}/receipt", files={"file": (name, content)}, headers=headers
    )


# --- записи ---


def test_create_record_computes_total(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = create(client, auth_headers, car_id)
    assert body["car_id"] == car_id
    assert body["service_date"] == "2026-05-03"
    assert body["mileage"] == 92_000
    assert body["works"] == [
        {"name": "Замена масла", "price": 3_500},
        {"name": "Диагностика подвески", "price": 1_500},
    ]
    assert body["total"] == 5_000
    assert body["has_receipt"] is False


def test_client_cannot_send_total(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = create(client, auth_headers, car_id, total=1)
    assert body["total"] == 5_000


def test_optional_fields_can_be_omitted(client, auth_headers):
    car_id = make_car(client, auth_headers)
    body = {"car_id": car_id, "service_date": "2026-05-03", "works": [{"name": "ТО", "price": 0}]}
    response = client.post(URL, json=body, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["mileage"] is None
    assert response.json()["sto_name"] is None


def test_list_is_newest_first_and_per_car(client, auth_headers):
    car_id = make_car(client, auth_headers)
    other_car_id = make_car(client, auth_headers)
    create(client, auth_headers, car_id, service_date="2025-01-10")
    create(client, auth_headers, car_id, service_date="2026-05-03")
    create(client, auth_headers, other_car_id)
    records = client.get(URL, params={"car_id": car_id}, headers=auth_headers).json()
    assert [r["service_date"] for r in records] == ["2026-05-03", "2025-01-10"]


def test_get_and_delete_record(client, auth_headers):
    car_id = make_car(client, auth_headers)
    record_id = create(client, auth_headers, car_id)["id"]
    assert client.get(f"{URL}/{record_id}", headers=auth_headers).status_code == 200
    assert client.delete(f"{URL}/{record_id}", headers=auth_headers).status_code == 204
    assert client.get(f"{URL}/{record_id}", headers=auth_headers).status_code == 404


def test_foreign_car_and_record_are_404(client, auth_headers, other_auth_headers):
    car_id = make_car(client, auth_headers)
    record_id = create(client, auth_headers, car_id)["id"]
    stranger = other_auth_headers
    assert client.post(URL, json=payload(car_id), headers=stranger).status_code == 404
    assert client.get(URL, params={"car_id": car_id}, headers=stranger).status_code == 404
    assert client.get(f"{URL}/{record_id}", headers=stranger).status_code == 404
    assert client.delete(f"{URL}/{record_id}", headers=stranger).status_code == 404
    assert upload(client, stranger, record_id).status_code == 404
    assert client.get(f"{URL}/{record_id}/receipt", headers=stranger).status_code == 404
    assert (
        client.get(f"{URL}/report", params={"car_id": car_id}, headers=stranger).status_code == 404
    )


@pytest.mark.parametrize(
    "override",
    [
        {"service_date": (date.today() + timedelta(days=1)).isoformat()},
        {"service_date": "не дата"},
        {"mileage": -1},
        {"works": []},
        {"works": [{"name": "ТО", "price": -5}]},
        {"works": [{"name": "   ", "price": 100}]},
        {"works": [{"name": "ТО", "price": 10**8}]},
        {"works": [{"name": "ТО", "price": 100}] * 51},
    ],
)
def test_invalid_record_is_rejected(client, auth_headers, override):
    car_id = make_car(client, auth_headers)
    response = client.post(URL, json=payload(car_id, **override), headers=auth_headers)
    assert response.status_code == 422


def test_requires_token(client):
    assert client.get(URL, params={"car_id": 1}).status_code == 401
    assert client.post(URL, json={}).status_code == 401
    assert client.get(f"{URL}/report", params={"car_id": 1}).status_code == 401


# --- чеки ---


def test_upload_and_download_receipt(client, auth_headers):
    car_id = make_car(client, auth_headers)
    record_id = create(client, auth_headers, car_id)["id"]
    response = upload(client, auth_headers, record_id)
    assert response.status_code == 200
    assert response.json()["has_receipt"] is True
    download = client.get(f"{URL}/{record_id}/receipt", headers=auth_headers)
    assert download.status_code == 200
    assert download.content == PNG
    assert download.headers["content-type"] == "image/png"
    assert download.headers["x-content-type-options"] == "nosniff"


def test_replacing_receipt_removes_old_file(client, auth_headers, upload_dir):
    car_id = make_car(client, auth_headers)
    record_id = create(client, auth_headers, car_id)["id"]
    upload(client, auth_headers, record_id, PNG)
    upload(client, auth_headers, record_id, PDF, name="check.pdf")
    files = list((upload_dir / "receipts").iterdir())
    assert len(files) == 1 and files[0].suffix == ".pdf"
    download = client.get(f"{URL}/{record_id}/receipt", headers=auth_headers)
    assert download.headers["content-type"] == "application/pdf"


def test_type_is_taken_from_content_not_from_name(client, auth_headers):
    car_id = make_car(client, auth_headers)
    record_id = create(client, auth_headers, car_id)["id"]
    assert (
        upload(client, auth_headers, record_id, b"<script>x</script>", "a.png").status_code == 415
    )
    # настоящий PNG с чужим расширением принимается
    assert upload(client, auth_headers, record_id, PNG, "check.txt").status_code == 200


def test_too_large_receipt_is_rejected(client, auth_headers):
    car_id = make_car(client, auth_headers)
    record_id = create(client, auth_headers, car_id)["id"]
    big = PNG + b"0" * (5 * 1024 * 1024)
    assert upload(client, auth_headers, record_id, big).status_code == 413


def test_receipt_missing_is_404(client, auth_headers):
    car_id = make_car(client, auth_headers)
    record_id = create(client, auth_headers, car_id)["id"]
    assert client.get(f"{URL}/{record_id}/receipt", headers=auth_headers).status_code == 404


def test_deleting_record_deletes_receipt_file(client, auth_headers, upload_dir):
    car_id = make_car(client, auth_headers)
    record_id = create(client, auth_headers, car_id)["id"]
    upload(client, auth_headers, record_id)
    assert len(list((upload_dir / "receipts").iterdir())) == 1
    client.delete(f"{URL}/{record_id}", headers=auth_headers)
    assert list((upload_dir / "receipts").iterdir()) == []


# --- PDF-отчёт ---


def test_report_is_pdf(client, auth_headers):
    car_id = make_car(client, auth_headers)
    create(client, auth_headers, car_id)
    response = client.get(f"{URL}/report", params={"car_id": car_id}, headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_report_without_records_is_404(client, auth_headers):
    car_id = make_car(client, auth_headers)
    response = client.get(f"{URL}/report", params={"car_id": car_id}, headers=auth_headers)
    assert response.status_code == 404
