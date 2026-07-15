import hashlib
import json
from datetime import date, datetime, timedelta

import bcrypt
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AgendaItem, AgendaManager, Person, PersonCalendarFeed, PersonGoogleCalendarFeed, Task, TaskCompletion, TaskDayOrder, TaskManager
from app.services.agenda_display import agenda_event_sort_key, build_agenda_event_dict, feed_for_item
from app.services.color_palette import normalize_stored_color, resolve_color_label, label_to_badge_classes
from app.services.recurrence import (
    DAY_KEYS,
    format_dutch_date,
    format_dutch_day,
    monday_of_week,
    occurs_on_date,
    week_dates,
)



def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_etag(self, reference: date | None = None) -> str:
        ref = reference or date.today()
        parts = []

        for model in (Task, AgendaItem, Person):
            max_updated = self.db.query(func.max(model.updated_at)).scalar()
            if max_updated:
                parts.append(f"{model.__tablename__}:{max_updated.isoformat()}")

        for model in (PersonCalendarFeed, PersonGoogleCalendarFeed):
            max_synced = self.db.query(func.max(model.last_synced_at)).scalar()
            if max_synced:
                parts.append(f"{model.__tablename__}:sync:{max_synced.isoformat()}")

        task_count = self.db.query(func.count(Task.id)).scalar()
        max_task_id = self.db.query(func.max(Task.id)).scalar()
        agenda_count = self.db.query(func.count(AgendaItem.id)).scalar()
        order_count = self.db.query(func.count(TaskDayOrder.id)).scalar()
        parts.append(f"counts:{task_count}:{max_task_id}:{agenda_count}:{order_count}")

        completion_count = self.db.query(func.count(TaskCompletion.id)).filter(
            TaskCompletion.completion_date == ref
        ).scalar()
        parts.append(f"completions:{completion_count}:{ref.isoformat()}")

        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]

    def build_dashboard(self, reference: date | None = None) -> dict:
        ref = reference or date.today()
        week = week_dates(ref)

        todos = self._build_todos(ref)
        week_days = [
            {"day": format_dutch_day(d), "date": format_dutch_date(d), "iso": d.isoformat()}
            for d in week
        ]
        calendar = self._build_calendar(week, range_start=week[0], range_end=week[-1])

        return {
            "todo": todos,
            "weekDays": week_days,
            "calendar": calendar,
        }

    def build_dashboard_range(self, start: date, end: date) -> dict:
        """Build dashboard calendar data for each week in [start, end] (inclusive)."""
        start_monday = monday_of_week(start)
        end_monday = monday_of_week(end)
        if end_monday < start_monday:
            end_monday = start_monday

        week_starts: list[date] = []
        current = start_monday
        while current <= end_monday:
            week_starts.append(current)
            current += timedelta(days=7)

        todos = self._build_todos(date.today())
        range_start = start_monday
        range_end = end_monday + timedelta(days=6)
        calendar_ctx = self._load_calendar_context(range_start, range_end)
        weeks = []
        for week_start in week_starts:
            week = week_dates(week_start)
            weeks.append({
                "week_start": week_start.isoformat(),
                "weekDays": [
                    {"day": format_dutch_day(d), "date": format_dutch_date(d), "iso": d.isoformat()}
                    for d in week
                ],
                "calendar": self._build_calendar(week, calendar_ctx),
            })

        return {"todo": todos, "weeks": weeks}

    def _load_calendar_context(self, range_start: date, range_end: date) -> dict:
        items_query = self.db.query(AgendaItem).filter(
            (AgendaItem.end_date.is_(None) | (AgendaItem.end_date >= range_start)),
            (AgendaItem.anchor_date.is_(None) | (AgendaItem.anchor_date <= range_end)),
        )
        return {
            "persons": self.db.query(Person).order_by(Person.sort_order, Person.id).all(),
            "items": items_query.all(),
            "feeds": {f.id: f for f in self.db.query(PersonCalendarFeed).all()},
            "google_feeds": {f.id: f for f in self.db.query(PersonGoogleCalendarFeed).all()},
        }

    def _build_todos(self, target: date) -> list[dict]:
        tasks = self.db.query(Task).all()
        applicable = [
            t for t in tasks
            if occurs_on_date(
                t.repeat_type, t.get_weekdays(), t.anchor_date,
                t.end_date, target
            )
        ]

        day_orders = {
            o.task_id: o.sort_order
            for o in self.db.query(TaskDayOrder).filter(TaskDayOrder.order_date == target).all()
        }
        completions = {
            c.task_id
            for c in self.db.query(TaskCompletion).filter(TaskCompletion.completion_date == target).all()
        }

        applicable.sort(key=lambda t: (day_orders.get(t.id, t.sort_order), t.id))

        return [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "icon": t.icon,
                "completed": t.id in completions,
                "person_id": t.person_id,
            }
            for t in applicable
        ]

    def _build_calendar(
        self,
        week: list[date],
        ctx: dict | None = None,
        range_start: date | None = None,
        range_end: date | None = None,
    ) -> list[dict]:
        if ctx is None:
            rs = range_start or week[0]
            re = range_end or week[-1]
            ctx = self._load_calendar_context(rs, re)
        persons = ctx["persons"]
        items = ctx["items"]
        feeds = ctx["feeds"]
        google_feeds = ctx["google_feeds"]

        result = []
        for person in persons:
            person_items = [i for i in items if i.person_id == person.id]
            entry = {"name": person.name}
            for day_index, day_date in enumerate(week):
                day_events = []
                for item in person_items:
                    if not occurs_on_date(
                        item.repeat_type, item.get_weekdays(), item.anchor_date,
                        item.end_date, day_date
                    ):
                        continue
                    feed = feed_for_item(item, feeds)
                    prefix = (feed.prefix or "").strip() if feed else ""
                    gfeed = google_feeds.get(item.google_feed_id) if item.google_feed_id else None
                    feed_color = (feed.color or "").strip() if feed else ""
                    google_calendar_color = (gfeed.calendar_color or "").strip() if gfeed else ""
                    event_color = (item.event_color or "").strip() or None
                    color_label = resolve_color_label(
                        feed_color=feed_color or None,
                        event_color=event_color,
                        google_calendar_color=google_calendar_color or None,
                    )
                    legacy_color = event_color or google_calendar_color or feed_color or None
                    text = build_agenda_event_dict(
                        item,
                        feed,
                        prefix=prefix,
                        color=legacy_color,
                        color_label=color_label,
                    )
                    day_events.append(text)
                day_events.sort(key=agenda_event_sort_key)
                entry[DAY_KEYS[day_index]] = day_events
            result.append(entry)
        return result


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Task]:
        return self.db.query(Task).order_by(Task.sort_order, Task.id).all()

    def list_for_person(self, person_id: int) -> list[Task]:
        return (
            self.db.query(Task)
            .filter(Task.person_id == person_id)
            .order_by(Task.sort_order, Task.id)
            .all()
        )

    def get(self, task_id: int) -> Task | None:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def create(self, data: dict) -> Task:
        task = Task(**data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task_id: int, data: dict) -> Task | None:
        task = self.get(task_id)
        if not task:
            return None
        for key, value in data.items():
            setattr(task, key, value)
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task_id: int) -> bool:
        task = self.get(task_id)
        if not task:
            return False
        self.db.delete(task)
        self.db.commit()
        return True

    def get_for_date(self, target: date, person_id: int | None = None) -> list[Task]:
        tasks = self.list_for_person(person_id) if person_id is not None else self.list_all()
        return [
            t for t in tasks
            if occurs_on_date(
                t.repeat_type, t.get_weekdays(), t.anchor_date,
                t.end_date, target
            )
        ]

    def reorder_for_date(self, target: date, task_ids: list[int]) -> None:
        for index, task_id in enumerate(task_ids):
            existing = self.db.query(TaskDayOrder).filter(
                TaskDayOrder.task_id == task_id,
                TaskDayOrder.order_date == target,
            ).first()
            if existing:
                existing.sort_order = index
            else:
                self.db.add(TaskDayOrder(task_id=task_id, order_date=target, sort_order=index))
        self.db.commit()

    def move_to_date(self, task_id: int, from_date: date, to_date: date) -> bool:
        task = self.get(task_id)
        if not task:
            return False

        task.anchor_date = to_date

        if task.repeat_type == "weekdays":
            weekdays = task.get_weekdays()
            from_weekday = from_date.weekday()
            to_weekday = to_date.weekday()
            if from_weekday in weekdays:
                weekdays = [d for d in weekdays if d != from_weekday]
            if to_weekday not in weekdays:
                weekdays.append(to_weekday)
            weekdays.sort()
            task.repeat_weekdays = json.dumps(weekdays)
        elif task.repeat_type == "once":
            pass
        elif task.repeat_type in ("weekly", "biweekly", "daily"):
            pass

        task.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def mark_complete(self, task_id: int, target: date) -> bool:
        task = self.get(task_id)
        if not task:
            return False
        existing = self.db.query(TaskCompletion).filter(
            TaskCompletion.task_id == task_id,
            TaskCompletion.completion_date == target,
        ).first()
        if not existing:
            self.db.add(TaskCompletion(task_id=task_id, completion_date=target))
            self.db.commit()
        return True

    def task_to_dict(self, task: Task, target: date | None = None) -> dict:
        result = {
            "id": task.id,
            "person_id": task.person_id,
            "title": task.title,
            "description": task.description,
            "icon": task.icon,
            "repeat_type": task.repeat_type,
            "repeat_weekdays": task.get_weekdays(),
            "anchor_date": task.anchor_date.isoformat() if task.anchor_date else None,
            "end_date": task.end_date.isoformat() if task.end_date else None,
            "sort_order": task.sort_order,
        }
        if target:
            completion = self.db.query(TaskCompletion).filter(
                TaskCompletion.task_id == task.id,
                TaskCompletion.completion_date == target,
            ).first()
            result["completed"] = completion is not None
        return result


