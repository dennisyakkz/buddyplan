"""AI buddy: a Gemini-backed assistant that reads and changes agenda items and tasks (REQ-BE-080..089).

Tool calls go through the REST API route functions themselves, so the AI buddy has exactly the
rights of the calling user and refusals carry the API's Dutch error messages (REQ-BE-084).
"""

import logging
import time
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AiConfig, AiMessage, AiPendingDeletion, Person
from app.services import ai_monitoring
from app.services.dashboard_service import PersonService

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
REQUEST_TIMEOUT_SECONDS = 60  # REQ-BE-083
MAX_TOOL_CALLS = 10  # REQ-BE-088
CONTEXT_MESSAGES_DEFAULT = 20  # REQ-BE-087
CONTEXT_MESSAGES_MIN = 2
CONTEXT_MESSAGES_MAX = 100
MAX_MESSAGE_LENGTH = 4000
# thinkingLevel is only valid on Gemini 3/4 models; older models error on it (REQ-BE-098).
# "minimal" is left out: some current Gemini 3/4 models reject it.
THINKING_LEVELS = ("low", "medium", "high", "xhigh")
THINKING_CAPABLE_MODEL_PREFIXES = ("gemini-3", "gemini-4")
SEARCH_MAX_DAYS = 180  # REQ-BE-085, like /api/mobile/calendar
# What a search returns depends on the length of its range, first and last day included (REQ-BE-085).
SEARCH_ALL_DAYS = 14  # up to here: everything, keywords ignored
SEARCH_FALLBACK_DAYS = 31  # up to here: keywords, falling back to everything when nothing matches
TZ = ZoneInfo("Europe/Amsterdam")

NOT_CONFIGURED_MESSAGE = "De AI buddy is nog niet ingesteld door de beheerder."
UNAVAILABLE_MESSAGE = "De AI buddy is nu niet bereikbaar. Probeer het later opnieuw."
EMPTY_REPLY = "Sorry, daar heb ik geen antwoord op."

DEFAULT_SYSTEM_PROMPT = """Je bent de AI buddy van Buddyplan, de gezinsplanner van dit huishouden.
Je helpt de gebruiker met de agenda en de takenlijsten van de mensen in de planner.

- Antwoord altijd in het Nederlands, kort en vriendelijk, zoals in een chatapp.
- Gebruik de tools om agenda-items en taken op te zoeken, te lezen, aan te maken, te wijzigen en te verwijderen. Verzin nooit gegevens of id's: zoek ze eerst op.
- Gebruik de datum en tijd uit de context om woorden als 'morgen' of 'volgende week dinsdag' om te zetten naar een datum (JJJJ-MM-DD) en tijden naar UU:MM.
- Noem je in je antwoord de dag van de week bij een datum, gebruik dan het weekday-veld dat search_agenda en search_tasks meegeven. Reken dit nooit zelf uit: dat gaat te vaak mis.
- Is niet duidelijk voor wie iets is, voor wanneer, of welk item de gebruiker bedoelt, vraag het dan eerst.
- Verwijderen gaat in twee stappen: roep de verwijder-tool eerst aan zonder bevestiging, vertel de gebruiker wat er verwijderd wordt en vraag of dat klopt. Pas na een duidelijk 'ja' in het volgende bericht roep je de tool aan met bevestiging.
- Weigert een tool iets, bijvoorbeeld omdat de gebruiker geen rechten heeft of omdat een item uit een gekoppelde agenda komt, leg dat dan in gewone woorden uit.
- Vertel na een wijziging kort wat je hebt gedaan."""

WEEKDAYS_NL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTHS_NL = [
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
]


class AiNotConfigured(Exception):
    pass


class AiUnavailable(Exception):
    pass


# --- settings ------------------------------------------------------------------------------------


def get_config(db: Session) -> AiConfig | None:
    return db.query(AiConfig).first()


def _usable(cfg: AiConfig | None) -> bool:
    """Switched on, with a key and a model (REQ-BE-083)."""
    return bool(cfg and cfg.enabled and cfg.api_key and cfg.model)


