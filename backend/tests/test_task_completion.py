"""REQ-BE-024: who may mark a task occurrence as done."""

import uuid
from datetime import date

import pytest

TODAY = date.today().isoformat()


@pytest.fixture
def child_task(client, admin_headers, make_user):
    """A task of a child who may not manage their own tasks; a parent manages them."""
    child, child_headers = make_user("Kind")
    parent, parent_headers = make_user("Ouder")
    response = client.put(
        f"/api/admin/users/{child['id']}/task-managers",
        headers=admin_headers,
        json={"tasks_enabled": True, "manager_ids": [parent["id"]]},
    )
    assert response.status_code == 200, response.text
    task = client.post(
        f"/api/tasks?person_id={child['id']}",
        headers=parent_headers,
        json={"title": "Tanden poetsen", "anchor_date": TODAY},
    ).json()
    return task, child, child_headers, parent_headers


def complete(client, task, headers):
    return client.post(f"/api/tasks/{task['id']}/complete?date={TODAY}", headers=headers)


def is_completed(client, task, child, headers) -> bool:
    listed = client.get(f"/api/tasks?date={TODAY}&person_id={child['id']}", headers=headers).json()
    return next(t for t in listed if t["id"] == task["id"])["completed"]


def test_the_person_completes_their_own_task_without_manager_rights(client, child_task):
    task, child, child_headers, parent_headers = child_task
    assert complete(client, task, child_headers).status_code == 200
    assert is_completed(client, task, child, parent_headers)
    # Completing does not grant other task rights.
    edit = client.put(f"/api/tasks/{task['id']}", headers=child_headers, json={"title": "X", "anchor_date": TODAY})
    assert edit.status_code == 403


def test_a_task_manager_completes_the_task(client, child_task):
    task, child, _child_headers, parent_headers = child_task
    assert complete(client, task, parent_headers).status_code == 200
    assert is_completed(client, task, child, parent_headers)


def test_an_administrator_completes_any_task(client, child_task, admin_headers):
    task, child, _child_headers, parent_headers = child_task
    assert complete(client, task, admin_headers).status_code == 200
    assert is_completed(client, task, child, parent_headers)


def test_a_wall_tablet_completes_any_task(client, child_task, make_user):
    task, child, _child_headers, parent_headers = child_task
    other, _ = make_user("Tabletaccount")
    # make_user logs in as a phone; log in again as a wall tablet.
    response = client.post(
        "/api/auth/login",
        json={
            "username": other["username"],
            "password": "geheim-123",
            "device_id": f"tablet-{uuid.uuid4()}",
            "device_type": "dashboard",
        },
    )
    assert response.status_code == 200, response.text
    tablet_headers = {"Authorization": f"Bearer {response.json()['token']}"}
    assert complete(client, task, tablet_headers).status_code == 200
    assert is_completed(client, task, child, parent_headers)


def test_someone_else_on_a_phone_may_not_complete_the_task(client, child_task, make_user):
    task, child, _child_headers, parent_headers = child_task
    _other, other_headers = make_user("Buurman")
    response = complete(client, task, other_headers)
    assert response.status_code == 403
    assert "af te vinken" in response.json()["detail"]
    assert not is_completed(client, task, child, parent_headers)