class AgendaService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_person(self, person_id: int) -> list[AgendaItem]:
        return (
            self.db.query(AgendaItem)
            .filter(AgendaItem.person_id == person_id)
            .order_by(AgendaItem.sort_order, AgendaItem.id)
            .all()
        )

    def get(self, item_id: int) -> AgendaItem | None:
        return self.db.query(AgendaItem).filter(AgendaItem.id == item_id).first()

    def create(self, data: dict) -> AgendaItem:
        item = AgendaItem(**data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: int, data: dict) -> AgendaItem | None:
        item = self.get(item_id)
        if not item:
            return None
        for key, value in data.items():
            setattr(item, key, value)
        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        item = self.get(item_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    def get_for_date(self, person_id: int, target: date) -> list[AgendaItem]:
        items = self.list_for_person(person_id)
        return [
            i for i in items
            if occurs_on_date(
                i.repeat_type, i.get_weekdays(), i.anchor_date,
                i.end_date, target
            )
        ]

    def feed_maps_for_person(self, person_id: int) -> tuple[dict[int, PersonCalendarFeed], dict[int, PersonGoogleCalendarFeed]]:
        feeds = {
            f.id: f
            for f in self.db.query(PersonCalendarFeed)
            .filter(PersonCalendarFeed.person_id == person_id)
            .all()
        }
        google_feeds = {
            f.id: f
            for f in self.db.query(PersonGoogleCalendarFeed)
            .filter(PersonGoogleCalendarFeed.person_id == person_id)
            .all()
        }
        return feeds, google_feeds

    def item_to_dict(
        self,
        item: AgendaItem,
        *,
        feeds: dict[int, PersonCalendarFeed] | None = None,
        google_feeds: dict[int, PersonGoogleCalendarFeed] | None = None,
    ) -> dict:
        result = {
            "id": item.id,
            "person_id": item.person_id,
            "title": item.title,
            "repeat_type": item.repeat_type,
            "repeat_weekdays": item.get_weekdays(),
            "anchor_date": item.anchor_date.isoformat() if item.anchor_date else None,
            "end_date": item.end_date.isoformat() if item.end_date else None,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "sort_order": item.sort_order,
            "source": item.source,
        }
        if feeds is not None:
            feed = feed_for_item(item, feeds)
            gfeed = google_feeds.get(item.google_feed_id) if item.google_feed_id and google_feeds else None
            feed_color = (feed.color or "").strip() if feed else ""
            google_calendar_color = (gfeed.calendar_color or "").strip() if gfeed else ""
            event_color = (item.event_color or "").strip() or None
            color_label = resolve_color_label(
                feed_color=feed_color or None,
                event_color=event_color,
                google_calendar_color=google_calendar_color or None,
            )
            result["color_label"] = color_label
            result["badge_classes"] = label_to_badge_classes(color_label)
        return result


class PersonService:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Person]:
        return self.db.query(Person).order_by(Person.sort_order, Person.id).all()

    def get(self, person_id: int) -> Person | None:
        return self.db.query(Person).filter(Person.id == person_id).first()

    def get_by_username(self, username: str) -> Person | None:
        return (
            self.db.query(Person)
            .filter(Person.username == username)
            .first()
        )

    def verify_login(self, username: str, password: str) -> Person | None:
        person = self.get_by_username(username.strip())
        if not person:
            return None
        if not getattr(person, "can_login", False):
            return None
        if not person.password_hash:
            return None
        if not _verify_password(password, person.password_hash):
            return None
        return person

    def has_login_users(self) -> bool:
        return (
            self.db.query(Person)
            .filter(Person.can_login.is_(True))
            .count() > 0
        )

    def bootstrap_admin(self, name: str, username: str, password: str) -> Person:
        username = username.strip()
        if self.get_by_username(username):
            raise ValueError("Username bestaat al")
        person = Person(
            name=name.strip(),
            username=username,
            can_login=True,
            is_admin=True,
            tasks_enabled=True,
            sort_order=1,
            password_hash=_hash_password(password),
        )
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)
        self.db.add(
            TaskManager(owner_person_id=person.id, manager_person_id=person.id)
        )
        self._ensure_self_agenda_manager(person.id)
        self.db.commit()
        self.db.refresh(person)
        return person

    def _ensure_self_agenda_manager(self, person_id: int) -> None:
        exists = (
            self.db.query(AgendaManager)
            .filter(
                AgendaManager.owner_person_id == person_id,
                AgendaManager.manager_person_id == person_id,
            )
            .first()
        )
        if not exists:
            self.db.add(
                AgendaManager(
                    owner_person_id=person_id,
                    manager_person_id=person_id,
                )
            )

    def create(self, name: str) -> Person:
        max_order = self.db.query(func.max(Person.sort_order)).scalar() or 0
        person = Person(name=name, sort_order=max_order + 1)
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)
        self._ensure_self_agenda_manager(person.id)
        self.db.commit()
        self.db.refresh(person)
        return person

    def update_user_fields(
        self,
        person_id: int,
        username: str | None,
        email: str | None,
        is_admin: bool,
    ) -> Person | None:
        person = self.get(person_id)
        if not person:
            return None

        person.username = username.strip() if username else None
        person.email = email.strip() if email else None
        person.is_admin = bool(is_admin)
        person.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(person)
        return person

    def set_tasks_enabled(self, person_id: int, enabled: bool) -> Person | None:
        person = self.get(person_id)
        if not person:
            return None
        person.tasks_enabled = bool(enabled)
        person.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(person)
        return person

    def list_task_managers(self, owner_person_id: int) -> list[Person]:
        pairs = (
            self.db.query(TaskManager)
            .filter(TaskManager.owner_person_id == owner_person_id)
            .order_by(TaskManager.id)
            .all()
        )
        ids = [p.manager_person_id for p in pairs]
        if not ids:
            return []
        return self.db.query(Person).filter(Person.id.in_(ids)).order_by(Person.name).all()

    def set_task_managers(self, owner_person_id: int, manager_ids: list[int]) -> None:
        existing = (
            self.db.query(TaskManager)
            .filter(TaskManager.owner_person_id == owner_person_id)
            .all()
        )
        existing_ids = {p.manager_person_id for p in existing}
        desired_ids = {int(i) for i in manager_ids}

        for pair in existing:
            if pair.manager_person_id not in desired_ids:
                self.db.delete(pair)
        for mid in desired_ids:
            if mid not in existing_ids:
                self.db.add(TaskManager(owner_person_id=owner_person_id, manager_person_id=mid))
        self.db.commit()

    def can_manage_tasks(self, owner_person_id: int, manager_person_id: int) -> bool:
        person = self.get(owner_person_id)
        if not person or not getattr(person, "tasks_enabled", False):
            return False
        return (
            self.db.query(TaskManager)
            .filter(
                TaskManager.owner_person_id == owner_person_id,
                TaskManager.manager_person_id == manager_person_id,
            )
            .first()
            is not None
        )

    def can_manage_agenda(self, owner_person_id: int, manager_person_id: int) -> bool:
        if not self.get(owner_person_id):
            return False
        return (
            self.db.query(AgendaManager)
            .filter(
                AgendaManager.owner_person_id == owner_person_id,
                AgendaManager.manager_person_id == manager_person_id,
            )
            .first()
            is not None
        )

    def update(
        self,
        person_id: int,
        name: str,
        can_login: bool,
        password: str | None = None,
    ) -> Person | None:
        person = self.get(person_id)
        if not person:
            return None

        person.name = name
        person.can_login = can_login
        if password:
            person.password_hash = _hash_password(password)

        if can_login:
            self._ensure_self_agenda_manager(person_id)

        person.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(person)
        return person

    def delete(self, person_id: int) -> bool:
        person = self.get(person_id)
        if not person:
            return False
        self.db.delete(person)
        self.db.commit()
        return True

    def list_feeds(self, person_id: int) -> list[PersonCalendarFeed]:
        return (
            self.db.query(PersonCalendarFeed)
            .filter(PersonCalendarFeed.person_id == person_id)
            .order_by(PersonCalendarFeed.id)
            .all()
        )

    def add_feed(
        self,
        person_id: int,
        url: str,
        label: str = "",
        sync_interval_minutes: int = 60,
        prefix: str = "",
        color: str = "",
        show_times: bool = False,
        hide_title: bool = False,
    ) -> PersonCalendarFeed | None:
        if not self.get(person_id):
            return None
        feed = PersonCalendarFeed(
            person_id=person_id,
            url=url.strip(),
            label=label.strip(),
            sync_interval_minutes=sync_interval_minutes,
            prefix=prefix.strip() or None,
            color=normalize_stored_color(color.strip() or None),
            show_times=show_times,
            hide_title=hide_title,
        )
        self.db.add(feed)
        self.db.commit()
        self.db.refresh(feed)
        return feed

    def update_feed(
        self,
        person_id: int,
        feed_id: int,
        url: str,
        label: str = "",
        sync_interval_minutes: int | None = None,
        prefix: str | None = None,
        color: str | None = None,
        show_times: bool | None = None,
        hide_title: bool | None = None,
    ) -> PersonCalendarFeed | None:
        feed = (
            self.db.query(PersonCalendarFeed)
            .filter(PersonCalendarFeed.id == feed_id, PersonCalendarFeed.person_id == person_id)
            .first()
        )
        if not feed:
            return None
        feed.url = url.strip()
        feed.label = label.strip()
        if sync_interval_minutes is not None:
            feed.sync_interval_minutes = sync_interval_minutes
            # Reset caching headers when URL or interval changes so the next sync is forced.
            feed.etag = None
            feed.last_modified = None
        if prefix is not None:
            feed.prefix = prefix.strip() or None
        if color is not None:
            feed.color = normalize_stored_color(color.strip() or None)
        if show_times is not None:
            feed.show_times = show_times
        if hide_title is not None:
            feed.hide_title = hide_title
        feed.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(feed)
        return feed

    def delete_feed(self, person_id: int, feed_id: int) -> bool:
        feed = (
            self.db.query(PersonCalendarFeed)
            .filter(PersonCalendarFeed.id == feed_id, PersonCalendarFeed.person_id == person_id)
            .first()
        )
        if not feed:
            return False
        self.db.delete(feed)
        self.db.commit()
        return True

    def person_to_dict(self, person: Person) -> dict:
        return {
            "id": person.id,
            "name": person.name,
            "username": getattr(person, "username", None),
            "email": getattr(person, "email", None),
            "is_admin": getattr(person, "is_admin", False),
            "sort_order": person.sort_order,
            "can_login": person.can_login,
            "tasks_enabled": getattr(person, "tasks_enabled", False),
        }

    def list_agenda_managers(self, owner_person_id: int) -> list[Person]:
        pairs = (
            self.db.query(AgendaManager)
            .filter(AgendaManager.owner_person_id == owner_person_id)
            .all()
        )
        ids = [p.manager_person_id for p in pairs]
        if not ids:
            return []
        return self.db.query(Person).filter(Person.id.in_(ids)).order_by(Person.name).all()

    def set_agenda_managers(self, owner_person_id: int, manager_ids: list[int]) -> None:
        existing = (
            self.db.query(AgendaManager)
            .filter(AgendaManager.owner_person_id == owner_person_id)
            .all()
        )
        existing_ids = {p.manager_person_id for p in existing}
        desired_ids = {int(i) for i in manager_ids}
        for pair in existing:
            if pair.manager_person_id not in desired_ids:
                self.db.delete(pair)
        for mid in desired_ids:
            if mid not in existing_ids:
                self.db.add(AgendaManager(owner_person_id=owner_person_id, manager_person_id=mid))
        self.db.commit()

    def person_detail_dict(self, person: Person) -> dict:
        feeds = self.list_feeds(person.id)
        task_managers = self.list_task_managers(person.id)
        agenda_managers = self.list_agenda_managers(person.id)
        return {
            **self.person_to_dict(person),
            "has_password": bool(person.password_hash),
            "feeds": [self.feed_to_dict(feed) for feed in feeds],
            "tasks_enabled": getattr(person, "tasks_enabled", False),
            "task_manager_ids": [m.id for m in task_managers],
            "agenda_manager_ids": [m.id for m in agenda_managers],
        }

    def feed_to_dict(self, feed: PersonCalendarFeed) -> dict:
        return {
            "id": feed.id,
            "person_id": feed.person_id,
            "url": feed.url,
            "label": feed.label,
            "sync_interval_minutes": feed.sync_interval_minutes or 60,
            "prefix": feed.prefix or "",
            "color": feed.color or "",
            "show_times": bool(feed.show_times),
            "hide_title": bool(feed.hide_title),
            "last_synced_at": feed.last_synced_at.isoformat() if feed.last_synced_at else None,
            "last_error": feed.last_error,
        }
