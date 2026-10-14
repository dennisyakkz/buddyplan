import atexit
import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest

# app.main builds the app (migrations, seed) at import time, so the environment
# must point at a throwaway database before anything from `app` is imported.
_TMP_DIR = Path(tempfile.mkdtemp(prefix="buddyplan-tests-"))
atexit.register(shutil.rmtree, _TMP_DIR, ignore_errors=True)
os.environ.update(
    {
        "BUDDYPLAN_DEV": "1",
        "DATA_DIR": str(_TMP_DIR),
        "DATABASE_PATH": str(_TMP_DIR / "test.db"),
        "BUDDYPLAN_ADMIN_USERNAME": "admin",
        "BUDDYPLAN_ADMIN_PASSWORD": "admin-wachtwoord",
        "BUDDYPLAN_ADMIN_NAME": "Beheerder",
    }
)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ADMIN_USERNAME = os.environ["BUDDYPLAN_ADMIN_USERNAME"]
ADMIN_PASSWORD = os.environ["BUDDYPLAN_ADMIN_PASSWORD"]


@pytest.fixture(scope="session")
def client() -> TestClient:
    # Not used as a context manager, so the lifespan (APScheduler) never starts
    return TestClient(app)


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password, "device_id": f"test-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture(scope="session")
def admin_headers(client: TestClient) -> dict[str, str]:
    return login(client, ADMIN_USERNAME, ADMIN_PASSWORD)


@pytest.fixture
def make_user(client: TestClient, admin_headers: dict[str, str]):
    """Create a login-capable, non-admin user; returns (person dict, auth headers)."""

    def _make(name: str = "Gebruiker"):
        suffix = uuid.uuid4().hex[:8]
        username = f"user-{suffix}"
        password = "geheim-123"
        response = client.post(
            "/api/admin/users",
            headers=admin_headers,
            json={
                "username": username,
                "name": f"{name} {suffix}",  # persons.name is unique
                "can_login": True,
                "password": password,
                "password_confirm": password,
            },
        )
        assert response.status_code == 200, response.text
        return response.json(), login(client, username, password)

    return _make
