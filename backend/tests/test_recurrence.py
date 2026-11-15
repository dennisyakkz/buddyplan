from datetime import date

import pytest

from app.services.recurrence import (
    format_dutch_date,
    format_dutch_day,
    monday_of_week,
    occurs_on_date,
    week_dates,
)

MONDAY = date(2026, 11, 2)
WEDNESDAY = date(2026, 11, 4)


def test_monday_of_week_and_week_dates():
    assert monday_of_week(date(2026, 11, 8)) == MONDAY  # Sunday belongs to the week before
    assert monday_of_week(MONDAY) == MONDAY
    week = week_dates(WEDNESDAY)
    assert week[0] == MONDAY
    assert week[-1] == date(2026, 11, 8)
    assert len(week) == 7


def test_dutch_formatting():
    assert format_dutch_date(date(2026, 3, 5)) == "5 Maart"
    assert format_dutch_day(MONDAY) == "Maandag"
    assert format_dutch_day(date(2026, 11, 8)) == "Zondag"


@pytest.mark.parametrize(
    ("target", "expected"),
    [(MONDAY, True), (date(2026, 11, 3), False), (date(2026, 11, 9), False)],
)
def test_once(target, expected):
    assert occurs_on_date("once", [], MONDAY, None, target) is expected


def test_daily_respects_anchor_and_end_date():
    end = date(2026, 11, 10)
    assert occurs_on_date("daily", [], MONDAY, end, date(2026, 11, 1)) is False
    assert occurs_on_date("daily", [], MONDAY, end, MONDAY) is True
    assert occurs_on_date("daily", [], MONDAY, end, end) is True
    assert occurs_on_date("daily", [], MONDAY, end, date(2026, 11, 11)) is False


def test_weekly_uses_anchor_weekday():
    assert occurs_on_date("weekly", [], MONDAY, None, date(2026, 11, 9)) is True
    assert occurs_on_date("weekly", [], MONDAY, None, date(2026, 11, 10)) is False


def test_biweekly_skips_odd_weeks():
    assert occurs_on_date("biweekly", [], MONDAY, None, date(2026, 11, 9)) is False
    assert occurs_on_date("biweekly", [], MONDAY, None, date(2026, 11, 16)) is True
    assert occurs_on_date("biweekly", [], MONDAY, None, date(2026, 10, 19)) is False  # before anchor


def test_weekdays_uses_listed_days():
    days = [0, 2]  # Monday, Wednesday
    assert occurs_on_date("weekdays", days, MONDAY, None, WEDNESDAY) is True
    assert occurs_on_date("weekdays", days, MONDAY, None, date(2026, 11, 5)) is False


def test_without_anchor_or_unknown_type_never_occurs():
    assert occurs_on_date("daily", [], None, None, MONDAY) is False
    assert occurs_on_date("monthly", [], MONDAY, None, MONDAY) is False
