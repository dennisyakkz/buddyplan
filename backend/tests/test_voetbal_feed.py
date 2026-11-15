"""REQ-BE-044..046: voetbal.nl feeds (served by data.sportlink.com)."""

from datetime import date, timedelta

import pytest
from icalendar import Calendar

from app.database import SessionLocal
from app.models import PersonCalendarFeed
from app.services.dashboard_service import PersonService
from app.services.ical_sync_service import sync_feed_from_content
from app.services.voetbal_feed import detect_own_team, home_away_title, is_voetbal_calendar

OWN = "FC Voorbeeld MO15-4"
DAY = date.today() + timedelta(days=3)


def event(summary: str, day: date, organizer: str = "CN=Voetbal.nl:MAILTO:noreply@voetbal.nl") -> str:
    stamp = day.strftime("%Y%m%d")
    return (
        "BEGIN:VEVENT\r\n"
        f"UID:{summary}-{stamp}@example.test\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DTSTART;TZID=Europe/Amsterdam:{stamp}T100000\r\n"
        f"DTEND;TZID=Europe/Amsterdam:{stamp}T120000\r\n"
        f"ORGANIZER;{organizer}\r\n"
        "END:VEVENT\r\n"
    )


def feed_content(summaries: list[str], calname: str = "Voetbal.nl - persoonlijk", **kwargs) -> bytes:
    events = "".join(event(s, DAY + timedelta(days=i), **kwargs) for i, s in enumerate(summaries))
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Dexels//Navajo Integrator Adapters iCal 1.0//EN\r\n"
        f"X-WR-CALNAME:{calname}\r\n{events}END:VCALENDAR\r\n"
    ).encode()


MATCHES = [
    f"VV 't Dorp MO15-2-{OWN}",
    f"{OWN}-SV Tegenstander MO15-5",
    f"{OWN}-Kockendam MO15-1",
    f"Stadse Boys MO15-2-{OWN}",
]


# --- recognition and own-team detection --------------------------------------------------------


def test_recognises_voetbal_feeds_by_name_or_organiser():
    assert is_voetbal_calendar(Calendar.from_ical(feed_content(MATCHES)))
    by_organiser = feed_content(MATCHES, calname="Mijn agenda")
    assert is_voetbal_calendar(Calendar.from_ical(by_organiser))
    other = feed_content(["Hockey"], calname="Hockey", organizer="CN=Club:MAILTO:info@example.test")
    assert not is_voetbal_calendar(Calendar.from_ical(other))


def test_own_team_is_the_name_in_most_matches():
    assert detect_own_team(MATCHES) == OWN
    # Not in every title: a cup match without the own team does not matter.
    assert detect_own_team([*MATCHES, "Stadse Boys MO15-2-Kockendam MO15-1"]) == OWN
    assert detect_own_team([]) is None


def test_home_and_away_titles():
    assert home_away_title(f"{OWN}-SV Tegenstander MO15-5", OWN) == "Voetbal thuis tegen SV Tegenstander MO15-5"
    assert home_away_title(f"VV 't Dorp MO15-2-{OWN}", OWN) == "Voetbal uit tegen VV 't Dorp MO15-2"
    assert home_away_title(f"VV 't Dorp MO15-2 - {OWN.lower()}", OWN) == "Voetbal uit tegen VV 't Dorp MO15-2"
    assert home_away_title("Training", OWN) is None
    assert home_away_title("Stadse Boys MO15-2-Kockendam MO15-1", OWN) is None
    assert home_away_title(f"{OWN}-SV X", "") is None


# --- end to end through sync and API -----------------------------------------------------------


@pytest.fixture
def voetbal_feed(make_user):
    person, headers = make_user("Speler")
    db = SessionLocal()
    try:
        feed = PersonService(db).add_feed(person["id"], "https://data.example.test/ical-person?token=x", "Voetbal")
        sync_feed_from_content(db, feed.id, feed_content([*MATCHES, "Training"]))
        return feed.id, person, headers
    finally:
        db.close()


def stored_feed(feed_id: int) -> PersonCalendarFeed:
    db = SessionLocal()
    try:
        return db.get(PersonCalendarFeed, feed_id)
    finally:
        db.close()


def shown_titles(client, headers, person_id: int) -> set[str]:
    end = DAY + timedelta(days=len(MATCHES) + 1)
    items = client.get(f"/api/mobile/calendar?start={DAY.isoformat()}&end={end.isoformat()}", headers=headers).json()
    return {i["title"] for i in items if i["person_id"] == person_id}