def is_configured(db: Session) -> bool:
    return _usable(get_config(db))


def effective_system_prompt(cfg: AiConfig | None) -> str:
    prompt = (cfg.system_prompt or "").strip() if cfg else ""
    return prompt or DEFAULT_SYSTEM_PROMPT


def api_key_hint(api_key: str | None) -> str:
    """Only the last four characters are ever shown again (REQ-BE-081)."""
    return f"…{api_key[-4:]}" if api_key else ""


def config_to_dict(cfg: AiConfig | None) -> dict:
    return {
        "has_api_key": bool(cfg and cfg.api_key),
        "api_key_hint": api_key_hint(cfg.api_key if cfg else None),
        "model": (cfg.model if cfg else None) or "",
        "thinking_level": (cfg.thinking_level if cfg else None) or "",
        "thinking_levels": list(THINKING_LEVELS),
        "system_prompt": effective_system_prompt(cfg),
        "is_default_prompt": not (cfg and (cfg.system_prompt or "").strip()),
        "default_system_prompt": DEFAULT_SYSTEM_PROMPT,
        "enabled": bool(cfg and cfg.enabled),
        "context_messages": (cfg.context_messages if cfg else None) or CONTEXT_MESSAGES_DEFAULT,
        "configured": _usable(cfg),
        "debug_log_enabled": bool(cfg and cfg.debug_log_enabled),
        "debug_retention_days": (cfg.debug_retention_days if cfg else None) or 7,
    }


def update_config(
    db: Session,
    *,
    api_key: str | None,
    clear_api_key: bool,
    model: str | None,
    thinking_level: str | None,
    system_prompt: str | None,
    debug_log_enabled: bool | None = None,
    debug_retention_days: int | None = None,
    enabled: bool | None = None,
    context_messages: int | None = None,
) -> AiConfig:
    if context_messages is not None and not (CONTEXT_MESSAGES_MIN <= context_messages <= CONTEXT_MESSAGES_MAX):
        raise ValueError(
            f"Aantal berichten als context moet tussen {CONTEXT_MESSAGES_MIN} en {CONTEXT_MESSAGES_MAX} liggen"
        )
    if debug_retention_days is not None and not (
        ai_monitoring.RETENTION_MIN_DAYS <= debug_retention_days <= ai_monitoring.RETENTION_MAX_DAYS
    ):
        raise ValueError(
            f"Bewaartermijn moet tussen {ai_monitoring.RETENTION_MIN_DAYS} en "
            f"{ai_monitoring.RETENTION_MAX_DAYS} dagen liggen"
        )
    if thinking_level is not None and thinking_level.strip() and thinking_level.strip().lower() not in THINKING_LEVELS:
        raise ValueError(f"Thinking moet leeg zijn of één van: {', '.join(THINKING_LEVELS)}")
    cfg = get_config(db)
    if not cfg:
        cfg = AiConfig()
        db.add(cfg)
    if enabled is not None:
        cfg.enabled = enabled
    if context_messages is not None:
        cfg.context_messages = context_messages
    if debug_log_enabled is not None:
        cfg.debug_log_enabled = debug_log_enabled
    if debug_retention_days is not None:
        cfg.debug_retention_days = debug_retention_days
    if clear_api_key:
        cfg.api_key = None
    elif api_key and api_key.strip():
        # An empty field keeps the stored key: the page never receives it back.
        cfg.api_key = api_key.strip()[:255]
    if model is not None:
        cfg.model = model.strip()[:100] or None
    if thinking_level is not None:
        cfg.thinking_level = thinking_level.strip().lower()[:20] or None
    if system_prompt is not None:
        prompt = system_prompt.strip()
        cfg.system_prompt = None if not prompt or prompt == DEFAULT_SYSTEM_PROMPT.strip() else prompt
    cfg.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(cfg)
    return cfg


# --- Gemini REST API -----------------------------------------------------------------------------


