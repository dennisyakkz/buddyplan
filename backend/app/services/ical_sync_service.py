import json
import logging
import threading
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar
from sqlalchemy.orm import Session

from app.models import AgendaItem, PersonCalendarFeed, utcnow

logger = logging.getLogger(__name__)

TZ = ZoneInfo("Europe/Amsterdam")
ICAL_DAY_MAP = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}

# Only one feed may sync at a time; others wait in line.
_sync_lock = threading.Semaphore(1)

VALID_INTERVALS = {15, 60, 1440}


def sync_all_feeds(db: Session) -> None:
    now = datetime.now(timezone.utc)
    feeds = db.query(PersonCalendarFeed).all()
    for feed in feeds:
        interval = feed.sync_interval_minutes or 60
        if feed.last_synced_at is None:
            due = True
        else:
            last = feed.last_synced_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            due = (now - last) >= timedelta(minutes=interval)
        if due:
            try:
                sync_feed(db, feed.id)
            except Exception as exc:
                logger.exception("Feed sync failed for feed %s: %s", feed.id, exc)


def sync_feed(db: Session, feed_id: int) -> int:
    """Fetch and import one iCal feed. Returns the number of imported events.

    Uses ETag / Last-Modified for conditional requests; returns 0 immediately
    when the server signals the content is unchanged (HTTP 304).
    Acquires a global lock so only one feed syncs at a time.
    """
    feed = db.query(PersonCalendarFeed).filter(PersonCalendarFeed.id == feed_id).first()
    if not feed:
        return 0

    _sync_lock.acquire()
    try:
        return _do_sync(db, feed)
    finally:
        _sync_lock.release()


def _do_sync(db: Session, feed: PersonCalendarFeed) -> int:
    from app.services.ical_validation import normalize_ical_url

    headers: dict[str, str] = {}
    if feed.etag:
        headers["If-None-Match"] = feed.etag
    if feed.last_modified:
        headers["If-Modified-Since"] = feed.last_modified

    try:
        response = requests.get(normalize_ical_url(feed.url), headers=headers, timeout=30)

        if response.status_code == 304:
            # Content unchanged — only update the sync timestamp.
            feed.last_synced_at = utcnow()
            feed.last_error = None
            feed.updated_at = utcnow()
            db.commit()
            logger.debug("Feed %s: 304 Not Modified, skipped import", feed.id)
            return 0

        response.raise_for_status()

        # Store caching headers for the next request.
        new_etag = response.headers.get("ETag")
        new_last_modified = response.headers.get("Last-Modified")
        if new_etag is not None:
            feed.etag = new_etag
        if new_last_modified is not None:
            feed.last_modified = new_last_modified

        calendar = Calendar.from_ical(response.content)
        imported = _import_calendar(db, feed, calendar)

        feed.last_synced_at = utcnow()
        feed.last_error = None
        feed.updated_at = utcnow()
        db.commit()
        return imported

    except Exception as exc:
        feed.last_error = str(exc)
        feed.updated_at = utcnow()
        db.commit()
        raise


def _import_calendar(db: Session, feed: PersonCalendarFeed, calendar: Calendar) -> int:
    db.query(AgendaItem).filter(
        AgendaItem.feed_id == feed.id,
        AgendaItem.source == "ical",
    ).delete(synchronize_session=False)

    count = 0
    for component in calendar.walk():
        if component.name != "VEVENT":
            continue
        item = _event_to_agenda_item(feed, component)
        if item:
            db.add(item)
            count += 1
    db.flush()
    return count


def _extract_time(dt_value) -> str | None:
    """Return 'HH:MM' from a datetime, or None for all-day (date) events."""
    if isinstance(dt_value, datetime):
        local = dt_value.astimezone(TZ) if dt_value.tzinfo else dt_value
        return local.strftime("%H:%M")
    return None


def _event_to_agenda_item(feed: PersonCalendarFeed, event) -> AgendaItem | None:
    title = str(event.get("SUMMARY") or "Afspraak").strip()
    if not title:
        return None

    uid = str(event.get("UID") or f"{feed.id}-{title}-{event.get('DTSTART')}")
    dtstart = event.get("DTSTART")
    if not dtstart:
        return None

    anchor = _to_local_date(dtstart.dt)
    start_time = _extract_time(dtstart.dt)

    dtend = event.get("DTEND")
    end_time = _extract_time(dtend.dt) if dtend else None

    repeat_type, weekdays, end_date = _parse_recurrence(event, anchor)

    return AgendaItem(
        person_id=feed.person_id,
        title=title[:200],
        repeat_type=repeat_type,
        repeat_weekdays=json.dumps(weekdays),
        anchor_date=anchor,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        source="ical",
        external_uid=uid[:255],
        feed_id=feed.id,
    )


def _to_local_date(value) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        if value.tzinfo:
            return value.astimezone(TZ).date()
        return value.date()
    raise ValueError(f"Unsupported date value: {value!r}")


def _parse_recurrence(event, anchor: date) -> tuple[str, list[int], date | None]:
    rrule = event.get("RRULE")
    if not rrule:
        return "once", [], None

    rule = {str(k): str(v) for k, v in rrule.items()}
    freq = rule.get("FREQ", "").upper()
    end_date = _parse_until(rule.get("UNTIL"))

    byday_raw = rule.get("BYDAY", "")
    if isinstance(byday_raw, bytes):
        byday_raw = byday_raw.decode()
    weekdays = sorted({
        ICAL_DAY_MAP[day]
        for day in str(byday_raw).split(",")
        if day in ICAL_DAY_MAP
    })

    if freq == "DAILY":
        return "daily", [], end_date
    if freq == "WEEKLY":
        if len(weekdays) > 1:
            return "weekdays", weekdays, end_date
        if len(weekdays) == 1:
            return "weekly", weekdays, end_date
        return "weekly", [], end_date
    if freq == "MONTHLY":
        return "once", [], end_date

    return "once", [], end_date


def _parse_until(value) -> date | None:
    if not value:
        return None
    text = str(value)
    if "T" in text:
        text = text.split("T", 1)[0]
    if len(text) >= 8:
        return date(int(text[0:4]), int(text[4:6]), int(text[6:8]))
    return None
