import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

test_directory = Path(tempfile.mkdtemp(prefix="reee-track-tests-"))
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{test_directory / 'test.db'}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-characters"
os.environ["INITIAL_ADMIN_USERNAME"] = "admin"
os.environ["INITIAL_ADMIN_EMAIL"] = "admin@example.com"
os.environ["INITIAL_ADMIN_FULL_NAME"] = "Administrador de testes"
os.environ["INITIAL_ADMIN_PASSWORD"] = "test-admin-password"

from app.cli import seed_rbac  # noqa: E402
from app.core.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.modules.equipment.seed import seed_catalogs  # noqa: E402
from app.modules.triage.seed import seed_triage_catalogs  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_rbac(session)
        seed_catalogs(session)
        seed_triage_catalogs(session)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(database) -> TestClient:
    del database
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "test-admin-password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
