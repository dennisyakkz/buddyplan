from datetime import date
from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup

from app.services.agenda_display import agenda_event_sort_key, build_agenda_display_text
from app.services.color_palette import (
    hex_to_label,
    label_to_badge_classes,
    normalize_profile_color,
    resolve_color_label,
)
from app.services.mijnafvalwijzer import _parse_events, _parse_housenumber


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("Groen", "groen"),
        ("#3498db", "blauw"),  # legacy palette
        ("#FED7D7", "rood"),  # exact brand background
        ("#FFD0D0", "rood"),  # nearest brand color
        ("not-a-color", None),
    ],
)
def test_hex_to_label(value, expected):
    assert hex_to_label(value) == expected


def test_profile_color_falls_back_by_index():
    assert normalize_profile_color("paars") == "paars"
    assert normalize_profile_color(None, 0) == "rood"
    assert normalize_profile_color(None, 9) == "oranje"  # wraps around the 8 labels


def test_color_priority_event_then_google_then_feed():
    assert resolve_color_label(feed_color="groen", event_color="rood", google_calendar_color="blauw") == "rood"
    assert resolve_color_label(feed_color="groen", google_calendar_color="blauw") == "blauw"
    assert resolve_color_label(feed_color="groen") == "groen"
    assert resolve_color_label() is None


def test_badge_classes():
    assert label_to_badge_classes("teal") == "cal-chip agenda-badge-teal"
    assert label_to_badge_classes("magenta") == "cal-chip"


def item(title="Voetbal", start=None, end=None, source="manual"):
    return SimpleNamespace(title=title, start_time=start, end_time=end, source=source)


def feed(prefix="", show_times=False, hide_title=False):
    return SimpleNamespace(prefix=prefix, show_times=show_times, hide_title=hide_title)


def test_manual_items_always_show_times():
    assert build_agenda_display_text(item(start="10:00", end="11:00"), None) == "10:00-11:00 Voetbal"
    assert build_agenda_display_text(item(start="10:00"), None) == "10:00 Voetbal"


def test_feed_items_follow_feed_settings():
    ical = item(start="10:00", end="11:00", source="ical")
    assert build_agenda_display_text(ical, feed(prefix="School")) == "School: Voetbal"
    assert build_agenda_display_text(ical, feed(show_times=True)) == "10:00-11:00 Voetbal"
    assert build_agenda_display_text(ical, feed(prefix="Werk", show_times=True, hide_title=True)) == "Werk: 10:00-11:00"


def test_events_sort_by_start_time_with_all_day_last():
    events = [
        {"title": "B", "start_time": None},
        {"title": "C", "start_time": "09:00"},
        {"title": "A", "start_time": "08:30"},
    ]
    assert [e["title"] for e in sorted(events, key=agenda_event_sort_key)] == ["A", "C", "B"]


def test_parse_housenumber():
    assert _parse_housenumber("12") == ("12", "")
    assert _parse_housenumber(" 12a ") == ("12", "a")
    assert _parse_housenumber("12-3") == ("12-3", "")  # digits in the suffix: keep it whole


AFVAL_HTML = """
<div>
  <a class="wasteInfoIcon textDecorationNone" href="#waste-gft">
    <p class="gft">dinsdag 3 november 2026<span class="afvaldescr">Groente-, fruit- en tuinafval</span></p>
  </a>
  <a class="wasteInfoIcon textDecorationNone" href="#waste-gft">
    <p class="gft">dinsdag 3 november 2026<span class="afvaldescr">Groente-, fruit- en tuinafval</span></p>
  </a>
  <a class="wasteInfoIcon textDecorationNone" href="javascript:void(0);">
    <p class="papier">vrijdag 13 november 2026</p>
  </a>
  <a class="wasteInfoIcon textDecorationNone" href="#waste-pmd">
    <p class="pmd">onbekend formaat</p>
  </a>
</div>
"""


def test_parse_afvalwijzer_events():
    events = _parse_events(BeautifulSoup(AFVAL_HTML, "html.parser"))
    assert events == [
        {"date": date(2026, 11, 3), "waste_type": "gft", "label": "Groente-, fruit- en tuinafval"},
        {"date": date(2026, 11, 13), "waste_type": "papier", "label": "papier"},
    ]
