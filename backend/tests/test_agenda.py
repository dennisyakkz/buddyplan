from datetime import date, timedelta

import pytest

TODAY = date.today()


@pytest.fixture
def agenda_owner(client, admin_headers, make_user):
    """A user who may manage their own agenda."""
    person, headers = make_user("Agenda")
    response = client.put(
        f"/api/admin/users/{person['id']}/agenda-managers",
        headers=admin_headers,
        json={"manager_ids": [person["id"]]},
    )
    assert response.status_code == 200, response.text
    return person, headers


def create_item(client, headers, person_id, **fields):
    payload = {"person_id": person_id, "title": "Zwemles", "anchor_date": TODAY.isoformat(), **fields}
    return client.post("/api/agenda", headers=headers, json=payload)


def test_requires_login(client):
    assert client.get(f"/api/agenda?person_id=1&date={TODAY}").status_code == 401


def test_users_manage_their_own_agenda_but_not_someone_elses(client, make_user):
    person, headers = make_user()
    other, _ = make_user()
    assert client.get(f"/api/agenda/access?person_id={person['id']}", headers=headers).json() == {"can_manage": True}
    assert client.get(f"/api/agenda/access?person_id={other['id']}", headers=headers).json() == {"can_manage": False}
    assert create_item(client, headers, other["id"]).status_code == 403


def test_agenda_lifecycle(client, agenda_owner):
    person, headers = agenda_owner
    assert client.get(f"/api/agenda/access?person_id={person['id']}", headers=headers).json() == {"can_manage": True}

    created = create_item(client, headers, person["id"], start_time="16:00", end_time="17:00")
    assert created.status_code == 200, created.text
    item = created.json()
    assert (item["title"], item["start_time"], item["end_time"]) == ("Zwemles", "16:00", "17:00")

    listed = client.get(f"/api/agenda?person_id={person['id']}&date={TODAY}", headers=headers).json()
    assert [i["id"] for i in listed] == [item["id"]]

    updated = client.put(
        f"/api/agenda/{item['id']}",
        headers=headers,
        json={"title": "Zwemles diploma B", "start_time": ""},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Zwemles diploma B"
    assert updated.json()["start_time"] is None  # empty string clears the time

    assert client.delete(f"/api/agenda/{item['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/agenda?person_id={person['id']}&date={TODAY}", headers=headers).json() == []
    assert client.delete(f"/api/agenda/{item['id']}", headers=headers).status_code == 404


def test_weekly_item_shows_up_on_following_weeks_only(client, agenda_owner):
    person, headers = agenda_owner
    create_item(client, headers, person["id"], title="Muziekles", repeat_type="weekly")

    def titles_on(day):
        response = client.get(f"/api/agenda?person_id={person['id']}&date={day}", headers=headers)
        return [i["title"] for i in response.json()]

    assert titles_on(TODAY + timedelta(days=7)) == ["Muziekles"]
    assert titles_on(TODAY + timedelta(days=1)) == []
    assert titles_on(TODAY - timedelta(days=7)) == []


def test_mobile_calendar_expands_recurring_items(client, agenda_owner):
    person, headers = agenda_owner
    create_item(client, headers, person["id"], title="Ochtendrun", repeat_type="daily", start_time="07:00")

    start, end = TODAY, TODAY + timedelta(days=2)
    response = client.get(f"/api/mobile/calendar?start={start}&end={end}", headers=headers)
    assert response.status_code == 200, response.text
    mine = [e for e in response.json() if e["person_id"] == person["id"]]
    assert [e["date"] for e in mine] == [(TODAY + timedelta(days=i)).isoformat() for i in range(3)]
    assert all(e["start_time"] == "07:00" and e["source"] == "manual" for e in mine)


def test_mobile_calendar_rejects_large_ranges(client, admin_headers):
    end = TODAY + timedelta(days=181)
    response = client.get(f"/api/mobile/calendar?start={TODAY}&end={end}", headers=admin_headers)
    assert response.status_code == 400
