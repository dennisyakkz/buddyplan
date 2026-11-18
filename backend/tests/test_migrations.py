"""REQ-BE-071: migrations keep existing data, also rows behind ON DELETE CASCADE foreign keys."""

from datetime import date
from pathlib import Path

from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.database import SessionLocal, engine
from app.models import AgendaItem, PersonCalendarFeed

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def test_migrations_keep_imported_agenda_items(make_user):
    person, _headers = make_user("Migratie")
    db = SessionLocal()
    try:
        feed = PersonCalendarFeed(person_id=person["id"], url="https://example.test/a.ics", label="A")
        db.add(feed)
        db.flush()
        for index in range(3):
            db.add(
                AgendaItem(
                    person_id=person["id"],
                    title=f"Geimporteerd {index}",
                    source="ical",
                    feed_id=feed.id,
                    anchor_date=date.today(),
                    repeat_type="once",
                )
            )
        db.commit()
        feed_id = feed.id
    finally:
        db.close()

    # 005 rebuilds person_calendar_feeds (SQLite batch mode) on the way down and up again.
    cfg = Config(str(ALEMBIC_INI))
    command.downgrade(cfg, "004_voetbal_feed_options")
    command.upgrade(cfg, "head")

    db = SessionLocal()
    try:
        assert db.query(AgendaItem).filter(AgendaItem.feed_id == feed_id).count() == 3
    finally:
        db.close()
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1
