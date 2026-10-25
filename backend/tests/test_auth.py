from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings


def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "new@example.com",
            "password": "correct-horse-battery",
            "phone": "+79991234567",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["phone"] == "+79991234567"
    assert isinstance(body["id"], int)
    # Пароль и хеш наружу не отдаются.
    assert "password" not in body
    assert "password_hash" not in body


def test_register_normalizes_email_and_blocks_duplicates(client):
    payload = {"email": "Driver@Example.com", "password": "correct-horse-battery"}
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    assert first.json()["email"] == "driver@example.com"

    second = client.post(
        "/api/auth/register",
        json={"email": "driver@example.com", "password": "another-password-1"},
    )
    assert second.status_code == 409


def test_register_duplicate_phone(client):
    base = {"password": "correct-horse-battery", "phone": "+79991234567"}
    first = client.post("/api/auth/register", json={**base, "email": "a@example.com"})
    second = client.post("/api/auth/register", json={**base, "email": "b@example.com"})
    assert first.status_code == 201
    assert second.status_code == 409


def test_register_validation_errors(client):
    bad_email = client.post(
        "/api/auth/register", json={"email": "not-an-email", "password": "correct-horse-battery"}
    )
    short_password = client.post(
        "/api/auth/register", json={"email": "a@example.com", "password": "short"}
    )
    bad_phone = client.post(
        "/api/auth/register",
        json={
            "email": "a@example.com",
            "password": "correct-horse-battery",
            "phone": "89991234567",
        },
    )
    assert bad_email.status_code == 422
    assert short_password.status_code == 422
    assert bad_phone.status_code == 422


def test_login_success_returns_bearer_token(client, registered_user):
    response = client.post("/api/auth/login", json=registered_user)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_is_case_insensitive_for_email(client, registered_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "DRIVER@example.com", "password": registered_user["password"]},
    )
    assert response.status_code == 200


def test_login_wrong_password_and_unknown_user_look_the_same(client, registered_user):
    wrong_password = client.post(
        "/api/auth/login", json={"email": registered_user["email"], "password": "wrong-password"}
    )
    unknown_user = client.post(
        "/api/auth/login", json={"email": "ghost@example.com", "password": "whatever-123"}
    )
    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_me_returns_profile(client, auth_headers):
    response = client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "driver@example.com"
    assert "password_hash" not in body


def test_me_requires_token(client):
    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_rejects_garbage_token(client):
    response = client.get("/api/users/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401


def test_me_rejects_expired_token(client, registered_user):
    settings = get_settings()
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_me_rejects_token_signed_with_other_key(client, registered_user):
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "x" * 40,
        algorithm="HS256",
    )
    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_me_rejects_token_of_deleted_user(client):
    settings = get_settings()
    token = jwt.encode(
        {"sub": "999", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
