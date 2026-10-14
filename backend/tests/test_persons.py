DUPLICATE_NAME = "Er bestaat al een gebruiker met deze naam"


def test_admin_create_user_with_existing_name_is_rejected(client, admin_headers, make_user):
    person, _ = make_user()
    response = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={"username": "ander-account", "name": person["name"]},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == DUPLICATE_NAME


def test_create_person_with_existing_name_is_rejected(client, admin_headers, make_user):
    person, _ = make_user()
    response = client.post("/api/persons", headers=admin_headers, json={"name": person["name"]})
    assert response.status_code == 400
    assert response.json()["detail"] == DUPLICATE_NAME


def test_admin_rename_to_existing_name_is_rejected(client, admin_headers, make_user):
    first, _ = make_user()
    second, _ = make_user()
    response = client.put(
        f"/api/admin/users/{second['id']}",
        headers=admin_headers,
        json={"username": second["username"], "name": first["name"]},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == DUPLICATE_NAME


def test_update_person_to_existing_name_is_rejected(client, admin_headers, make_user):
    first, _ = make_user()
    second, _ = make_user()
    response = client.put(
        f"/api/persons/{second['id']}",
        headers=admin_headers,
        json={"name": first["name"], "can_login": True},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == DUPLICATE_NAME


def test_rename_me_to_existing_name_changes_nothing(client, make_user):
    other, _ = make_user()
    me, headers = make_user()
    response = client.put(
        "/api/me",
        headers=headers,
        json={"name": other["name"], "email": "nieuw@example.com"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == DUPLICATE_NAME

    # The rejected request must not have saved its other fields either
    current = client.get("/api/me", headers=headers).json()
    assert current["name"] == me["name"]
    assert current["email"] is None


def test_keeping_your_own_name_is_allowed(client, make_user):
    me, headers = make_user()
    response = client.put("/api/me", headers=headers, json={"name": me["name"], "email": "ik@example.com"})
    assert response.status_code == 200
    assert response.json()["email"] == "ik@example.com"
