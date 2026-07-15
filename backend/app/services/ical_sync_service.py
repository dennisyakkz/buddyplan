import json
import logging
import threading
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

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


def sync_feed(db: Session, feed_id: int, *, force_full: bool = False) -> int:
    """Fetch and import one iCal feed. Returns the number of imported events.

    Uses ETag / Last-Modified for conditional requests when items already exist.
    A 304 or empty body on a conditional fetch keeps existing items.
    Pass force_full=True for manual sync to always fetch the full calendar.
    Acquires a global lock so only one feed syncs at a time.
    """
    feed = db.query(PersonCalendarFeed).filter(PersonCalendarFeed.id == feed_id).first()
    if not feed:
        return 0

    _sync_lock.acquire()
    try:
        return _do_sync(db, feed, force_full=force_full)
    finally:
        _sync_lock.release()


def _touch_feed_sync(db: Session, feed: PersonCalendarFeed) -> None:
    feed.last_synced_at = utcnow()
    feed.last_error = None
    feed.updated_at = utcnow()
    db.commit()


def _do_sync(db: Session, feed: PersonCalendarFeed, *, force_full: bool = False) -> int:
    from app.services.ical_validation import fetch_ical_response

    existing_count = (
        db.query(AgendaItem)
        .filter(
            AgendaItem.feed_id == feed.id,
            AgendaItem.source == "ical",
        )
        .count()
    )
    use_conditional = existing_count > 0 and not force_full

    try:
        response = fetch_ical_response(
            feed.url,
            etag=feed.etag if use_conditional else None,
            last_modified=feed.last_modified if use_conditional else None,
            force_full=not use_conditional,
        )

        if use_conditional and response.status_code == 304:
            _touch_feed_sync(db, feed)
            logger.debug(
                "Feed %s: 304 Not Modified, kept %s items", feed.id, existing_count
            )
            return 0

        if use_conditional and not response.content:
            _touch_feed_sync(db, feed)
            logger.debug(
                "Feed %s: empty conditional response, kept %s items",
                feed.id,
                existing_count,
            )
            return 0

        if response.status_code == 304 and not response.content:
            raise ValueError(
                "Agenda-server gaf geen data terug (304). Probeer later opnieuw."
            )

        response.raise_for_status()

        if not response.content:
            if existing_count > 0:
                _touch_feed_sync(db, feed)
                logger.warning(
                    "Feed %s: empty full response, kept %s items", feed.id, existing_count
                )
                return 0
            raise ValueError("Agenda-server gaf geen data terug. Probeer later opnieuw.")

        calendar = Calendar.from_ical(response.content)
        new_items = _items_from_calendar(feed, calendar)

        if use_conditional and len(new_items) == 0:
            _touch_feed_sync(db, feed)
            logger.warning(
                "Feed %s: conditional sync parsed 0 events, kept %s items",
                feed.id,
                existing_count,
            )
            return 0

        new_etag = response.headers.get("ETag")
        new_last_modified = response.headers.get("Last-Modified")
        if new_etag is not None:
            feed.etag = new_etag
        if new_last_modified is not None:
            feed.last_modified = new_last_modified

        imported = _replace_feed_items(db, feed, new_items)

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


def sync_feed_from_content(db: Session, feed_id: int, content: bytes) -> int:
    """Import a pre-fetched iCal payload (e.g. right after validation)."""
    feed = db.query(PersonCalendarFeed).filter(PersonCalendarFeed.id == feed_id).first()
    if not feed:
        return 0

    _sync_lock.acquire()
    try:
        calendar = Calendar.from_ical(content)
        new_items = _items_from_calendar(feed, calendar)
        imported = _replace_feed_items(db, feed, new_items)
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
    finally:
        _sync_lock.release()


def _items_from_calendar(feed: PersonCalendarFeed, calendar: Calendar) -> list[AgendaItem]:
    items: list[AgendaItem] = []
    for component in calendar.walk():
        if component.name != "VEVENT":
            continue
        item = _event_to_agenda_item(feed, component)
        if item:
            items.append(item)
    return items


def _replace_feed_items(
    db: Session, feed: PersonCalendarFeed, items: list[AgendaItem]
) -> int:
    db.query(AgendaItem).filter(
        AgendaItem.feed_id == feed.id,
        AgendaItem.source == "ical",
    ).delete(synchronize_session=False)

    for item in items:
        db.add(item)
    db.flush()
    return len(items)


def _import_calendar(db: Session, feed: PersonCalendarFeed, calendar: Calendar) -> int:
    return _replace_feed_items(db, feed, _items_from_calendar(feed, calendar))


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
