"""Display text helpers for agenda items (feed prefix, times, hide title)."""

from app.models import AgendaItem, PersonCalendarFeed


def build_agenda_display_text(
    item: AgendaItem,
    feed: PersonCalendarFeed | None,
    *,
    prefix: str | None = None,
) -> str:
    """Build the user-facing label for an agenda item."""
    prefix_value = prefix if prefix is not None else (
        (feed.prefix or "").strip() if feed else ""
    )
    show_times = bool(feed and feed.show_times)
    hide_title = bool(feed and feed.hide_title and show_times)

    time_str = ""
    if show_times and (item.start_time or item.end_time):
        if item.start_time and item.end_time:
            time_str = f"{item.start_time}-{item.end_time}"
        elif item.start_time:
            time_str = item.start_time

    if hide_title and time_str:
        content = time_str
    elif time_str:
        content = f"{time_str} {item.title}"
    else:
        content = item.title

    return f"{prefix_value}: {content}" if prefix_value else content


def build_agenda_event_dict(
    item: AgendaItem,
    feed: PersonCalendarFeed | None,
    *,
    prefix: str | None = None,
    color: str | None = None,
) -> dict:
    """Structured calendar event; times are always included when present on the item."""
    prefix_value = prefix if prefix is not None else (
        (feed.prefix or "").strip() if feed else ""
    )
    return {
        "text": build_agenda_display_text(item, feed, prefix=prefix_value),
        "color": color,
        "title": item.title,
        "start_time": item.start_time,
        "end_time": item.end_time,
    }


def agenda_event_sort_key(event: dict) -> tuple:
    start = event.get("start_time")
    return (start is None, start or "99:99", event.get("title") or "")


def feed_for_item(
    item: AgendaItem,
    feeds: dict[int, PersonCalendarFeed],
) -> PersonCalendarFeed | None:
    if not item.feed_id:
        return None
    return feeds.get(item.feed_id)