def list_models(api_key: str) -> list[dict]:
    """Models available to the key that can generate content (REQ-BE-081)."""
    try:
        response = requests.get(
            f"{GEMINI_BASE_URL}/models",
            params={"pageSize": 1000},
            headers={"x-goog-api-key": api_key},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AiUnavailable(str(exc)) from exc
    if response.status_code != 200:
        raise AiUnavailable(_error_text(response))
    models = []
    for model in response.json().get("models", []):
        if "generateContent" not in model.get("supportedGenerationMethods", []):
            continue
        name = model.get("name", "").removeprefix("models/")
        models.append({"name": name, "display_name": model.get("displayName") or name})
    return sorted(models, key=lambda m: m["name"])


RETRY_DELAYS_SECONDS = (1, 2)  # REQ-BE-083: three attempts in total


class _RetryableFailure(AiUnavailable):
    """A connection error, timeout or HTTP 5xx: worth another attempt."""


def _sleep(seconds: float) -> None:  # replaced in tests
    time.sleep(seconds)


def generate(
    cfg: AiConfig,
    system: list[str],
    contents: list[dict],
    *,
    allow_tools: bool,
    log: ai_monitoring.CallContext | None = None,
) -> dict:
    """One generateContent request with retries; returns the first candidate's content."""
    body: dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": part} for part in system]},
        "contents": contents,
        "tools": [{"functionDeclarations": TOOL_DECLARATIONS}],
        # After the tool budget is spent the model must answer in text (REQ-BE-088).
        "toolConfig": {"functionCallingConfig": {"mode": "AUTO" if allow_tools else "NONE"}},
    }
    # thinkingLevel errors on models older than Gemini 3, so only Gemini 3/4 models get it (REQ-BE-098).
    if cfg.thinking_level and cfg.model.startswith(THINKING_CAPABLE_MODEL_PREFIXES):
        body["generationConfig"] = {"thinkingConfig": {"thinkingLevel": cfg.thinking_level.upper()}}
    for delay in (*RETRY_DELAYS_SECONDS, None):
        try:
            return _generate_once(cfg, body, log)
        except _RetryableFailure as exc:
            if delay is None:
                raise AiUnavailable(str(exc)) from exc
            logger.warning("Gemini call failed (%s); retrying in %ss", exc, delay)
            _sleep(delay)
    raise AssertionError("unreachable")


