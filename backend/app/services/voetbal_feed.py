"""voetbal.nl iCal feeds: recognition, own-team detection and home/away titles.

REQ-BE-044, REQ-BE-045 and REQ-BE-046. The feeds are served by data.sportlink.com; match titles
look like "VV 't Dorp MO15-2-FC Voorbeeld MO15-4" (home team, '-', away team), and team names contain
hyphens themselves, so a title is never split blindly on '-'.
"""

from collections import Counter

from icalendar import Calendar

MARKER = "voetbal.nl"


def is_voetbal_calendar(calendar: Calendar) -> bool:
    """True when the calendar name or an event organiser names Voetbal.nl."""
    if MARKER in str(calendar.get("X-WR-CALNAME", "")).lower():
        return True
    for event in calendar.walk("VEVENT"):
        organizer = event.get("ORGANIZER")
        if organizer is None:
            continue
        common_name = str(getattr(organizer, "params", {}).get("CN", ""))
        if MARKER in f"{common_name} {organizer}".lower():
            return True
    return False


def detect_own_team(titles: list[str]) -> str | None:
    """The team name found in the most match titles; the longest one on a tie."""
    counts: Counter[str] = Counter()
    for title in titles:
        candidates: set[str] = set()
        for index, char in enumerate(title):
            if char != "-":
                continue
            for side in (title[:index], title[index + 1 :]):
                side = side.strip()
                if side:
                    candidates.add(side)
        counts.update(candidates)
    if not counts:
        return None
    team, _count = max(counts.items(), key=lambda entry: (entry[1], len(entry[0])))
    return team


def home_away_title(title: str, own_team: str) -> str | None:
    """'Voetbal thuis/uit tegen <opponent>', or None when the title is no match of own_team."""
    title = title.strip()
    team = own_team.strip()
    if not team:
        return None
    folded_title, folded_team = title.casefold(), team.casefold()

    if folded_title.startswith(folded_team):
        rest = title[len(team) :].lstrip()
        if rest.startswith("-") and rest[1:].strip():
            return f"Voetbal thuis tegen {rest[1:].strip()}"

    if folded_title.endswith(folded_team):
        rest = title[: len(title) - len(team)].rstrip()
        if rest.endswith("-") and rest[:-1].strip():
            return f"Voetbal uit tegen {rest[:-1].strip()}"

    return None


def apply_feed_detection(feed, calendar: Calendar) -> None:
    """Mark the feed as voetbal.nl and fill an empty own team (called on every full sync)."""
    feed.is_voetbal = is_voetbal_calendar(calendar)
    if feed.is_voetbal and not (feed.own_team or "").strip():
        titles = [str(event.get("SUMMARY", "")) for event in calendar.walk("VEVENT")]
        feed.own_team = detect_own_team([t for t in titles if t.strip()])


def feed_item_title(item, feed) -> str:
    """The title to show for an agenda item, with the home/away mode applied."""
    own_team = getattr(feed, "own_team", None)
    if (
        getattr(item, "source", None) == "ical"
        and getattr(feed, "is_voetbal", False)
        and getattr(feed, "home_away_mode", False)
        and own_team
    ):
        shaped = home_away_title(item.title, own_team)
        if shaped:
            return shaped
    return item.title
