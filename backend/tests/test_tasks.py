from datetime import date

import pytest

TODAY = date.today().isoformat()


@pytest.fixture
def task_owner(client, admin_headers, make_user):
    """A user with tasks enabled who manages their own tasks."""
    person, headers = make_user("Taakeigenaar")
    response = client.put(
        f"/api/admin/users/{person['id']}/task-managers",
        headers=admin_headers,
        json={"tasks_enabled": True, "manager_ids": [person["id"]]},
    )
    assert response.status_code == 200, response.text
    return person, headers


def test_cannot_create_tasks_without_manager_rights(client, make_user):
    person, headers = make_user()
    response = client.post(
        f"/api/tasks?person_id={person['id']}",
        headers=headers,
        json={"title": "Afwassen", "anchor_date": TODAY},
    )
    assert response.status_code == 403


def test_task_lifecycle(client, task_owner):
    person, headers = task_owner

    created = client.post(
        f"/api/tasks?person_id={person['id']}",
        headers=headers,
        json={"title": "Kliko buitenzetten", "anchor_date": TODAY},
    )
    assert created.status_code == 200, created.text
    task = created.json()
    assert task["person_id"] == person["id"]

    listed = client.get(f"/api/tasks?date={TODAY}&person_id={person['id']}", headers=headers).json()
    assert [t["id"] for t in listed] == [task["id"]]
    assert listed[0]["completed"] is False

    assert client.post(f"/api/tasks/{task['id']}/complete?date={TODAY}", headers=headers).status_code == 200
    listed = client.get(f"/api/tasks?date={TODAY}&person_id={person['id']}", headers=headers).json()
    assert listed[0]["completed"] is True

    assert client.delete(f"/api/tasks/{task['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/tasks/{task['id']}", headers=headers).status_code == 404


def test_creating_a_task_changes_dashboard_etag(client, task_owner):
    person, headers = task_owner
    before = client.get("/api/dashboard/etag", headers=headers).json()["etag"]
    client.post(
        f"/api/tasks?person_id={person['id']}",
        headers=headers,
        json={"title": "Planten water geven", "anchor_date": TODAY},
    )
    after = client.get("/api/dashboard/etag", headers=headers).json()["etag"]
    assert before != after
