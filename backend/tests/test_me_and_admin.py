import uuid

from tests.conftest import login


def test_me_returns_the_logged_in_user(client, make_user):
    person, headers = make_user("Profiel")
    me = client.get("/api/me", headers=headers).json()
    assert me["id"] == person["id"]
    assert me["name"] == person["name"]


def test_update_me_changes_name_and_color(client, make_user):
    person, headers = make_user()
    new_name = f"Nieuwe naam {uuid.uuid4().hex[:6]}"
    response = client.put("/api/me", headers=headers, json={"name": new_name, "profile_color": "teal"})
    assert response.status_code == 200, response.text
    assert response.json()["name"] == new_name
    assert response.json()["profile_color"] == "teal"


def test_update_me_rejects_empty_or_taken_name(client, make_user):
    other, _ = make_user()
    _, headers = make_user()
    assert client.put("/api/me", headers=headers, json={"name": "  "}).status_code == 400
    assert client.put("/api/me", headers=headers, json={"name": other["name"]}).status_code == 400


def test_change_password(client, make_user):
    person, headers = make_user()
    bad = client.put("/api/me/password", headers=headers, json={"password": "nieuw-1", "password_confirm": "anders"})
    assert bad.status_code == 400
    short = client.put("/api/me/password", headers=headers, json={"password": "abc", "password_confirm": "abc"})
    assert short.status_code == 400

    ok = client.put(
        "/api/me/password",
        headers=headers,
        json={"password": "nieuw-wachtwoord", "password_confirm": "nieuw-wachtwoord"},
    )
    assert ok.status_code == 200
    login(client, person["username"], "nieuw-wachtwoord")


def test_wrong_password_and_unknown_user_are_rejected(client, make_user):
    person, _ = make_user()
    for username, password in [(person["username"], "fout"), ("bestaat-niet", "geheim-123")]:
        response = client.post(
            "/api/auth/login", json={"username": username, "password": password, "device_id": "test-device"}
        )
        assert response.status_code == 401


def test_revoking_a_device_logs_it_out(client, make_user):
    person, headers = make_user()
    second = login(client, person["username"], "geheim-123")

    devices = client.get("/api/me/devices", headers=headers).json()
    assert len(devices) == 2
    other = next(d for d in devices if not d.get("is_current"))

    assert client.delete(f"/api/me/devices/{other['device_id']}", headers=headers).status_code == 200
    assert client.get("/api/me", headers=second).status_code == 401
    assert client.get("/api/me", headers=headers).status_code == 200
    assert client.delete("/api/me/devices/bestaat-niet", headers=headers).status_code == 404


def test_admin_endpoints_are_closed_to_regular_users(client, make_user):
    _, headers = make_user()
    assert client.get("/api/admin/users", headers=headers).status_code == 403
    assert client.post("/api/admin/users", headers=headers, json={"username": "x", "name": "x"}).status_code == 403
    assert client.get("/api/admin/dashboard-upgrade", headers=headers).status_code == 403


def test_admin_can_delete_a_user(client, admin_headers, make_user):
    person, headers = make_user()
    assert client.delete(f"/api/admin/users/{person['id']}", headers=admin_headers).status_code == 200
    assert client.get(f"/api/admin/users/{person['id']}", headers=admin_headers).status_code == 404
    assert client.get("/api/me", headers=headers).status_code == 401


def test_dashboard_lists_users_and_has_a_stable_etag(client, make_user):
    person, headers = make_user("Dashboard")
    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    assert person["name"] in dashboard.text

    first = client.get("/api/dashboard/etag", headers=headers).json()["etag"]
    assert client.get("/api/dashboard/etag", headers=headers).json()["etag"] == first