def update(client, headers, feed_id, **fields):
    current = next(f for f in client.get("/api/me", headers=headers).json()["feeds"] if f["id"] == feed_id)
    body = {k: current[k] for k in ("url", "label", "sync_interval_minutes", "prefix", "color", "show_times")}
    response = client.put(f"/api/me/feeds/{feed_id}", headers=headers, json={**body, **fields})
    assert response.status_code == 200, response.text
    return response.json()


def test_sync_marks_the_feed_and_fills_the_own_team(voetbal_feed):
    feed_id, _person, _headers = voetbal_feed
    feed = stored_feed(feed_id)
    assert feed.is_voetbal
    assert feed.home_away_mode
    assert feed.own_team == OWN


def test_titles_follow_the_home_away_mode(client, voetbal_feed):
    feed_id, person, headers = voetbal_feed
    assert shown_titles(client, headers, person["id"]) == {
        "Voetbal uit tegen VV 't Dorp MO15-2",
        "Voetbal thuis tegen SV Tegenstander MO15-5",
        "Voetbal thuis tegen Kockendam MO15-1",
        "Voetbal uit tegen Stadse Boys MO15-2",
        "Training",
    }

    data = update(client, headers, feed_id, home_away_mode=False)
    assert data["is_voetbal"] and data["home_away_mode"] is False
    assert shown_titles(client, headers, person["id"]) == {*MATCHES, "Training"}


def test_prefix_still_applies(client, voetbal_feed):
    feed_id, person, headers = voetbal_feed
    update(client, headers, feed_id, prefix="Sam")
    assert "Sam: Voetbal thuis tegen Kockendam MO15-1" in shown_titles(client, headers, person["id"])


def test_edited_own_team_is_kept_on_the_next_sync(client, voetbal_feed):
    feed_id, person, headers = voetbal_feed
    data = update(client, headers, feed_id, own_team="Stadse Boys MO15-2")
    assert data["own_team"] == "Stadse Boys MO15-2"
    assert "Voetbal thuis tegen FC Voorbeeld MO15-4" in shown_titles(client, headers, person["id"])

    db = SessionLocal()
    try:
        sync_feed_from_content(db, feed_id, feed_content(MATCHES))
    finally:
        db.close()
    assert stored_feed(feed_id).own_team == "Stadse Boys MO15-2"


def test_dashboard_shows_the_shaped_title(client, voetbal_feed):
    _feed_id, person, headers = voetbal_feed
    monday = DAY - timedelta(days=DAY.weekday())
    end = monday + timedelta(weeks=2, days=-1)
    weeks = client.get(
        f"/api/dashboard?start_date={monday.isoformat()}&end_date={end.isoformat()}", headers=headers
    ).json()["weeks"]
    titles = {
        event["title"]
        for week in weeks
        for calendar in week["calendar"]
        if calendar.get("person_id") == person["id"] or calendar.get("name") == person["name"]
        for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
        for event in calendar.get(day, [])
    }
    assert "Voetbal thuis tegen SV Tegenstander MO15-5" in titles


def test_regular_feeds_are_not_changed(client, make_user):
    person, headers = make_user("Gewoon")
    db = SessionLocal()
    try:
        feed = PersonService(db).add_feed(person["id"], "https://example.test/school.ics", "School")
        content = feed_content([f"{OWN}-SV Tegenstander MO15-5"], calname="School", organizer="CN=School:MAILTO:a@b.c")
        sync_feed_from_content(db, feed.id, content)
        assert not db.get(PersonCalendarFeed, feed.id).is_voetbal
    finally:
        db.close()
    assert shown_titles(client, headers, person["id"]) == {f"{OWN}-SV Tegenstander MO15-5"}


def test_adding_a_feed_recognises_it_immediately(client, make_user, monkeypatch):
    import app.routers.api as api

    monkeypatch.setattr(api, "validate_ical_feed", lambda url: feed_content(MATCHES))
    person, headers = make_user("Nieuw")
    response = client.post(
        "/api/me/feeds",
        headers=headers,
        json={"url": "webcal://data.example.test/ical-person?token=x", "label": "Voetbal"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["is_voetbal"] and data["home_away_mode"] and data["own_team"] == OWN
    assert "Voetbal thuis tegen Kockendam MO15-1" in shown_titles(client, headers, person["id"])
