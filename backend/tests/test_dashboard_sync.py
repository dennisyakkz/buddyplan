"""The wall tablet polls /api/dashboard/etag every minute and only reloads when it changes."""

from datetime import date, timedelta

import pytest

TODAY = date.today()


@pytest.fixture
def planner(client, admin_headers, make_user):
    """A user who manages their own tasks and agenda."""
    person, headers = make_user("Planner")
    response = client.put(
        f"/api/admin/users/{person['id']}/task-managers",
        headers=admin_headers,
        json={"tasks_enabled": True, "manager_ids": [person["id"]]},
    )
    assert response.status_code == 200, response.text
    return person, headers


def etag(client, headers) -> str:
    return client.get("/api/dashboard/etag", headers=headers).json()["etag"]


def assert_etag_changes(client, headers, action):
    before = etag(client, headers)
    response = action()
    assert response.status_code == 200, response.text
    assert etag(client, headers) != before
    return response


def test_every_task_change_changes_the_etag(client, planner):
    person, headers = planner

    def create(title):
        return client.post(
            f"/api/tasks?person_id={person['id']}",
            headers=headers,
            json={"title": title, "anchor_date": TODAY.isoformat()},
        )

    first = assert_etag_changes(client, headers, lambda: create("Tanden poetsen")).json()
    second = create("Bed opmaken").json()

    assert_etag_changes(
        client,
        headers,
        lambda: client.put(
            f"/api/tasks/{first['id']}",
            headers=headers,
            json={"title": "Flossen", "anchor_date": TODAY.isoformat()},
        ),
    )

    def reorder(task_ids):
        return client.put(
            f"/api/tasks/reorder?person_id={person['id']}",
            headers=headers,
            json={"date": TODAY.isoformat(), "task_ids": task_ids},
        )

    assert_etag_changes(client, headers, lambda: reorder([second["id"], first["id"]]))
    # Reordering again only updates existing order rows: the row count stays the same.
    assert_etag_changes(client, headers, lambda: reorder([first["id"], second["id"]]))

    assert_etag_changes(
        client,
        headers,
        lambda: client.put(
            "/api/tasks/move",
            headers=headers,
            json={
                "task_id": first["id"],
                "from_date": TODAY.isoformat(),
                "to_date": (TODAY + timedelta(days=1)).isoformat(),
            },
        ),
    )
    assert_etag_changes(
        client,
        headers,
        lambda: client.post(f"/api/tasks/{second['id']}/complete?date={TODAY.isoformat()}", headers=headers),
    )
    assert_etag_changes(client, headers, lambda: client.delete(f"/api/tasks/{first['id']}", headers=headers))


def test_every_agenda_change_changes_the_etag(client, planner):
    person, headers = planner

    created = assert_etag_changes(
        client,
        headers,
        lambda: client.post(
            "/api/agenda",
            headers=headers,
            json={"person_id": person["id"], "title": "Zwemles", "anchor_date": TODAY.isoformat()},
        ),
    ).json()
    assert_etag_changes(
        client,
        headers,
        lambda: client.put(f"/api/agenda/{created['id']}", headers=headers, json={"start_time": "16:00"}),
    )
    assert_etag_changes(client, headers, lambda: client.delete(f"/api/agenda/{created['id']}", headers=headers))


def test_changing_a_profile_color_changes_the_etag(client, planner):
    person, headers = planner
    assert_etag_changes(
        client,
        headers,
        lambda: client.put("/api/me", headers=headers, json={"name": person["name"], "profile_color": "teal"}),
    )


def test_dashboard_range_is_limited_to_twelve_weeks(client, planner):
    """The tablet must split its refresh into requests of at most 12 weeks."""
    _person, headers = planner
    monday = TODAY - timedelta(days=TODAY.weekday())

    def dashboard(weeks):
        end = monday + timedelta(weeks=weeks - 1, days=6)
        return client.get(f"/api/dashboard?start_date={monday.isoformat()}&end_date={end.isoformat()}", headers=headers)

    assert dashboard(12).status_code == 200
    assert len(dashboard(12).json()["weeks"]) == 12
    assert dashboard(13).status_code == 400
