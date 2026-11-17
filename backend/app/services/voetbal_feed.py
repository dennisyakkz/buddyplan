"""voetbal.nl iCal feeds: recognition, own-team detection and home/away titles.

REQ-BE-044..049. The feeds are served by data.sportlink.com; match titles
look like "VV 't Dorp MO15-2-FC Voorbeeld MO15-4" (home team, '-', away team), and team names contain
hyphens themselves, so a title is never split blindly on '-'.
"""

import re
from collections import Counter

from icalendar import Calendar

MARKER = "voetbal.nl"
REFEREE_WORD = re.compile(r"scheidsrechter", re.IGNORECASE)


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


def referee_match(title: str) -> str | None:
    """The match of a referee duty: the title after 'scheidsrechter' and its punctuation."""
    found = REFEREE_WORD.search(title)
    if not found:
        return None
    return title[found.end() :].strip().lstrip(",:;.-").strip() or None


def drop_refereed_duplicates(items: list) -> list:
    """Leave out normal items that are also listed as a referee duty at the same start (REQ-BE-051)."""

    def key(item, title: str) -> tuple:
        return (item.anchor_date, item.start_time, title.strip().casefold())

    refereed = {key(item, match) for item in items if (match := referee_match(item.title))}
    return [item for item in items if referee_match(item.title) or key(item, item.title) not in refereed]


def referee_home_team(title: str) -> str | None:
    """The home team of a referee duty like 'Scheidsrechter, FC Club JO15-1-SV Other JO15-2'.

    Team names contain hyphens ('JO15-1'), so the teams are split at the first '-' that directly
    follows a digit and is not followed by a digit. None when the title is no referee duty.
    """
    match = referee_match(title)
    if not match:
        return None
    for index, char in enumerate(match):
        if char != "-" or index == 0:
            continue
        before, after = match[:index].rstrip(), match[index + 1 :].lstrip()
        if before and before[-1].isdigit() and after and not after[0].isdigit():
            return before
    return None


def club_from_team(team: str | None) -> str:
    """The club of a team: the team without its last word when that word holds a digit."""
    words = (team or "").split()
    if len(words) > 1 and any(char.isdigit() for char in words[-1]):
        words = words[:-1]
    return " ".join(words)


def effective_club(feed) -> str:
    """The stored club; while it was never set, the club suggested from the own team."""
    club = getattr(feed, "club", None)
    if club is None:
        return club_from_team(getattr(feed, "own_team", None))
    return club.strip()


def referee_title(title: str, club: str) -> str | None:
    """'Fluiten <home team>' without the club, or None when the title is no referee duty."""
    home = referee_home_team(title)
    if not home:
        return None
    club = club.strip()
    if club and home.casefold().startswith(club.casefold() + " "):
        home = home[len(club) :].strip()
    return f"Fluiten {home}"


def feed_item_title(item, feed) -> str:
    """The title to show for an agenda item, with the referee and home/away modes applied."""
    is_feed_item = getattr(item, "source", None) == "ical" and getattr(feed, "is_voetbal", False)
    if is_feed_item and getattr(feed, "referee_compact", False):
        shaped = referee_title(item.title, effective_club(feed))
        if shaped:
            return shaped
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
