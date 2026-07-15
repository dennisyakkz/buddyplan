import json
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.icons import LEGACY_ICON_MAP, load_icons, normalize_icon_id
from app.services.color_palette import normalize_stored_color
from app.services.dashboard_service import AgendaService, DashboardService, PersonService, TaskService
from app.services.ical_sync_service import sync_feed, sync_feed_from_content
from app.services.current_user import get_current_user, require_admin
from app.services.ical_validation import validate_ical_feed

import secrets

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Mobile app auth
# ---------------------------------------------------------------------------

class AppLoginRequest(BaseModel):
    username: str
    password: str
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None


@router.post("/auth/login")
def app_login(data: AppLoginRequest, db: Session = Depends(get_db)):
    from app.services.api_token_service import issue_token_for_device

    person = PersonService(db).verify_login(data.username.strip(), data.password)
    if not person:
        raise HTTPException(401, "Onjuiste inloggegevens")
    device_id = data.device_id.strip()
    if not device_id:
        raise HTTPException(400, "device_id is verplicht")
    try:
        plain_token = issue_token_for_device(
            db,
            person_id=person.id,
            device_id=device_id,
            device_name=data.device_name,
            device_type=data.device_type,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"token": plain_token, "person_id": person.id, "name": person.name}


def _profile_color_label(index: int) -> str:
    from app.services.color_palette import BRAND_LABELS
    return BRAND_LABELS[index % len(BRAND_LABELS)]