def _generate_once(cfg: AiConfig, body: dict, log: ai_monitoring.CallContext | None) -> dict:
    """One attempt; every attempt is recorded (REQ-BE-091)."""
    started = time.monotonic()

    def record(**fields) -> None:
        elapsed = int((time.monotonic() - started) * 1000)
        ai_monitoring.record_call(log, cfg, request_body=body, duration_ms=elapsed, **fields)

    try:
        response = requests.post(
            f"{GEMINI_BASE_URL}/models/{cfg.model}:generateContent",
            json=body,
            headers={"x-goog-api-key": cfg.api_key or ""},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        record(status="error", error_message=str(exc))
        raise _RetryableFailure(str(exc)) from exc
    if response.status_code != 200:
        error = _error_text(response)
        record(status="error", http_status=response.status_code, error_message=error, response_text=response.text)
        if response.status_code >= 500:
            raise _RetryableFailure(error)
        raise AiUnavailable(error)
    try:
        data = response.json()
    except ValueError as exc:
        record(
            status="error", http_status=200, error_message="Ongeldig antwoord (geen JSON)", response_text=response.text
        )
        raise AiUnavailable("Ongeldig antwoord van Gemini") from exc
    candidates = data.get("candidates") or []
    content = (candidates[0].get("content") if candidates else None) or {}
    content.setdefault("role", "model")
    content.setdefault("parts", [])
    answered = any(
        "functionCall" in part or (part.get("text") and not part.get("thought")) for part in content["parts"]
    )
    record(
        status="ok" if answered else "empty",
        http_status=200,
        usage=data.get("usageMetadata"),
        response_text=response.text,
    )
    return content


def _error_text(response) -> str:
    try:
        return f"{response.status_code}: {response.json().get('error', {}).get('message', '')}"
    except ValueError:
        return f"{response.status_code}: {response.text[:200]}"


# --- context (REQ-BE-082) -----------------------------------------------------------------------


def context_text(db: Session, user, now: datetime | None = None) -> str:
    """Facts the model always gets, independent of the editable system prompt."""
    now = (now or datetime.now(UTC)).astimezone(TZ)
    service = PersonService(db)
    lines = [
        "Context (automatisch toegevoegd door Buddyplan):",
        f"- Nu is het {WEEKDAYS_NL[now.weekday()]} {now.day} {MONTHS_NL[now.month - 1]} {now.year}, "
        f"{now:%H:%M} (Europe/Amsterdam). Vandaag is {now.date().isoformat()}.",
        f"- {_week_line(now.date())}",
        f"- Je praat met {user.name} (person_id {user.id}).",
        "- Mensen in de planner (person_id: naam; mag de gebruiker hun agenda / taken beheren):",
    ]
    for person in db.query(Person).order_by(Person.sort_order, Person.id).all():
        agenda = "ja" if service.can_manage_agenda(person.id, user.id) else "nee"
        tasks = "ja" if service.can_manage_tasks(person.id, user.id) else "nee"
        lines.append(f"  - {person.id}: {person.name} (agenda: {agenda}, taken: {tasks})")
    return "\n".join(lines)


def _week_line(today: date) -> str:
    """This week and next week, Monday to Sunday, like the agenda (REQ-BE-082)."""
    monday = today - timedelta(days=today.weekday())
    next_monday = monday + timedelta(days=7)

    def span(start: date) -> str:
        end = start + timedelta(days=6)
        return f"maandag {_day_month(start)} t/m zondag {_day_month(end)} ({start.isoformat()} t/m {end.isoformat()})"

    return f"Deze week loopt van {span(monday)}; volgende week van {span(next_monday)}."


def _day_month(day: date) -> str:
    return f"{day.day} {MONTHS_NL[day.month - 1]}"


# --- tools (REQ-BE-084, REQ-BE-085, REQ-BE-086) ----------------------------------------------------

_DATE = {"type": "string", "description": "Datum als JJJJ-MM-DD."}
_TIME = {"type": "string", "description": "Tijd als UU:MM (24 uur)."}
_REPEAT = {
    "type": "string",
    "enum": ["once", "daily", "weekly", "biweekly", "weekdays"],
    "description": "Herhaling: once (eenmalig), daily, weekly / biweekly (op de weekdag van date), "
    "weekdays (op de dagen in repeat_weekdays).",
}
_WEEKDAYS = {
    "type": "array",
    "items": {"type": "integer"},
    "description": "Weekdagen voor repeat_type 'weekdays': 0 = maandag … 6 = zondag.",
}
_SEARCH_PARAMS = {
    "type": "object",
    "properties": {
        "start_date": _DATE,
        "end_date": {"type": "string", "description": "Laatste datum (JJJJ-MM-DD), max 180 dagen na start_date."},
        "person_id": {"type": "integer", "description": "Alleen voor deze persoon (optioneel)."},
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Zoekwoorden; een item past als de titel minstens één ervan bevat (hoofdletters en "
            "spaties tellen niet). Geef meerdere vormen en synoniemen mee, bijv. ['training', 'trainen', "
            "'voetbal']. Bij periodes tot 14 dagen genegeerd, verplicht bij periodes langer dan 31 dagen.",
        },
    },
    "required": ["start_date", "end_date"],
}
_DELETE_PARAMS = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "confirmed": {
            "type": "boolean",
            "description": "Alleen true nadat de gebruiker deze verwijdering in een nieuw bericht bevestigd heeft.",
        },
    },
    "required": ["id"],
}

_SEARCH_RULES = (
    f"Tot en met {SEARCH_ALL_DAYS} dagen (eerste en laatste dag meegeteld) krijg je alle items in de periode en "
    "beoordeel je zelf wat bij de vraag past; zoekwoorden worden dan genegeerd. "
    f"Van {SEARCH_ALL_DAYS + 1} tot en met {SEARCH_FALLBACK_DAYS} dagen krijg je de items die bij een zoekwoord "
    "passen; past er niets, of geef je geen zoekwoorden, dan krijg je alle items met een notitie. "
    f"Langer dan {SEARCH_FALLBACK_DAYS} dagen (max {SEARCH_MAX_DAYS}) alleen met zoekwoorden, en alleen de items "
    "die erbij passen: kies dan ruime zoekwoorden met varianten."
)

