from datetime import date
from types import SimpleNamespace

import pytest
from icalendar import Calendar

from app.services import ical_validation
from app.services.ical_sync_service import _items_from_calendar

FEED = SimpleNamespace(id=1, person_id=7)


def parse(*event_lines: str):
    body = "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "BEGIN:VEVENT", *event_lines, "END:VEVENT", "END:VCALENDAR"])
    return _items_from_calendar(FEED, Calendar.from_ical(body.encode()))


def test_single_event_with_times_in_amsterdam_time():
    [item] = parse("UID:a", "SUMMARY:Tandarts", "DTSTART:20261102T140000Z", "DTEND:20261102T150000Z")
    assert item.title == "Tandarts"
    assert item.repeat_type == "once"
    assert item.anchor_date == date(2026, 11, 2)
    assert (item.start_time, item.end_time) == ("15:00", "16:00")  # UTC+1 in November
    assert item.person_id == 7
    assert item.feed_id == 1
    assert item.source == "ical"
    assert item.external_uid == "a"


def test_all_day_event_has_no_times():
    [item] = parse("UID:b", "SUMMARY:Studiedag", "DTSTART;VALUE=DATE:20261105", "DTEND;VALUE=DATE:20261106")
    assert item.anchor_date == date(2026, 11, 5)
    assert item.start_time is None
    assert item.end_time is None


def test_late_utc_time_lands_on_next_local_day():
    [item] = parse("UID:c", "SUMMARY:Nachtdienst", "DTSTART:20261102T233000Z")
    assert item.anchor_date == date(2026, 11, 3)
    assert item.start_time == "00:30"


@pytest.mark.parametrize(
    ("rrule", "repeat_type", "weekdays"),
    [
        ("FREQ=DAILY", "daily", []),
        ("FREQ=WEEKLY", "weekly", []),
        ("FREQ=WEEKLY;BYDAY=MO", "weekly", [0]),
        ("FREQ=WEEKLY;BYDAY=MO,WE,FR", "weekdays", [0, 2, 4]),
        ("FREQ=WEEKLY;INTERVAL=2;BYDAY=MO", "biweekly", [0]),
        ("FREQ=MONTHLY;BYMONTHDAY=2", "once", []),
    ],
)
def test_recurrence_rules(rrule, repeat_type, weekdays):
    [item] = parse("UID:d", "SUMMARY:Zwemles", "DTSTART:20261102T150000Z", f"RRULE:{rrule}")
    assert item.repeat_type == repeat_type
    assert item.get_weekdays() == weekdays
    assert item.end_date is None


def test_recurrence_until_sets_end_date():
    [item] = parse(
        "UID:e",
        "SUMMARY:Zwemles",
        "DTSTART:20261102T150000Z",
        "RRULE:FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261231T000000Z",
    )
    assert item.repeat_type == "weekdays"
    assert item.end_date == date(2026, 12, 31)


def test_recurrence_until_as_date():
    [item] = parse("UID:f", "SUMMARY:Training", "DTSTART;VALUE=DATE:20261102", "RRULE:FREQ=DAILY;UNTIL=20261110")
    assert item.end_date == date(2026, 11, 10)


def test_event_without_start_is_skipped():
    assert parse("UID:g", "SUMMARY:Zonder datum") == []


def test_normalize_ical_url():
    assert ical_validation.normalize_ical_url(" webcal://example.com/a.ics ") == "https://example.com/a.ics"
    assert ical_validation.normalize_ical_url("https://example.com/a.ics") == "https://example.com/a.ics"


class FakeResponse:
    def __init__(self, status_code: int, content: bytes = b""):
        self.status_code = status_code
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_fetch_retries_full_after_empty_304(monkeypatch):
    calls = []

    def fake_get(url, headers, timeout):
        calls.append(headers.get("If-None-Match"))
        return FakeResponse(304) if len(calls) == 1 else FakeResponse(200, b"BEGIN:VCALENDAR")

    monkeypatch.setattr(ical_validation.requests, "get", fake_get)
    assert ical_validation.fetch_ical_content("https://x/a.ics", etag='"1"') == b"BEGIN:VCALENDAR"
    assert calls == ['"1"', None]


def test_fetch_raises_dutch_error_when_server_keeps_returning_nothing(monkeypatch):
    monkeypatch.setattr(ical_validation.requests, "get", lambda url, headers, timeout: FakeResponse(304))
    with pytest.raises(ValueError, match="geen data"):
        ical_validation.fetch_ical_content("https://x/a.ics", force_full=True)
