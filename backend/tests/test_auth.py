import pytest

from tests.conftest import ADMIN_USERNAME


def test_api_requires_login(client):
    response = client.get("/api/dashboard/etag")
    assert response.status_code == 401


def test_login_with_wrong_password_is_rejected(client):
    response = client.post(
        "/api/auth/login",
        json={"username": ADMIN_USERNAME, "password": "fout", "device_id": "test-device"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Onjuiste inloggegevens"


def test_invalid_bearer_token_is_rejected(client):
    response = client.get("/api/dashboard/etag", headers={"Authorization": "Bearer niet-geldig"})
    assert response.status_code == 401


def test_bearer_token_grants_access(client, admin_headers):
    response = client.get("/api/dashboard/etag", headers=admin_headers)
    assert response.status_code == 200
    assert "etag" in response.json()


def test_non_admin_cannot_use_admin_endpoints(client, make_user):
    _, headers = make_user()
    response = client.get("/api/admin/users", headers=headers)
    assert response.status_code == 403


def test_duplicate_username_is_rejected(client, admin_headers, make_user):
    person, _ = make_user()
    response = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={"username": person["username"], "name": "Dubbel"},
    )
    assert response.status_code == 400


@pytest.mark.xfail(reason="Known bug: duplicate display name raises IntegrityError (500) instead of a 400", strict=True)
def test_duplicate_name_is_rejected(client, admin_headers, make_user):
    person, _ = make_user()
    response = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={"username": "ander-account", "name": person["name"]},
    )
    assert response.status_code == 400
