import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.services.ical_sync_service import sync_all_feeds

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None

# In-process scheduler for single-container deployments. Not suitable for
# multi-instance HA without external job locking.


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="Europe/Amsterdam")

    def ical_job():
        db = SessionLocal()
        try:
            sync_all_feeds(db)
        except Exception:
            logger.exception("Scheduled iCal sync failed")
        finally:
            db.close()

    def afvalwijzer_job():
        from app.services.afvalwijzer_service import AfvalwijzerService
        db = SessionLocal()
        try:
            service = AfvalwijzerService(db)
            today = date.today()
            # Sunday at 2:00 AM → create tasks for the coming week (Mon–Sun)
            next_monday = today + timedelta(days=1)
            count = service.create_tasks_for_weeks([next_monday])
            logger.info("Afvalwijzer: %d taken aangemaakt voor week van %s", count, next_monday)
        except Exception:
            logger.exception("Afvalwijzer scheduled task creation failed")
        finally:
            db.close()

    def google_calendar_job():
        from app.services.google_sync_service import sync_all_google_calendars
        db = SessionLocal()
        try:
            sync_all_google_calendars(db)
        except Exception:
            logger.exception("Google Calendar sync failed")
        finally:
            db.close()

    # Poll every 5 minutes; each feed decides based on its own sync_interval_minutes.
    _scheduler.add_job(
        ical_job, "interval", minutes=5, id="ical_sync",
        replace_existing=True, max_instances=1,
    )

    # Sync Google Calendar feeds every 10 minutes.
    _scheduler.add_job(
        google_calendar_job, "interval", minutes=10, id="google_calendar_sync",
        replace_existing=True, max_instances=1,
    )

    # Every Sunday at 02:00 Europe/Amsterdam time create waste tasks for the coming week.
    _scheduler.add_job(
        afvalwijzer_job, "cron", day_of_week="sun", hour=2, minute=0,
        id="afvalwijzer_create_tasks", replace_existing=True, max_instances=1,
    )

    _scheduler.start()
    logger.info("Scheduler started (iCal every 5 min, Google Calendar every 10 min, afvalwijzer every Sunday 02:00)")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