@router.get("/app/users")
def app_get_users(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import Person
    users = (
        db.query(Person)
        .filter(Person.tasks_enabled == True)  # noqa: E712
        .order_by(Person.sort_order, Person.id)
        .all()
    )
    svc = PersonService(db)
    return [
        {
            "id": u.id,
            "name": u.name,
            "profile_color": _profile_color_label(i),
            "can_manage_tasks": svc.can_manage_tasks(u.id, current_user.id),
        }
        for i, u in enumerate(users)
    ]


# ---------------------------------------------------------------------------
# Mobile app calendar + tasks API
# ---------------------------------------------------------------------------


@router.get("/mobile/persons")
def mobile_persons(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """All persons with brandbook profile_color label."""
    from app.models import Person
    persons = (
        db.query(Person)
        .order_by(Person.sort_order, Person.id)
        .all()
    )
    svc = PersonService(db)
    return [
        {
            "id": p.id,
            "name": p.name,
            "is_me": p.id == current_user.id,
            "profile_color": _profile_color_label(i),
            "can_manage_agenda": svc.can_manage_agenda(p.id, current_user.id),
        }
        for i, p in enumerate(persons)
    ]


@router.get("/mobile/calendar")
def mobile_calendar(
    start: date = Query(...),
    end: date = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Flat list of AgendaItems expanded over a date range."""
    from app.models import AgendaItem as _AgendaItem
    from app.models import PersonCalendarFeed as _PersonCalendarFeed
    from app.services.agenda_display import build_agenda_display_text, feed_for_item
    from app.services.recurrence import occurs_on_date as _occurs
    from datetime import timedelta as _td

    if (end - start).days > 180:
        raise HTTPException(400, "Datumbereik te groot (max 180 dagen)")

    items = db.query(_AgendaItem).all()
    feeds = {f.id: f for f in db.query(_PersonCalendarFeed).all()}
    result = []
    cursor = start
    while cursor <= end:
        for item in items:
            if _occurs(item.repeat_type, item.get_weekdays(), item.anchor_date, item.end_date, cursor):
                feed = feed_for_item(item, feeds)
                result.append({
                    "id": item.id,
                    "title": build_agenda_display_text(item, feed),
                    "person_id": item.person_id,
                    "date": cursor.isoformat(),
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                    "source": item.source,
                })
        cursor += _td(days=1)
    return result


@router.get("/mobile/tasks")
def mobile_tasks(
    start: date = Query(...),
    end: date = Query(...),
    person_id: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tasks expanded over a date range, optionally filtered by person."""
    from datetime import timedelta as _td

    if (end - start).days > 180:
        raise HTTPException(400, "Datumbereik te groot (max 180 dagen)")

    svc = TaskService(db)
    result = []
    cursor = start
    while cursor <= end:
        day_tasks = svc.get_for_date(cursor, person_id)
        for t in day_tasks:
            result.append({
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "icon": t.icon,
                "person_id": t.person_id,
                "date": cursor.isoformat(),
                "completed": svc.task_to_dict(t, cursor).get("completed", False),
            })
        cursor += _td(days=1)
    return result


@router.get("/mobile/calendar/{item_id}")
def mobile_calendar_item(
    item_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full agenda item for mobile detail/edit screen."""
    item = AgendaService(db).get(item_id)
    if not item:
        raise HTTPException(404, "Agenda-item niet gevonden")
    return {
        "id": item.id,
        "person_id": item.person_id,
        "title": item.title,
        "source": item.source,
        "repeat_type": item.repeat_type,
        "repeat_weekdays": item.get_weekdays(),
        "anchor_date": item.anchor_date.isoformat() if item.anchor_date else None,
        "end_date": item.end_date.isoformat() if item.end_date else None,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "is_read_only": item.source in ("ical", "gcal"),
    }


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    icon: str = "default"
    repeat_type: str = "once"
    repeat_weekdays: list[int] = []
    anchor_date: str
    end_date: Optional[str] = None
    sort_order: int = 0


class TaskUpdate(TaskCreate):
    pass


class ReorderRequest(BaseModel):
    date: str
    task_ids: list[int]


class MoveTaskRequest(BaseModel):
    task_id: int
    from_date: str
    to_date: str


class AgendaCreate(BaseModel):
    person_id: int
    title: str
    repeat_type: str = "once"
    repeat_weekdays: list[int] = []
    anchor_date: str
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    sort_order: int = 0


class AgendaUpdate(BaseModel):
    title: Optional[str] = None
    repeat_type: Optional[str] = None
    repeat_weekdays: Optional[list[int]] = None
    anchor_date: Optional[str] = None
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    sort_order: Optional[int] = None


class PersonCreate(BaseModel):
    name: str


class PersonUpdate(BaseModel):
    name: str
    can_login: bool = False
    password: Optional[str] = None
    password_confirm: Optional[str] = None


class PersonFeedCreate(BaseModel):
    url: str
    label: str = ""
    sync_interval_minutes: int = 60
    prefix: str = ""
    color: str = ""
    show_times: bool = False
    hide_title: bool = False


class MeUpdate(BaseModel):
    name: str
    email: Optional[str] = None


class PasswordUpdate(BaseModel):
    password: str
    password_confirm: str


class UserFeedCreate(BaseModel):
    url: str
    label: str = ""
    sync_interval_minutes: int = 60
    prefix: str = ""
    color: str = ""
    show_times: bool = False
    hide_title: bool = False


class AdminUserCreate(BaseModel):
    username: str
    name: str
    email: Optional[str] = None
    is_admin: bool = False
    can_login: bool = False
    password: Optional[str] = None
    password_confirm: Optional[str] = None


class AdminUserUpdate(AdminUserCreate):
    pass


class TaskManagersUpdate(BaseModel):
    tasks_enabled: bool
    manager_ids: list[int] = []


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def _task_payload(data: TaskCreate | TaskUpdate) -> dict:
    anchor = _parse_date(data.anchor_date)
    if not anchor:
        raise HTTPException(400, "Datum is verplicht")
    return {
        "title": data.title,
        "description": data.description,
        "icon": data.icon,
        "repeat_type": data.repeat_type,
        "repeat_weekdays": json.dumps(data.repeat_weekdays),
        "anchor_date": anchor,
        "start_date": None,
        "end_date": _parse_date(data.end_date),
        "sort_order": data.sort_order,
    }


def _agenda_payload(data: AgendaCreate) -> dict:
    anchor = _parse_date(data.anchor_date)
    if not anchor:
        raise HTTPException(400, "Datum is verplicht")
    return {
        "person_id": data.person_id,
        "title": data.title,
        "repeat_type": data.repeat_type,
        "repeat_weekdays": json.dumps(data.repeat_weekdays),
        "anchor_date": anchor,
        "start_date": None,
        "end_date": _parse_date(data.end_date),
        "start_time": data.start_time,
        "end_time": data.end_time,
        "sort_order": data.sort_order,
    }


@router.get("/icons")
def list_icons():
    return load_icons()


@router.get("/dashboard")
def get_dashboard(
    response: Response,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    if end_date:
        start = _parse_date(start_date) if start_date else None
        end = _parse_date(end_date)
        if not start or not end:
            raise HTTPException(400, "start_date en end_date zijn verplicht voor een datumbereik")
        if end < start:
            raise HTTPException(400, "end_date moet op of na start_date liggen")
        if (end - start).days > 83:
            raise HTTPException(400, "Datumbereik te groot (max 12 weken)")
        etag = service.get_etag()
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        return service.build_dashboard_range(start, end)

    reference = _parse_date(start_date) if start_date else None
    etag = service.get_etag(reference)
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return service.build_dashboard(reference)


@router.get("/dashboard/etag")
def get_dashboard_etag(response: Response, _user=Depends(get_current_user), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return {"etag": DashboardService(db).get_etag()}



@router.get("/tasks")
def list_tasks(
    date_str: Optional[str] = Query(None, alias="date"),
    person_id: Optional[int] = Query(None),
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models import TaskDayOrder

    service = TaskService(db)
    target = _parse_date(date_str) or date.today()
    tasks = service.get_for_date(target, person_id=person_id)
    day_orders = {
        o.task_id: o.sort_order
        for o in db.query(TaskDayOrder).filter(TaskDayOrder.order_date == target).all()
    }
    tasks.sort(key=lambda t: (day_orders.get(t.id, t.sort_order), t.id))
    return [service.task_to_dict(t, target) for t in tasks]


@router.get("/tasks/access")
def task_access(person_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return {"can_manage": PersonService(db).can_manage_tasks(person_id, user.id)}


@router.get("/tasks/{task_id}")
def get_task(task_id: int, _user=Depends(get_current_user), db: Session = Depends(get_db)):
    task = TaskService(db).get(task_id)
    if not task:
        raise HTTPException(404, "Taak niet gevonden")
    return TaskService(db).task_to_dict(task)


@router.post("/tasks")
def create_task(
    data: TaskCreate,
    person_id: int = Query(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not PersonService(db).can_manage_tasks(person_id, user.id):
        raise HTTPException(403, "Geen rechten om taken te beheren voor deze gebruiker")
    payload = _task_payload(data)
    payload["person_id"] = person_id
    task = TaskService(db).create(payload)
    return TaskService(db).task_to_dict(task)


@router.put("/tasks/reorder")
def reorder_tasks(
    data: ReorderRequest,
    person_id: int = Query(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = _parse_date(data.date)
    if not target:
        raise HTTPException(400, "Ongeldige datum")
    if not PersonService(db).can_manage_tasks(person_id, user.id):
        raise HTTPException(403, "Geen rechten om taken te beheren voor deze gebruiker")
    TaskService(db).reorder_for_date(target, data.task_ids)
    return {"ok": True}


@router.put("/tasks/move")
def move_task(
    data: MoveTaskRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from_date = _parse_date(data.from_date)
    to_date = _parse_date(data.to_date)
    if not from_date or not to_date:
        raise HTTPException(400, "Ongeldige datum")
    task = TaskService(db).get(data.task_id)
    if not task:
        raise HTTPException(404, "Taak niet gevonden")
    if task.person_id is None or not PersonService(db).can_manage_tasks(task.person_id, user.id):
        raise HTTPException(403, "Geen rechten om taken te beheren voor deze gebruiker")
    if not TaskService(db).move_to_date(data.task_id, from_date, to_date):
        raise HTTPException(404, "Taak niet gevonden")
    return {"ok": True}


@router.put("/tasks/{task_id}")
def update_task(task_id: int, data: TaskUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    existing = TaskService(db).get(task_id)
    if not existing:
        raise HTTPException(404, "Taak niet gevonden")
    if existing.person_id is None or not PersonService(db).can_manage_tasks(existing.person_id, user.id):
        raise HTTPException(403, "Geen rechten om taken te beheren voor deze gebruiker")
    task = TaskService(db).update(task_id, _task_payload(data))
    if not task:
        raise HTTPException(404, "Taak niet gevonden")
    return TaskService(db).task_to_dict(task)


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    existing = TaskService(db).get(task_id)
    if not existing:
        raise HTTPException(404, "Taak niet gevonden")
    if existing.person_id is None or not PersonService(db).can_manage_tasks(existing.person_id, user.id):
        raise HTTPException(403, "Geen rechten om taken te beheren voor deze gebruiker")
    if not TaskService(db).delete(task_id):
        raise HTTPException(404, "Taak niet gevonden")
    return {"ok": True}


@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    date_str: Optional[str] = Query(None, alias="date"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = _parse_date(date_str) or date.today()
    existing = TaskService(db).get(task_id)
    if not existing:
        raise HTTPException(404, "Taak niet gevonden")
    if existing.person_id is None or not PersonService(db).can_manage_tasks(existing.person_id, user.id):
        raise HTTPException(403, "Geen rechten om taken te beheren voor deze gebruiker")
    if not TaskService(db).mark_complete(task_id, target):
        raise HTTPException(404, "Taak niet gevonden")
    return {"ok": True}


@router.get("/agenda/access")
def agenda_access(person_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return {"can_manage": PersonService(db).can_manage_agenda(person_id, user.id)}


@router.get("/agenda")
def list_agenda(
    person_id: int = Query(...),
    date_str: Optional[str] = Query(None, alias="date"),
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AgendaService(db)
    target = _parse_date(date_str) or date.today()
    items = service.get_for_date(person_id, target)
    feeds, google_feeds = service.feed_maps_for_person(person_id)
    return [service.item_to_dict(i, feeds=feeds, google_feeds=google_feeds) for i in items]


@router.post("/agenda")
def create_agenda_item(data: AgendaCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not PersonService(db).can_manage_agenda(data.person_id, user.id):
        raise HTTPException(403, "Geen rechten om agenda te beheren voor deze gebruiker")
    item = AgendaService(db).create(_agenda_payload(data))
    return AgendaService(db).item_to_dict(item)


@router.put("/agenda/{item_id}")
def update_agenda_item(item_id: int, data: AgendaUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    existing = AgendaService(db).get(item_id)
    if not existing:
        raise HTTPException(404, "Agenda-item niet gevonden")
    if not PersonService(db).can_manage_agenda(existing.person_id, user.id):
        raise HTTPException(403, "Geen rechten om agenda te beheren voor deze gebruiker")
    if existing.source in ("ical", "gcal"):
        raise HTTPException(403, "Agenda-items uit een feed kunnen niet worden bewerkt")
    dumped = data.model_dump(exclude_unset=True)
    payload = {
        k: v for k, v in dumped.items()
        if v is not None and k not in ("start_time", "end_time")
    }
    for time_key in ("start_time", "end_time"):
        if time_key in dumped:
            payload[time_key] = dumped[time_key] or None
    if "repeat_weekdays" in payload:
        payload["repeat_weekdays"] = json.dumps(payload["repeat_weekdays"])
    if "anchor_date" in payload:
        parsed = _parse_date(payload["anchor_date"])
        if not parsed:
            raise HTTPException(400, "Datum is verplicht")
        payload["anchor_date"] = parsed
    if "end_date" in payload:
        payload["end_date"] = _parse_date(payload["end_date"])
    payload["start_date"] = None
    item = AgendaService(db).update(item_id, payload)
    if not item:
        raise HTTPException(404, "Agenda-item niet gevonden")
    return AgendaService(db).item_to_dict(item)


@router.delete("/agenda/{item_id}")
def delete_agenda_item(item_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    existing = AgendaService(db).get(item_id)
    if not existing:
        raise HTTPException(404, "Agenda-item niet gevonden")
    if not PersonService(db).can_manage_agenda(existing.person_id, user.id):
        raise HTTPException(403, "Geen rechten om agenda te beheren voor deze gebruiker")
    if existing.source in ("ical", "gcal"):
        raise HTTPException(403, "Agenda-items uit een feed kunnen niet worden verwijderd")
    if not AgendaService(db).delete(item_id):
        raise HTTPException(404, "Agenda-item niet gevonden")
    return {"ok": True}


@router.get("/persons")
def list_persons(_user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = PersonService(db)
    return [service.person_to_dict(p) for p in service.list_all()]


@router.post("/persons")
def create_person(data: PersonCreate, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    person = PersonService(db).create(data.name)
    return PersonService(db).person_to_dict(person)


@router.get("/persons/{person_id}")
def get_person(person_id: int, _user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = PersonService(db)
    person = service.get(person_id)
    if not person:
        raise HTTPException(404, "Persoon niet gevonden")
    return service.person_detail_dict(person)


@router.put("/persons/{person_id}")
def update_person(person_id: int, data: PersonUpdate, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    service = PersonService(db)
    person = service.get(person_id)
    if not person:
        raise HTTPException(404, "Persoon niet gevonden")

    password = None
    if data.can_login:
        if data.password:
            if data.password != data.password_confirm:
                raise HTTPException(400, "Wachtwoorden komen niet overeen")
            if len(data.password) < 4:
                raise HTTPException(400, "Wachtwoord moet minimaal 4 tekens zijn")
            password = data.password
        elif not person.password_hash:
            raise HTTPException(400, "Wachtwoord is verplicht bij inloggen")

    updated = service.update(person_id, data.name.strip(), data.can_login, password)
    if not updated:
        raise HTTPException(404, "Persoon niet gevonden")
    return service.person_detail_dict(updated)


@router.post("/persons/{person_id}/feeds")
def add_person_feed(person_id: int, data: PersonFeedCreate, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    url = data.url.strip()
    if not url:
        raise HTTPException(400, "iCal URL is verplicht")
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(400, "Ongeldige URL")

    service = PersonService(db)
    feed = service.add_feed(person_id, url, data.label)
    if not feed:
        raise HTTPException(404, "Persoon niet gevonden")

    try:
        content = validate_ical_feed(url)
        sync_feed_from_content(db, feed.id, content)
    except Exception as exc:
        db.refresh(feed)
        return {
            **service.feed_to_dict(feed),
            "sync_warning": str(exc),
        }

    db.refresh(feed)
    return service.feed_to_dict(feed)


@router.delete("/persons/{person_id}/feeds/{feed_id}")
def delete_person_feed(person_id: int, feed_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    if not PersonService(db).delete_feed(person_id, feed_id):
        raise HTTPException(404, "Kalender niet gevonden")
    return {"ok": True}


@router.post("/persons/{person_id}/feeds/{feed_id}/sync")
def sync_person_feed(person_id: int, feed_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    service = PersonService(db)
    feeds = service.list_feeds(person_id)
    if not any(f.id == feed_id for f in feeds):
        raise HTTPException(404, "Kalender niet gevonden")
    try:
        count = sync_feed(db, feed_id, force_full=True)
        feed = next(f for f in service.list_feeds(person_id) if f.id == feed_id)
        return {"ok": True, "imported": count, "feed": service.feed_to_dict(feed)}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.delete("/persons/{person_id}")
def delete_person(person_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    if not PersonService(db).delete(person_id):
        raise HTTPException(404, "Persoon niet gevonden")
    return {"ok": True}


@router.get("/me")
def get_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = PersonService(db)
    return service.person_detail_dict(user)


@router.put("/me")
def update_me(data: MeUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not data.name.strip():
        raise HTTPException(400, "Naam is verplicht")
    service = PersonService(db)
    updated = service.update_user_fields(user.id, user.username, data.email, user.is_admin)
    if not updated:
        raise HTTPException(404, "Gebruiker niet gevonden")
    updated = service.update(user.id, data.name.strip(), user.can_login, None)
    return service.person_detail_dict(updated)


@router.put("/me/password")
def update_my_password(data: PasswordUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if data.password != data.password_confirm:
        raise HTTPException(400, "Wachtwoorden komen niet overeen")
    if len(data.password) < 4:
        raise HTTPException(400, "Wachtwoord moet minimaal 4 tekens zijn")
    updated = PersonService(db).update(user.id, user.name, True, data.password)
    if not updated:
        raise HTTPException(404, "Gebruiker niet gevonden")
    return {"ok": True}


def _bearer_token_hash(request: Request) -> str | None:
    from app.services.token_utils import hash_api_token

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token_str = auth_header[7:].strip()
        if token_str:
            return hash_api_token(token_str)
    return None


@router.get("/me/devices")
def list_my_devices(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.api_token_service import device_to_dict, list_active_devices

    current_hash = _bearer_token_hash(request)
    records = list_active_devices(db, user.id)
    return [
        device_to_dict(record, current_token_hash=current_hash)
        for record in records
    ]


@router.delete("/me/devices/{device_id}")
def revoke_my_device(
    device_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.api_token_service import revoke_device

    if not revoke_device(db, person_id=user.id, device_id=device_id):
        raise HTTPException(404, "Apparaat niet gevonden")
    return {"ok": True}


@router.post("/me/feeds")
def add_my_feed(data: UserFeedCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    url = data.url.strip()
    if not url:
        raise HTTPException(400, "iCal URL is verplicht")
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(400, "Ongeldige URL")
    try:
        validate_ical_feed(url)
    except Exception as exc:
        raise HTTPException(400, f"iCal test faalde: {exc}") from exc
    service = PersonService(db)
    interval = data.sync_interval_minutes if data.sync_interval_minutes in {15, 60, 1440} else 60
    feed = service.add_feed(user.id, url, data.label, interval, data.prefix, data.color, data.show_times, data.hide_title)
    if not feed:
        raise HTTPException(404, "Gebruiker niet gevonden")
    return service.feed_to_dict(feed)


@router.put("/me/feeds/{feed_id}")
def update_my_feed(feed_id: int, data: UserFeedCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    url = data.url.strip()
    if not url:
        raise HTTPException(400, "iCal URL is verplicht")
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(400, "Ongeldige URL")
    service = PersonService(db)
    existing = next((f for f in service.list_feeds(user.id) if f.id == feed_id), None)
    if not existing:
        raise HTTPException(404, "Kalender niet gevonden")
    if url != existing.url:
        try:
            validate_ical_feed(url)
        except Exception as exc:
            raise HTTPException(400, f"iCal test faalde: {exc}") from exc
    interval = data.sync_interval_minutes if data.sync_interval_minutes in {15, 60, 1440} else 60
    feed = service.update_feed(user.id, feed_id, url, data.label, interval, data.prefix, data.color, data.show_times, data.hide_title)
    if not feed:
        raise HTTPException(404, "Kalender niet gevonden")
    return service.feed_to_dict(feed)


@router.post("/me/feeds/{feed_id}/sync")
def sync_my_feed(feed_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = PersonService(db)
    feeds = service.list_feeds(user.id)
    if not any(f.id == feed_id for f in feeds):
        raise HTTPException(404, "Kalender niet gevonden")
    try:
        count = sync_feed(db, feed_id, force_full=True)
        feed = next(f for f in service.list_feeds(user.id) if f.id == feed_id)
        return {"ok": True, "imported": count, "feed": service.feed_to_dict(feed)}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.delete("/me/feeds/{feed_id}")
def delete_my_feed(feed_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Validation on delete (best effort)
    warning = None
    service = PersonService(db)
    feeds = service.list_feeds(user.id)
    feed = next((f for f in feeds if f.id == feed_id), None)
    if not feed:
        raise HTTPException(404, "Kalender niet gevonden")
    try:
        validate_ical_feed(feed.url)
    except Exception as exc:
        warning = str(exc)
    if not service.delete_feed(user.id, feed_id):
        raise HTTPException(404, "Kalender niet gevonden")
    return {"ok": True, "validation_warning": warning}


@router.get("/admin/users")
def admin_list_users(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    service = PersonService(db)
    return [service.person_to_dict(p) for p in service.list_all()]

@router.get("/admin/users/{user_id}")
def admin_get_user(user_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    service = PersonService(db)
    person = service.get(user_id)
    if not person:
        raise HTTPException(404, "Gebruiker niet gevonden")
    return service.person_detail_dict(person)


@router.post("/admin/users")
def admin_create_user(data: AdminUserCreate, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    if not data.username.strip():
        raise HTTPException(400, "Username is verplicht")
    if not data.name.strip():
        raise HTTPException(400, "Naam is verplicht")
    if data.can_login:
        if not data.password:
            raise HTTPException(400, "Wachtwoord is verplicht bij inloggen")
        if data.password != data.password_confirm:
            raise HTTPException(400, "Wachtwoorden komen niet overeen")

    service = PersonService(db)
    # create Person with display name
    person = service.create(data.name.strip())
    # set user fields
    try:
        service.update_user_fields(person.id, data.username.strip(), data.email, data.is_admin)
    except IntegrityError:
        db.rollback()
        service.delete(person.id)
        raise HTTPException(400, "Username of e-mail bestaat al")
    # set login
    service.update(person.id, data.name.strip(), data.can_login, data.password)
    return service.person_to_dict(service.get(person.id))


@router.put("/admin/users/{user_id}")
def admin_update_user(
    user_id: int,
    data: AdminUserUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    if not data.username.strip():
        raise HTTPException(400, "Username is verplicht")
    if not data.name.strip():
        raise HTTPException(400, "Naam is verplicht")
    service = PersonService(db)
    person = service.get(user_id)
    if not person:
        raise HTTPException(404, "Gebruiker niet gevonden")

    try:
        service.update_user_fields(user_id, data.username.strip(), data.email, data.is_admin)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Username of e-mail bestaat al")

    password = None
    if data.can_login and data.password:
        if data.password != data.password_confirm:
            raise HTTPException(400, "Wachtwoorden komen niet overeen")
        password = data.password
    updated = service.update(user_id, data.name.strip(), data.can_login, password)
    return service.person_to_dict(updated)

@router.put("/admin/users/{user_id}/task-managers")
def admin_update_task_managers(
    user_id: int,
    data: TaskManagersUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = PersonService(db)
    person = service.get(user_id)
    if not person:
        raise HTTPException(404, "Gebruiker niet gevonden")
    service.set_tasks_enabled(user_id, data.tasks_enabled)
    if data.tasks_enabled:
        service.set_task_managers(user_id, data.manager_ids)
    else:
        service.set_task_managers(user_id, [])
    return service.person_detail_dict(service.get(user_id))


class AgendaManagersUpdate(BaseModel):
    manager_ids: list[int] = []


@router.put("/admin/users/{user_id}/agenda-managers")
def admin_update_agenda_managers(
    user_id: int,
    data: AgendaManagersUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = PersonService(db)
    if not service.get(user_id):
        raise HTTPException(404, "Gebruiker niet gevonden")
    service.set_agenda_managers(user_id, data.manager_ids)
    return service.person_detail_dict(service.get(user_id))


@router.post("/admin/users/{user_id}/feeds")
def admin_add_user_feed(
    user_id: int,
    data: UserFeedCreate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    url = data.url.strip()
    if not url:
        raise HTTPException(400, "iCal URL is verplicht")
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(400, "Ongeldige URL")
    try:
        validate_ical_feed(url)
    except Exception as exc:
        raise HTTPException(400, f"iCal test faalde: {exc}") from exc
    interval = data.sync_interval_minutes if data.sync_interval_minutes in {15, 60, 1440} else 60
    service = PersonService(db)
    feed = service.add_feed(user_id, url, data.label, interval, data.prefix, data.color, data.show_times, data.hide_title)
    if not feed:
        raise HTTPException(404, "Gebruiker niet gevonden")
    return service.feed_to_dict(feed)


@router.put("/admin/users/{user_id}/feeds/{feed_id}")
def admin_update_user_feed(
    user_id: int,
    feed_id: int,
    data: UserFeedCreate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    url = data.url.strip()
    if not url:
        raise HTTPException(400, "iCal URL is verplicht")
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(400, "Ongeldige URL")
    service = PersonService(db)
    existing = next((f for f in service.list_feeds(user_id) if f.id == feed_id), None)
    if not existing:
        raise HTTPException(404, "Kalender niet gevonden")
    if url != existing.url:
        try:
            validate_ical_feed(url)
        except Exception as exc:
            raise HTTPException(400, f"iCal test faalde: {exc}") from exc
    interval = data.sync_interval_minutes if data.sync_interval_minutes in {15, 60, 1440} else 60
    feed = service.update_feed(user_id, feed_id, url, data.label, interval, data.prefix, data.color, data.show_times, data.hide_title)
    if not feed:
        raise HTTPException(404, "Kalender niet gevonden")
    return service.feed_to_dict(feed)


@router.post("/admin/users/{user_id}/feeds/{feed_id}/sync")
def admin_sync_user_feed(
    user_id: int,
    feed_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = PersonService(db)
    feeds = service.list_feeds(user_id)
    if not any(f.id == feed_id for f in feeds):
        raise HTTPException(404, "Kalender niet gevonden")
    try:
        count = sync_feed(db, feed_id, force_full=True)
        feed = next(f for f in service.list_feeds(user_id) if f.id == feed_id)
        return {"ok": True, "imported": count, "feed": service.feed_to_dict(feed)}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.delete("/admin/users/{user_id}/feeds/{feed_id}")
def admin_delete_user_feed(
    user_id: int,
    feed_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = PersonService(db)
    feeds = service.list_feeds(user_id)
    feed = next((f for f in feeds if f.id == feed_id), None)
    if not feed:
        raise HTTPException(404, "Kalender niet gevonden")
    warning = None
    try:
        validate_ical_feed(feed.url)
    except Exception as exc:
        warning = str(exc)
    if not service.delete_feed(user_id, feed_id):
        raise HTTPException(404, "Kalender niet gevonden")
    return {"ok": True, "validation_warning": warning}


@router.get("/admin/users/{user_id}/devices")
def admin_list_user_devices(
    user_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.services.api_token_service import device_to_dict, list_active_devices

    if not PersonService(db).get(user_id):
        raise HTTPException(404, "Gebruiker niet gevonden")
    records = list_active_devices(db, user_id)
    return [device_to_dict(record) for record in records]


@router.delete("/admin/users/{user_id}/devices/{device_id}")
def admin_revoke_user_device(
    user_id: int,
    device_id: str,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.services.api_token_service import revoke_device

    if not PersonService(db).get(user_id):
        raise HTTPException(404, "Gebruiker niet gevonden")
    if not revoke_device(db, person_id=user_id, device_id=device_id):
        raise HTTPException(404, "Apparaat niet gevonden")
    return {"ok": True}


@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    if not PersonService(db).delete(user_id):
        raise HTTPException(404, "Gebruiker niet gevonden")
    return {"ok": True}


# ── Afvalwijzer ──────────────────────────────────────────────────────────────

class AfvalwijzerConfigUpdate(BaseModel):
    enabled: bool
    postcode: str = ""
    huisnummer: str = ""


class AfvalwijzerTypeUpdate(BaseModel):
    enabled: bool = False
    naam: str = ""
    buiten_dag: str = "day_before"
    buiten_person_id: Optional[int] = None
    buiten_icon: str = "fas:trash"
    binnen_dag: str = "same_day"
    binnen_person_id: Optional[int] = None
    binnen_icon: str = "fas:trash"


class AfvalwijzerTypePatch(BaseModel):
    enabled: Optional[bool] = None
    naam: Optional[str] = None
    buiten_dag: Optional[str] = None
    buiten_person_id: Optional[int] = None
    buiten_icon: Optional[str] = None
    binnen_dag: Optional[str] = None
    binnen_person_id: Optional[int] = None
    binnen_icon: Optional[str] = None


@router.get("/admin/afvalwijzer")
def admin_get_afvalwijzer(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    from app.services.afvalwijzer_service import AfvalwijzerService
    service = AfvalwijzerService(db)
    return service.config_to_dict(service.get_or_create_config())


@router.put("/admin/afvalwijzer")
def admin_update_afvalwijzer(
    data: AfvalwijzerConfigUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.services.afvalwijzer_service import AfvalwijzerService
    service = AfvalwijzerService(db)
    config = service.update_config(
        data.enabled,
        data.postcode.strip() or None,
        data.huisnummer.strip() or None,
    )
    return service.config_to_dict(config)


@router.post("/admin/afvalwijzer/sync")
def admin_sync_afvalwijzer(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    from app.services.afvalwijzer_service import AfvalwijzerService
    from app.services.mijnafvalwijzer import get_afval_types
    service = AfvalwijzerService(db)
    config = service.get_or_create_config()
    if not config.postcode or not config.huisnummer:
        raise HTTPException(400, "Postcode en huisnummer zijn verplicht")
    try:
        types = get_afval_types(config.postcode, config.huisnummer)
    except Exception as exc:
        raise HTTPException(400, f"Ophalen mislukt: {exc}") from exc
    config = service.sync_types(types)
    return service.config_to_dict(config)


@router.put("/admin/afvalwijzer/types/{type_id}")
def admin_update_afvalwijzer_type(
    type_id: int,
    data: AfvalwijzerTypeUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.services.afvalwijzer_service import AfvalwijzerService
    service = AfvalwijzerService(db)
    t = service.update_type(
        type_id,
        enabled=data.enabled,
        naam=data.naam,
        buiten_dag=data.buiten_dag,
        buiten_person_id=data.buiten_person_id,
        buiten_icon=data.buiten_icon,
        binnen_dag=data.binnen_dag,
        binnen_person_id=data.binnen_person_id,
        binnen_icon=data.binnen_icon,
    )
    if not t:
        raise HTTPException(404, "Afvaltype niet gevonden")
    return service.type_to_dict(t)


@router.patch("/admin/afvalwijzer/types/{type_id}")
def admin_patch_afvalwijzer_type(
    type_id: int,
    data: AfvalwijzerTypePatch,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.services.afvalwijzer_service import AfvalwijzerService
    service = AfvalwijzerService(db)
    kwargs = {}
    if data.enabled is not None:
        kwargs["enabled"] = data.enabled
    if data.naam is not None:
        kwargs["naam"] = data.naam
    if data.buiten_dag is not None:
        kwargs["buiten_dag"] = data.buiten_dag
    if data.buiten_person_id is not None:
        kwargs["buiten_person_id"] = data.buiten_person_id
    if data.buiten_icon is not None:
        kwargs["buiten_icon"] = data.buiten_icon
    if data.binnen_dag is not None:
        kwargs["binnen_dag"] = data.binnen_dag
    if data.binnen_person_id is not None:
        kwargs["binnen_person_id"] = data.binnen_person_id
    if data.binnen_icon is not None:
        kwargs["binnen_icon"] = data.binnen_icon
    t = service.update_type(type_id, **kwargs)
    if not t:
        raise HTTPException(404, "Afvaltype niet gevonden")
    return service.type_to_dict(t)


@router.post("/admin/afvalwijzer/create-tasks")
def admin_create_afval_tasks(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    from app.services.afvalwijzer_service import AfvalwijzerService
    service = AfvalwijzerService(db)
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    next_monday = monday + timedelta(weeks=1)
    try:
        count = service.create_tasks_for_weeks([monday, next_monday])
        return {"created": count}
    except Exception as exc:
        raise HTTPException(400, f"Aanmaken mislukt: {exc}") from exc


# ---------------------------------------------------------------------------
# Google Calendar – admin API config
# ---------------------------------------------------------------------------

class GoogleApiConfigUpdate(BaseModel):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri_override: str = ""


@router.get("/admin/google-calendar/config")
def admin_get_google_config(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    from app.models import GoogleApiConfig
    cfg = db.query(GoogleApiConfig).first()
    if not cfg:
        return {"client_id": "", "client_secret": "", "redirect_uri_override": ""}
    return {
        "client_id": cfg.client_id or "",
        "client_secret": cfg.client_secret or "",
        "redirect_uri_override": cfg.redirect_uri_override or "",
    }


@router.put("/admin/google-calendar/config")
def admin_update_google_config(
    data: GoogleApiConfigUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.models import GoogleApiConfig
    cfg = db.query(GoogleApiConfig).first()
    if not cfg:
        cfg = GoogleApiConfig()
        db.add(cfg)
    cfg.client_id = data.client_id.strip() or None
    cfg.client_secret = data.client_secret.strip() or None
    cfg.redirect_uri_override = data.redirect_uri_override.strip() or None
    db.commit()
    return {"client_id": cfg.client_id or "", "client_secret": cfg.client_secret or "", "redirect_uri_override": cfg.redirect_uri_override or ""}


# ---------------------------------------------------------------------------
# Google Calendar – shared helpers
# ---------------------------------------------------------------------------

def _resolve_redirect_uri(request, db: Session) -> str:
    from app.models import GoogleApiConfig
    cfg = db.query(GoogleApiConfig).first()
    if cfg and cfg.redirect_uri_override:
        return cfg.redirect_uri_override
    base = str(request.base_url).rstrip("/")
    return f"{base}/google/callback"


def _get_google_config(db: Session):
    from app.models import GoogleApiConfig
    cfg = db.query(GoogleApiConfig).first()
    if not cfg or not cfg.client_id or not cfg.client_secret:
        raise HTTPException(400, "Google Calendar API is niet geconfigureerd. Stel de API-instellingen in via het admin menu.")
    return cfg


def _google_auth_url_for_person(person_id: int, return_to: str, request, db: Session) -> str:
    from app.services.google_calendar_service import get_auth_url
    cfg = _get_google_config(db)
    redirect_uri = _resolve_redirect_uri(request, db)
    request.session["gcal_oauth_person_id"] = person_id
    request.session["gcal_oauth_return_to"] = return_to
    import secrets
    nonce = secrets.token_urlsafe(16)
    request.session["gcal_oauth_nonce"] = nonce
    return get_auth_url(cfg.client_id, redirect_uri, state=nonce)


def _get_or_create_google_auth(db: Session, person_id: int):
    from app.models import PersonGoogleAuth
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == person_id).first()
    if not auth:
        auth = PersonGoogleAuth(person_id=person_id)
        db.add(auth)
        db.flush()
    return auth


def _google_feeds_for_person(db: Session, person_id: int) -> list[dict]:
    from app.models import PersonGoogleCalendarFeed
    feeds = db.query(PersonGoogleCalendarFeed).filter(
        PersonGoogleCalendarFeed.person_id == person_id
    ).all()
    return [_google_feed_to_dict(f) for f in feeds]


def _google_feed_to_dict(feed) -> dict:
    import json as _json
    return {
        "id": feed.id,
        "google_calendar_id": feed.google_calendar_id,
        "calendar_name": feed.calendar_name,
        "calendar_color": feed.calendar_color,
        "color_filters": _json.loads(feed.color_filters) if feed.color_filters else [],
        "enabled": feed.enabled,
        "last_synced_at": feed.last_synced_at.isoformat() if feed.last_synced_at else None,
        "last_error": feed.last_error,
    }


def _get_google_feed_or_404(db: Session, feed_id: int, person_id: int):
    from app.models import PersonGoogleCalendarFeed
    feed = db.query(PersonGoogleCalendarFeed).filter(
        PersonGoogleCalendarFeed.id == feed_id,
        PersonGoogleCalendarFeed.person_id == person_id,
    ).first()
    if not feed:
        raise HTTPException(404, "Google calendar feed niet gevonden")
    return feed


def _run_google_feed_sync(db: Session, feed, *, full_sync: bool = False) -> None:
    from app.models import GoogleApiConfig
    from app.services.google_sync_service import _sync_feed

    config = db.query(GoogleApiConfig).first()
    if not config or not config.client_id:
        return
    _sync_feed(db, feed, config, full_sync=full_sync)
    db.refresh(feed)


# ---------------------------------------------------------------------------
# Google Calendar – /api/me/google/…
# ---------------------------------------------------------------------------

@router.get("/google/colors")
def get_google_colors():
    from app.services.google_calendar_service import GOOGLE_COLORS
    return GOOGLE_COLORS


@router.get("/me/google/status")
def me_google_status(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import PersonGoogleAuth
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == current_user.id).first()
    return {
        "linked": bool(auth and auth.refresh_token),
        "google_email": auth.google_email if auth else None,
    }


@router.get("/me/google/auth-url")
def me_google_auth_url(
    request: Request,
    return_to: str = "/profile",
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = _google_auth_url_for_person(current_user.id, return_to, request, db)
    return {"auth_url": url}


@router.delete("/me/google/auth")
def me_google_unlink(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import PersonGoogleAuth
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == current_user.id).first()
    if auth:
        db.delete(auth)
        db.commit()
    return {"ok": True}


@router.get("/me/google/calendars")
def me_google_list_calendars(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import PersonGoogleAuth
    from app.services.google_calendar_service import list_calendars
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == current_user.id).first()
    if not auth or not auth.refresh_token:
        raise HTTPException(400, "Google account niet gekoppeld")
    cfg = _get_google_config(db)
    access_token = _ensure_gcal_token(db, auth, cfg)
    try:
        cals = list_calendars(access_token)
    except Exception as exc:
        raise HTTPException(400, f"Ophalen agenda's mislukt: {exc}") from exc
    return [{"id": c["id"], "summary": c.get("summary", ""), "backgroundColor": c.get("backgroundColor", "")} for c in cals]


@router.get("/me/google/feeds")
def me_google_feeds(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return _google_feeds_for_person(db, current_user.id)


class GoogleFeedCreate(BaseModel):
    google_calendar_id: str
    calendar_name: str = ""
    calendar_color: Optional[str] = None
    color_filters: list[str] = []
    enabled: bool = True


class GoogleFeedUpdate(BaseModel):
    calendar_name: Optional[str] = None
    calendar_color: Optional[str] = None
    color_filters: Optional[list[str]] = None
    enabled: Optional[bool] = None


@router.post("/me/google/feeds")
def me_google_add_feed(
    data: GoogleFeedCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import json as _json
    from app.models import PersonGoogleAuth, PersonGoogleCalendarFeed
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == current_user.id).first()
    if not auth or not auth.refresh_token:
        raise HTTPException(400, "Google account niet gekoppeld")
    feed = PersonGoogleCalendarFeed(
        person_id=current_user.id,
        auth_id=auth.id,
        google_calendar_id=data.google_calendar_id,
        calendar_name=data.calendar_name,
        calendar_color=normalize_stored_color(data.calendar_color),
        color_filters=_json.dumps(data.color_filters) if data.color_filters else None,
        enabled=data.enabled,
    )
    db.add(feed)
    db.commit()
    return _google_feed_to_dict(feed)


@router.put("/me/google/feeds/{feed_id}")
def me_google_update_feed(
    feed_id: int,
    data: GoogleFeedUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import json as _json
    feed = _get_google_feed_or_404(db, feed_id, current_user.id)
    if data.calendar_name is not None:
        feed.calendar_name = data.calendar_name
    if data.calendar_color is not None:
        feed.calendar_color = normalize_stored_color(data.calendar_color)
    if data.color_filters is not None:
        feed.color_filters = _json.dumps(data.color_filters) if data.color_filters else None
        feed.sync_token = None  # reset sync so color filter applies from scratch
    if data.enabled is not None:
        feed.enabled = data.enabled
    color_filters_changed = data.color_filters is not None
    db.commit()
    if color_filters_changed:
        try:
            _run_google_feed_sync(db, feed, full_sync=True)
        except Exception as exc:
            feed.last_error = str(exc)
            db.commit()
    return _google_feed_to_dict(feed)


@router.delete("/me/google/feeds/{feed_id}")
def me_google_delete_feed(
    feed_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feed = _get_google_feed_or_404(db, feed_id, current_user.id)
    db.delete(feed)
    db.commit()
    return {"ok": True}


@router.post("/me/google/feeds/{feed_id}/sync")
def me_google_sync_feed(
    feed_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models import GoogleApiConfig
    from app.services.google_sync_service import _sync_feed
    feed = _get_google_feed_or_404(db, feed_id, current_user.id)
    config = db.query(GoogleApiConfig).first()
    if not config or not config.client_id:
        raise HTTPException(400, "Google Calendar API niet geconfigureerd")
    try:
        _sync_feed(db, feed, config, full_sync=True)
    except Exception as exc:
        raise HTTPException(500, f"Synchronisatie mislukt: {exc}") from exc
    return _google_feed_to_dict(db.query(feed.__class__).get(feed.id))


# ---------------------------------------------------------------------------
# Google Calendar – /api/admin/users/{user_id}/google/…
# ---------------------------------------------------------------------------

@router.get("/admin/users/{user_id}/google/status")
def admin_user_google_status(user_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    from app.models import PersonGoogleAuth
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == user_id).first()
    return {
        "linked": bool(auth and auth.refresh_token),
        "google_email": auth.google_email if auth else None,
    }


@router.get("/admin/users/{user_id}/google/auth-url")
def admin_user_google_auth_url(
    user_id: int,
    request: Request,
    return_to: str = "",
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return_to = return_to or f"/admin/user/{user_id}"
    url = _google_auth_url_for_person(user_id, return_to, request, db)
    return {"auth_url": url}


@router.delete("/admin/users/{user_id}/google/auth")
def admin_user_google_unlink(user_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    from app.models import PersonGoogleAuth
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == user_id).first()
    if auth:
        db.delete(auth)
        db.commit()
    return {"ok": True}


@router.get("/admin/users/{user_id}/google/calendars")
def admin_user_google_list_calendars(user_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    from app.models import PersonGoogleAuth
    from app.services.google_calendar_service import list_calendars
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == user_id).first()
    if not auth or not auth.refresh_token:
        raise HTTPException(400, "Google account niet gekoppeld")
    cfg = _get_google_config(db)
    access_token = _ensure_gcal_token(db, auth, cfg)
    try:
        cals = list_calendars(access_token)
    except Exception as exc:
        raise HTTPException(400, f"Ophalen agenda's mislukt: {exc}") from exc
    return [{"id": c["id"], "summary": c.get("summary", ""), "backgroundColor": c.get("backgroundColor", "")} for c in cals]


@router.get("/admin/users/{user_id}/google/feeds")
def admin_user_google_feeds(user_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    return _google_feeds_for_person(db, user_id)


@router.post("/admin/users/{user_id}/google/feeds")
def admin_user_google_add_feed(
    user_id: int,
    data: GoogleFeedCreate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    import json as _json
    from app.models import PersonGoogleAuth, PersonGoogleCalendarFeed
    auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == user_id).first()
    if not auth or not auth.refresh_token:
        raise HTTPException(400, "Google account niet gekoppeld")
    feed = PersonGoogleCalendarFeed(
        person_id=user_id,
        auth_id=auth.id,
        google_calendar_id=data.google_calendar_id,
        calendar_name=data.calendar_name,
        color_filters=_json.dumps(data.color_filters) if data.color_filters else None,
        enabled=data.enabled,
    )
    db.add(feed)
    db.commit()
    return _google_feed_to_dict(feed)


@router.put("/admin/users/{user_id}/google/feeds/{feed_id}")
def admin_user_google_update_feed(
    user_id: int,
    feed_id: int,
    data: GoogleFeedUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    import json as _json
    feed = _get_google_feed_or_404(db, feed_id, user_id)
    if data.calendar_name is not None:
        feed.calendar_name = data.calendar_name
    if data.calendar_color is not None:
        feed.calendar_color = normalize_stored_color(data.calendar_color)
    if data.color_filters is not None:
        feed.color_filters = _json.dumps(data.color_filters) if data.color_filters else None
        feed.sync_token = None
    if data.enabled is not None:
        feed.enabled = data.enabled
    color_filters_changed = data.color_filters is not None
    db.commit()
    if color_filters_changed:
        try:
            _run_google_feed_sync(db, feed, full_sync=True)
        except Exception as exc:
            feed.last_error = str(exc)
            db.commit()
    return _google_feed_to_dict(feed)


@router.delete("/admin/users/{user_id}/google/feeds/{feed_id}")
def admin_user_google_delete_feed(
    user_id: int,
    feed_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    feed = _get_google_feed_or_404(db, feed_id, user_id)
    db.delete(feed)
    db.commit()
    return {"ok": True}


@router.post("/admin/users/{user_id}/google/feeds/{feed_id}/sync")
def admin_user_google_sync_feed(
    user_id: int,
    feed_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.models import GoogleApiConfig
    from app.services.google_sync_service import _sync_feed
    feed = _get_google_feed_or_404(db, feed_id, user_id)
    config = db.query(GoogleApiConfig).first()
    if not config or not config.client_id:
        raise HTTPException(400, "Google Calendar API niet geconfigureerd")
    try:
        _sync_feed(db, feed, config, full_sync=True)
    except Exception as exc:
        raise HTTPException(500, f"Synchronisatie mislukt: {exc}") from exc
    return _google_feed_to_dict(db.query(feed.__class__).get(feed.id))


# ---------------------------------------------------------------------------
# Dashboard app upgrades
# ---------------------------------------------------------------------------

@router.get("/admin/dashboard-upgrade")
def admin_dashboard_upgrade_info(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    from app.services.dashboard_upgrade_service import DashboardUpgradeService

    return DashboardUpgradeService(db).get_info()


@router.post("/admin/dashboard-upgrade")
async def admin_dashboard_upgrade_upload(
    file: UploadFile = File(...),
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.services.dashboard_upgrade_service import DashboardUpgradeService

    content = await file.read()
    try:
        record = DashboardUpgradeService(db).upload_apk(content, file.filename or "")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "version": record.version,
        "uploaded_at": record.uploaded_at.isoformat() if record.uploaded_at else None,
    }


@router.get("/app/dashboard-upgrade")
def app_dashboard_upgrade_info(_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.dashboard_upgrade_service import DashboardUpgradeService

    return DashboardUpgradeService(db).get_info()


@router.get("/app/dashboard-upgrade/download")
def app_dashboard_upgrade_download(_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.dashboard_upgrade_service import DashboardUpgradeService

    path = DashboardUpgradeService(db).get_apk_path()
    if not path:
        raise HTTPException(404, "Geen update beschikbaar")
    return FileResponse(
        path,
        media_type="application/vnd.android.package-archive",
        filename="buddyplan-dashboard.apk",
    )


# ---------------------------------------------------------------------------
# Shared helper – ensure access token is valid
# ---------------------------------------------------------------------------

def _ensure_gcal_token(db: Session, auth, config) -> str:
    from datetime import timezone as _tz
    from app.services.google_calendar_service import refresh_access_token
    now = datetime.now(_tz.utc)
    expiry = auth.token_expiry
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=_tz.utc)
    needs_refresh = not auth.access_token or not expiry or expiry <= now + timedelta(minutes=5)
    if needs_refresh:
        token_data = refresh_access_token(config.client_id, config.client_secret, auth.refresh_token)
        auth.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            auth.refresh_token = token_data["refresh_token"]
        auth.token_expiry = now + timedelta(seconds=int(token_data.get("expires_in", 3600)))
        db.commit()
    return auth.access_token
