"""Sync Google Calendar events into local AgendaItems."""

import json
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import AgendaItem, GoogleApiConfig, PersonGoogleAuth, PersonGoogleCalendarFeed
from app.services.color_palette import normalize_stored_color
from app.services.google_calendar_service import (
    GOOGLE_COLORS,
    SyncTokenExpiredError,
    fetch_events,
    list_calendars,
    refresh_access_token,
)

logger = logging.getLogger(__name__)

_TZ_NAME = "Europe/Amsterdam"


def sync_all_google_calendars(db: Session) -> None:
    config = db.query(GoogleApiConfig).first()
    if not config or not config.client_id or not config.client_secret:
        return

    feeds = (
        db.query(PersonGoogleCalendarFeed)
        .filter(PersonGoogleCalendarFeed.enabled == True)  # noqa: E712
        .all()
    )

    for feed in feeds:
        try:
            _sync_feed(db, feed, config)
        except Exception:
            logger.exception("Google Calendar sync failed for feed %d", feed.id)


def _sync_feed(
    db: Session,
    feed: PersonGoogleCalendarFeed,
    config: GoogleApiConfig,
    *,
    full_sync: bool = False,
) -> None:
    auth = db.query(PersonGoogleAuth).filter(
        PersonGoogleAuth.person_id == feed.person_id
    ).first()

    if not auth or not auth.refresh_token:
        return

    access_token = _ensure_valid_token(db, auth, config)
    _ensure_feed_calendar_color(db, feed, access_token)
    color_filters: list[str] | None = json.loads(feed.color_filters) if feed.color_filters else None

    if full_sync:
        feed.sync_token = None

    now_utc = datetime.now(timezone.utc)
    time_min = (now_utc - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        items, next_sync_token = fetch_events(
            access_token,
            feed.google_calendar_id,
            sync_token=feed.sync_token,
            time_min=time_min if not feed.sync_token else None,
        )
    except SyncTokenExpiredError:
        logger.info("Sync token expired for feed %d, doing full sync", feed.id)
        items, next_sync_token = fetch_events(
            access_token,
            feed.google_calendar_id,
            time_min=time_min,
        )

    _apply_events(db, feed, items, color_filters, full_sync=full_sync)

    feed.sync_token = next_sync_token
    feed.last_synced_at = now_utc
    feed.last_error = None
    db.commit()


def _ensure_valid_token(db: Session, auth: PersonGoogleAuth, config: GoogleApiConfig) -> str:
    now = datetime.now(timezone.utc)
    expiry = auth.token_expiry
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    needs_refresh = (
        not auth.access_token
        or not expiry
        or expiry <= now + timedelta(minutes=5)
    )

    if needs_refresh:
        token_data = refresh_access_token(
            config.client_id, config.client_secret, auth.refresh_token
        )
        auth.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            auth.refresh_token = token_data["refresh_token"]
        expires_in = int(token_data.get("expires_in", 3600))
        auth.token_expiry = now + timedelta(seconds=expires_in)
        auth.updated_at = now
        db.commit()

    return auth.access_token


def _apply_events(
    db: Session,
    feed: PersonGoogleCalendarFeed,
    items: list[dict],
    color_filters: list[str] | None,
    *,
    full_sync: bool = False,
) -> None:
    if color_filters:
        color_filters = [_normalize_color_id(c) for c in color_filters if _normalize_color_id(c)]

    seen_uids: set[str] = set()

    for item in items:
        event_id = item.get("id")
        if not event_id:
            continue

        external_uid = f"gcal-{feed.id}-{event_id}"

        if item.get("status") == "cancelled":
            _delete_gcal_item(db, feed.id, external_uid)
            continue

        if color_filters:
            event_color_id = _normalize_color_id(item.get("colorId"))
            if event_color_id not in color_filters:
                _delete_gcal_item(db, feed.id, external_uid)
                continue

        start = item.get("start", {})
        end = item.get("end", {})

        anchor_date = _parse_date(start)
        if not anchor_date:
            continue

        end_date = _parse_date(end)
        start_time = _parse_time(start)
        end_time = _parse_time(end)

        title = (item.get("summary") or "Afspraak").strip()[:200]

        event_color = _resolve_event_color(item, feed)
        seen_uids.add(external_uid)

        existing = (
            db.query(AgendaItem)
            .filter(
                AgendaItem.google_feed_id == feed.id,
                AgendaItem.external_uid == external_uid,
            )
            .first()
        )

        if existing:
            existing.title = title
            existing.anchor_date = anchor_date
            existing.end_date = end_date if end_date and end_date != anchor_date else None
            existing.start_time = start_time
            existing.end_time = end_time
            existing.event_color = event_color
        else:
            db.add(AgendaItem(
                person_id=feed.person_id,
                title=title,
                repeat_type="once",
                repeat_weekdays="[]",
                anchor_date=anchor_date,
                end_date=end_date if end_date and end_date != anchor_date else None,
                start_time=start_time,
                end_time=end_time,
                source="gcal",
                external_uid=external_uid,
                google_feed_id=feed.id,
                event_color=event_color,
            ))

    if full_sync:
        _purge_unseen_gcal_items(db, feed.id, seen_uids)


def _delete_gcal_item(db: Session, feed_id: int, external_uid: str) -> None:
    db.query(AgendaItem).filter(
        AgendaItem.google_feed_id == feed_id,
        AgendaItem.external_uid == external_uid,
    ).delete(synchronize_session=False)


def _purge_unseen_gcal_items(db: Session, feed_id: int, seen_uids: set[str]) -> None:
    query = db.query(AgendaItem).filter(AgendaItem.google_feed_id == feed_id)
    if seen_uids:
        query = query.filter(AgendaItem.external_uid.notin_(seen_uids))
    query.delete(synchronize_session=False)


def _normalize_color_id(color_id) -> str | None:
    if color_id is None:
        return None
    return str(color_id)


def _resolve_event_color(item: dict, feed: PersonGoogleCalendarFeed) -> str | None:
    color_id = _normalize_color_id(item.get("colorId"))
    if color_id:
        hex_color = GOOGLE_COLORS.get(color_id, {}).get("hex")
        if hex_color:
            return hex_color
    calendar_color = (feed.calendar_color or "").strip()
    return calendar_color or None


def _ensure_feed_calendar_color(
    db: Session,
    feed: PersonGoogleCalendarFeed,
    access_token: str,
) -> None:
    if (feed.calendar_color or "").strip():
        return
    try:
        for cal in list_calendars(access_token):
            if cal.get("id") == feed.google_calendar_id:
                raw_color = (cal.get("backgroundColor") or "").strip() or None
                feed.calendar_color = normalize_stored_color(raw_color)
                db.commit()
                break
    except Exception:
        logger.exception("Could not fetch calendar color for feed %d", feed.id)


def _parse_date(dt_obj: dict) -> date | None:
    if not dt_obj:
        return None
    if "date" in dt_obj:
        try:
            return date.fromisoformat(dt_obj["date"])
        except (ValueError, TypeError):
            return None
    if "dateTime" in dt_obj:
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(_TZ_NAME)
            dt = datetime.fromisoformat(dt_obj["dateTime"])
            return dt.astimezone(tz).date()
        except (ValueError, TypeError, ImportError):
            return None
    return None


def _parse_time(dt_obj: dict) -> str | None:
    if not dt_obj or "dateTime" not in dt_obj:
        return None
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(_TZ_NAME)
        dt = datetime.fromisoformat(dt_obj["dateTime"])
        return dt.astimezone(tz).strftime("%H:%M")
    except (ValueError, TypeError, ImportError):
        return None
