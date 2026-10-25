import os

# Переменные должны быть заданы ДО импорта приложения (настройки читаются при импорте).
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-0123456789"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def session_factory():
    """Чистая in-memory SQLite на каждый тест."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client):
    payload = {"email": "driver@example.com", "password": "correct-horse-battery"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    return payload


@pytest.fixture()
def auth_headers(client, registered_user):
    response = client.post("/api/auth/login", json=registered_user)
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