TOOL_DECLARATIONS: list[dict] = [
    {
        "name": "search_agenda",
        "description": "Zoek agenda-items in een periode. Geeft per item id, persoon, titel, datum, weekdag en "
        "tijden. " + _SEARCH_RULES,
        "parameters": _SEARCH_PARAMS,
    },
    {
        "name": "get_agenda_item",
        "description": "Lees één agenda-item met alle velden, inclusief herhaling.",
        "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
    },
    {
        "name": "create_agenda_item",
        "description": "Maak een agenda-item aan voor een persoon.",
        "parameters": {
            "type": "object",
            "properties": {
                "person_id": {"type": "integer"},
                "title": {"type": "string"},
                "date": _DATE,
                "start_time": _TIME,
                "end_time": _TIME,
                "repeat_type": _REPEAT,
                "repeat_weekdays": _WEEKDAYS,
                "end_date": {"type": "string", "description": "Laatste datum van de herhaling (optioneel)."},
            },
            "required": ["person_id", "title", "date"],
        },
    },
    {
        "name": "update_agenda_item",
        "description": "Wijzig een agenda-item. Geef alleen de velden mee die veranderen; "
        "een lege tekst voor start_time of end_time haalt die tijd weg.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "date": _DATE,
                "start_time": _TIME,
                "end_time": _TIME,
                "repeat_type": _REPEAT,
                "repeat_weekdays": _WEEKDAYS,
                "end_date": {"type": "string"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "delete_agenda_item",
        "description": "Verwijder een agenda-item. Eerst zonder confirmed aanroepen en de gebruiker om "
        "bevestiging vragen; pas na een 'ja' in een volgend bericht aanroepen met confirmed=true.",
        "parameters": _DELETE_PARAMS,
    },
    {
        "name": "search_tasks",
        "description": "Zoek taken in een periode. Geeft per taak id, persoon, titel, datum, weekdag en of de taak "
        "af is. " + _SEARCH_RULES,
        "parameters": _SEARCH_PARAMS,
    },
    {
        "name": "get_task",
        "description": "Lees één taak met alle velden, inclusief herhaling.",
        "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
    },
    {
        "name": "create_task",
        "description": "Maak een taak aan voor een persoon.",
        "parameters": {
            "type": "object",
            "properties": {
                "person_id": {"type": "integer"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "date": _DATE,
                "repeat_type": _REPEAT,
                "repeat_weekdays": _WEEKDAYS,
                "end_date": {"type": "string", "description": "Laatste datum van de herhaling (optioneel)."},
            },
            "required": ["person_id", "title", "date"],
        },
    },
    {
        "name": "update_task",
        "description": "Wijzig een taak. Geef alleen de velden mee die veranderen.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "date": _DATE,
                "repeat_type": _REPEAT,
                "repeat_weekdays": _WEEKDAYS,
                "end_date": {"type": "string"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "delete_task",
        "description": "Verwijder een taak. Eerst zonder confirmed aanroepen en de gebruiker om "
        "bevestiging vragen; pas na een 'ja' in een volgend bericht aanroepen met confirmed=true.",
        "parameters": _DELETE_PARAMS,
    },
]


class ToolRunner:
    """Runs the model's tool calls for one user message, as that user."""

    def __init__(self, db: Session, user, user_message_id: int):
        self.db = db
        self.user = user
        self.user_message_id = user_message_id

    def run(self, name: str, args: dict) -> dict:
        handler = getattr(self, f"_tool_{name}", None)
        if handler is None:
            return {"error": f"Onbekende tool: {name}"}
        try:
            return handler(**args)
        except HTTPException as exc:
            self.db.rollback()
            return {"error": exc.detail}
        except (TypeError, ValueError) as exc:
            self.db.rollback()
            return {"error": f"Ongeldige invoer: {exc}"}

    # agenda ------------------------------------------------------------------------------------

    def _tool_search_agenda(self, start_date, end_date, person_id=None, keywords=None, text=None):
        from app.routers.api import mobile_calendar

        start, end = _search_range(start_date, end_date, _keywords(keywords, text))
        items = mobile_calendar(start=start, end=end, current_user=self.user, db=self.db)
        return _search_result("items", items, start, end, person_id, _keywords(keywords, text))

    def _tool_get_agenda_item(self, id):
        from app.routers.api import mobile_calendar_item

        return mobile_calendar_item(item_id=int(id), current_user=self.user, db=self.db)

    def _tool_create_agenda_item(self, person_id, title, date, **fields):
        from app.routers.api import AgendaCreate, create_agenda_item

        data = AgendaCreate(person_id=int(person_id), title=title, anchor_date=date, **_known_fields(fields))
        return {"created": create_agenda_item(data=data, user=self.user, db=self.db)}

    def _tool_update_agenda_item(self, id, **fields):
        from app.routers.api import AgendaUpdate, update_agenda_item

        if "date" in fields:
            fields["anchor_date"] = fields.pop("date")
        data = AgendaUpdate(**_known_fields(fields, keep_empty_times=True))
        return {"updated": update_agenda_item(item_id=int(id), data=data, user=self.user, db=self.db)}

    def _tool_delete_agenda_item(self, id, confirmed=False):
        from app.routers.api import delete_agenda_item, mobile_calendar_item

        item = mobile_calendar_item(item_id=int(id), current_user=self.user, db=self.db)
        if not PersonService(self.db).can_manage_agenda(item["person_id"], self.user.id):
            raise HTTPException(403, "Geen rechten om agenda te beheren voor deze gebruiker")
        if item["is_read_only"]:
            raise HTTPException(403, "Agenda-items uit een feed kunnen niet worden verwijderd")
        return self._delete("agenda", int(id), item, confirmed, delete_agenda_item)

    # tasks -------------------------------------------------------------------------------------

    def _tool_search_tasks(self, start_date, end_date, person_id=None, keywords=None, text=None):
        from app.routers.api import mobile_tasks

        start, end = _search_range(start_date, end_date, _keywords(keywords, text))
        items = mobile_tasks(start=start, end=end, person_id=None, current_user=self.user, db=self.db)
        for item in items:
            item.pop("profile_color", None)
            item.pop("icon", None)
        return _search_result("tasks", items, start, end, person_id, _keywords(keywords, text))

    def _tool_get_task(self, id):
        from app.routers.api import get_task

        return get_task(task_id=int(id), _user=self.user, db=self.db)

    def _tool_create_task(self, person_id, title, date, description="", **fields):
        from app.routers.api import TaskCreate, create_task

        data = TaskCreate(title=title, description=description or "", anchor_date=date, **_known_fields(fields))
        return {"created": create_task(data=data, person_id=int(person_id), user=self.user, db=self.db)}

    def _tool_update_task(self, id, **fields):
        from app.routers.api import TaskUpdate, get_task, update_task

        current = get_task(task_id=int(id), _user=self.user, db=self.db)
        if "date" in fields:
            fields["anchor_date"] = fields.pop("date")
        merged = {
            key: current.get(key)
            for key in ("title", "description", "icon", "repeat_type", "repeat_weekdays", "anchor_date", "end_date")
        }
        merged["sort_order"] = current.get("sort_order") or 0
        merged.update(_known_fields(fields))
        merged = {k: v for k, v in merged.items() if v is not None or k == "end_date"}
        data = TaskUpdate(**merged)
        return {"updated": update_task(task_id=int(id), data=data, user=self.user, db=self.db)}

    def _tool_delete_task(self, id, confirmed=False):
        from app.routers.api import delete_task, get_task

        task = get_task(task_id=int(id), _user=self.user, db=self.db)
        owner = task.get("person_id")
        if owner is None or not PersonService(self.db).can_manage_tasks(owner, self.user.id):
            raise HTTPException(403, "Geen rechten om taken te beheren voor deze gebruiker")
        return self._delete("task", int(id), task, confirmed, delete_task)

    # deletion with confirmation (REQ-BE-086) ---------------------------------------------------

    def _delete(self, kind: str, item_id: int, item: dict, confirmed: bool, delete_route) -> dict:
        pending = (
            self.db.query(AiPendingDeletion)
            .filter(
                AiPendingDeletion.person_id == self.user.id,
                AiPendingDeletion.kind == kind,
                AiPendingDeletion.item_id == item_id,
            )
            .first()
        )
        if confirmed and pending and pending.proposed_in_message_id < self.user_message_id:
            if kind == "agenda":
                delete_route(item_id=item_id, user=self.user, db=self.db)
            else:
                delete_route(task_id=item_id, user=self.user, db=self.db)
            self.db.query(AiPendingDeletion).filter(AiPendingDeletion.id == pending.id).delete()
            self.db.commit()
            return {"deleted": item}

        if pending is None:
            self.db.add(
                AiPendingDeletion(
                    person_id=self.user.id,
                    kind=kind,
                    item_id=item_id,
                    proposed_in_message_id=self.user_message_id,
                )
            )
        else:
            pending.proposed_in_message_id = self.user_message_id
        self.db.commit()
        return {
            "deleted": False,
            "needs_confirmation": True,
            "item": item,
            "instruction": "Nog niet verwijderd. Vertel de gebruiker wat er verwijderd wordt en vraag om "
            "bevestiging. Roep deze tool pas na een 'ja' in het volgende bericht aan met confirmed=true.",
        }


def _search_range(start_date: str, end_date: str, keywords: list[str]) -> tuple[date, date]:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date ligt voor start_date")
    if (end - start).days > SEARCH_MAX_DAYS:
        raise HTTPException(400, "Datumbereik te groot (max 180 dagen)")
    if _span_days(start, end) > SEARCH_FALLBACK_DAYS and not keywords:
        raise HTTPException(
            400,
            f"Geef zoekwoorden op, of zoek in een periode van maximaal {SEARCH_FALLBACK_DAYS} dagen",
        )
    return start, end


def _span_days(start: date, end: date) -> int:
    return (end - start).days + 1


def _keywords(keywords, text=None) -> list[str]:
    """The keywords as a list of normalised words; a single string (or the old 'text') counts as one keyword."""
    if isinstance(keywords, str):
        keywords = [keywords]
    words = [*(keywords or []), *([text] if text else [])]
    return [n for n in (_normalize_for_search(w) for w in words) if n]


def _normalize_for_search(value: str) -> str:
    """Casefolded with whitespace removed, so 'voetbaltraining' matches 'Voetbal training'."""
    return "".join(str(value).casefold().split())


def _search_result(key: str, items: list[dict], start: date, end: date, person_id, keywords: list[str]) -> dict:
    """Applies the range rules of REQ-BE-085 to the items of the range."""
    if person_id is not None:
        items = [i for i in items if i.get("person_id") == int(person_id)]
    span = _span_days(start, end)
    if span <= SEARCH_ALL_DAYS:
        return {key: _with_weekdays(items)}
    matching = [i for i in items if any(k in _normalize_for_search(i.get("title", "")) for k in keywords)]
    if matching or span > SEARCH_FALLBACK_DAYS:
        return {key: _with_weekdays(matching)}
    note = (
        "Geen zoekwoorden opgegeven: dit zijn alle items in de periode."
        if not keywords
        else "Geen titel bevat een van de zoekwoorden: dit zijn alle items in de periode. "
        "Beoordeel zelf welke bij de vraag passen."
    )
    return {key: _with_weekdays(items), "note": note}


def _with_weekdays(items: list[dict]) -> list[dict]:
    """Adds the Dutch weekday name next to each item's date: small models get this wrong
    when they have to compute it themselves from today's date."""
    for item in items:
        if item.get("date"):
            item["weekday"] = WEEKDAYS_NL[date.fromisoformat(item["date"]).weekday()]
    return items


def _known_fields(fields: dict, *, keep_empty_times: bool = False) -> dict:
    """Only the fields the API models know; empty times clear a time when updating."""
    allowed = (
        "title",
        "description",
        "anchor_date",
        "start_time",
        "end_time",
        "repeat_type",
        "repeat_weekdays",
        "end_date",
    )
    result = {}
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key in ("start_time", "end_time") and value == "" and not keep_empty_times:
            continue
        if key == "end_date" and value == "":
            value = None
        result[key] = value
    return result


# --- conversation (REQ-BE-080, REQ-BE-087) ------------------------------------------------------


def message_to_dict(message: AiMessage) -> dict:
    created = message.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return {
        "id": message.id,
        "role": message.role,
        "text": message.text,
        "created_at": created.isoformat() if created else None,
    }


def conversation(db: Session, person_id: int) -> list[AiMessage]:
    return db.query(AiMessage).filter(AiMessage.person_id == person_id).order_by(AiMessage.id).all()


def clear_conversation(db: Session, person_id: int) -> None:
    # The debug content holds the same conversation, so it goes too (REQ-BE-093).
    ai_monitoring.clear_person_content(db, person_id)
    db.query(AiMessage).filter(AiMessage.person_id == person_id).delete()
    db.query(AiPendingDeletion).filter(AiPendingDeletion.person_id == person_id).delete()
    db.commit()


def _store_user_message(db: Session, person_id: int, text: str) -> AiMessage:
    """Store the message; a retry of the last, unanswered message reuses it (REQ-BE-083)."""
    last = db.query(AiMessage).filter(AiMessage.person_id == person_id).order_by(AiMessage.id.desc()).first()
    if last and last.role == "user" and last.text == text:
        return last
    message = AiMessage(person_id=person_id, role="user", text=text)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def send_message(db: Session, user, text: str, now: datetime | None = None) -> tuple[AiMessage, AiMessage]:
    """Answer one user message, calling tools as needed. Returns (user message, reply)."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Bericht is leeg")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Bericht is te lang (max {MAX_MESSAGE_LENGTH} tekens)")
    cfg = get_config(db)
    if not _usable(cfg):
        raise AiNotConfigured(NOT_CONFIGURED_MESSAGE)

    user_message = _store_user_message(db, user.id, text)
    history = (
        db.query(AiMessage)
        .filter(AiMessage.person_id == user.id, AiMessage.id <= user_message.id)
        .order_by(AiMessage.id.desc())
        .limit(cfg.context_messages or CONTEXT_MESSAGES_DEFAULT)
        .all()
    )
    contents = [
        {"role": "user" if m.role == "user" else "model", "parts": [{"text": m.text}]} for m in reversed(history)
    ]
    system = [effective_system_prompt(cfg), context_text(db, user, now)]
    runner = ToolRunner(db, user, user_message.id)
    log = ai_monitoring.CallContext(person_id=user.id, message_id=user_message.id, activity="chat")

    tool_calls = 0
    while True:
        content = generate(cfg, system, contents, allow_tools=tool_calls < MAX_TOOL_CALLS, log=log)
        calls = [part["functionCall"] for part in content["parts"] if "functionCall" in part]
        if not calls or tool_calls >= MAX_TOOL_CALLS:
            reply_text = "".join(part.get("text", "") for part in content["parts"] if not part.get("thought")).strip()
            break
        # The model's content goes back unchanged: newer models need their thought signatures.
        contents.append(content)
        responses = []
        for call in calls:
            tool_calls += 1
            if tool_calls > MAX_TOOL_CALLS:
                result = {"error": "Maximum aantal tool-aanroepen bereikt; geef nu je antwoord."}
            else:
                result = runner.run(call.get("name", ""), call.get("args") or {})
            responses.append({"functionResponse": {"name": call.get("name", ""), "response": _jsonable(result)}})
        contents.append({"role": "user", "parts": responses})

    reply = AiMessage(person_id=user.id, role="assistant", text=reply_text or EMPTY_REPLY)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return user_message, reply


def _jsonable(value):
    """Tool results go to Gemini as JSON objects."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)
