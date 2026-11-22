"""AI monitoring (REQ-BE-090..097): Gemini call records, debug content, model prices and costs."""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import AiCall, AiConfig, AiModelPrice, Person

logger = logging.getLogger(__name__)

TZ = ZoneInfo("Europe/Amsterdam")
PAGE_SIZE = 50  # REQ-BE-094
RETENTION_MIN_DAYS = 1  # REQ-BE-093
RETENTION_MAX_DAYS = 90
STATUSES = ("ok", "empty", "error")
DELETED_PERSON_NAME = "Verwijderde gebruiker"


@dataclass
class CallContext:
    """Who and what a Gemini call is for (REQ-BE-091)."""

    person_id: int | None
    message_id: int | None = None
    activity: str = "chat"


# --- recording (REQ-BE-091, REQ-BE-092) ----------------------------------------------------------


def record_call(
    ctx: CallContext | None,
    cfg: AiConfig,
    *,
    request_body: dict,
    duration_ms: int,
    status: str,
    http_status: int | None = None,
    error_message: str | None = None,
    usage: dict | None = None,
    response_text: str | None = None,
) -> None:
    """Store one call record in its own session; a failure is logged and never reaches the chat."""
    if ctx is None:
        return
    usage = usage or {}
    debug = bool(cfg.debug_log_enabled)
    db = SessionLocal()
    try:
        db.add(
            AiCall(
                person_id=ctx.person_id,
                message_id=ctx.message_id,
                activity=ctx.activity,
                model=cfg.model or "",
                status=status,
                http_status=http_status,
                duration_ms=max(0, int(duration_ms)),
                error_message=error_message,
                prompt_tokens=int(usage.get("promptTokenCount") or 0),
                output_tokens=int(usage.get("candidatesTokenCount") or 0),
                thinking_tokens=int(usage.get("thoughtsTokenCount") or 0),
                cached_tokens=int(usage.get("cachedContentTokenCount") or 0),
                # The API key travels in a header, so it is never part of the stored bodies.
                request_body=json.dumps(request_body, ensure_ascii=False) if debug else None,
                response_body=response_text if debug else None,
            )
        )
        db.commit()
    except Exception:
        logger.exception("Storing the AI call record failed")
        db.rollback()
    finally:
        db.close()


# --- debug content (REQ-BE-093) ------------------------------------------------------------------


def _has_content():
    return (AiCall.request_body.isnot(None)) | (AiCall.response_body.isnot(None))


def _clear(query) -> int:
    return query.filter(_has_content()).update(
        {AiCall.request_body: None, AiCall.response_body: None}, synchronize_session=False
    )


def clear_all_content(db: Session) -> int:
    count = _clear(db.query(AiCall))
    db.commit()
    return count


def clear_person_content(db: Session, person_id: int) -> int:
    """Called when a user clears their conversation; the caller commits."""
    return _clear(db.query(AiCall).filter(AiCall.person_id == person_id))


def forget_person(db: Session, person_id: int) -> None:
    """Before a person is deleted: keep tokens and costs, drop the link and the content."""
    db.query(AiCall).filter(AiCall.person_id == person_id).update(
        {AiCall.person_id: None, AiCall.request_body: None, AiCall.response_body: None},
        synchronize_session=False,
    )


def purge_old_content(db: Session, now: datetime | None = None) -> int:
    cfg = db.query(AiConfig).first()
    days = (cfg.debug_retention_days if cfg else None) or 7
    now = now or datetime.now(UTC)
    cutoff = _naive_utc(now - timedelta(days=days))
    count = _clear(db.query(AiCall).filter(AiCall.created_at < cutoff))
    db.commit()
    if count:
        logger.info("AI debug log: content of %d calls older than %d days removed", count, days)
    return count


# --- prices and costs (REQ-BE-095, REQ-BE-096) ---------------------------------------------------


def _naive_utc(moment: datetime) -> datetime:
    """SQLite stores naive UTC datetimes."""
    return moment.astimezone(UTC).replace(tzinfo=None) if moment.tzinfo else moment


def local_day(created_at: datetime) -> date:
    moment = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
    return moment.astimezone(TZ).date()


def today_local() -> date:
    return datetime.now(TZ).date()


class PriceBook:
    """All prices, to look up the one valid for a model on a day."""

    def __init__(self, db: Session):
        self.by_model: dict[str, list[AiModelPrice]] = {}
        for price in db.query(AiModelPrice).order_by(AiModelPrice.valid_from.desc(), AiModelPrice.id.desc()):
            self.by_model.setdefault(price.model, []).append(price)

    def price_on(self, model: str, day: date) -> AiModelPrice | None:
        return next((p for p in self.by_model.get(model, []) if p.valid_from <= day), None)

    def cost(self, call: AiCall) -> float | None:
        """None when the model had no valid price on the day of the call."""
        price = self.price_on(call.model, local_day(call.created_at))
        if price is None:
            return None
        output = (call.output_tokens or 0) + (call.thinking_tokens or 0)
        return ((call.prompt_tokens or 0) * price.input_price_per_1m + output * price.output_price_per_1m) / 1_000_000


def price_to_dict(price: AiModelPrice) -> dict:
    return {
        "id": price.id,
        "model": price.model,
        "input_price_per_1m": price.input_price_per_1m,
        "output_price_per_1m": price.output_price_per_1m,
        "valid_from": price.valid_from.isoformat(),
    }


def list_prices(db: Session) -> list[dict]:
    """Every priced, logged or configured model, with its price history (REQ-BE-095)."""
    book = PriceBook(db)
    logged = {m for (m,) in db.query(AiCall.model).distinct() if m}
    cfg = db.query(AiConfig).first()
    configured = cfg.model if cfg and cfg.model else None
    models = set(book.by_model) | logged | ({configured} if configured else set())
    today = today_local()
    return [
        {
            "model": model,
            "configured": model == configured,
            "logged": model in logged,
            "has_price": bool(book.by_model.get(model)),
            "current_price": price_to_dict(p) if (p := book.price_on(model, today)) else None,
            "prices": [price_to_dict(p) for p in book.by_model.get(model, [])],
        }
        for model in sorted(models)
    ]


def add_price(db: Session, model: str, input_price: float, output_price: float, valid_from: date) -> AiModelPrice:
    model = (model or "").strip()[:100]
    if not model:
        raise ValueError("Vul een model in")
    if input_price < 0 or output_price < 0:
        raise ValueError("Een prijs kan niet negatief zijn")
    price = AiModelPrice(
        model=model, input_price_per_1m=input_price, output_price_per_1m=output_price, valid_from=valid_from
    )
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


def delete_price(db: Session, price_id: int) -> bool:
    deleted = db.query(AiModelPrice).filter(AiModelPrice.id == price_id).delete()
    db.commit()
    return bool(deleted)


# --- call log (REQ-BE-094) -----------------------------------------------------------------------


def _period_bounds(date_from: date | None, date_to: date | None) -> tuple[datetime | None, datetime | None]:
    """Local days to naive UTC bounds; the end is exclusive."""
    start = _naive_utc(datetime.combine(date_from, time.min, TZ)) if date_from else None
    end = _naive_utc(datetime.combine(date_to + timedelta(days=1), time.min, TZ)) if date_to else None
    return start, end


def _person_names(db: Session) -> dict[int, str]:
    return {p.id: p.name for p in db.query(Person.id, Person.name)}


def _iso_utc(moment: datetime) -> str:
    return (moment if moment.tzinfo else moment.replace(tzinfo=UTC)).isoformat()


def call_to_dict(call: AiCall, book: PriceBook, names: dict[int, str], *, with_content: bool = False) -> dict:
    data: dict[str, Any] = {
        "id": call.id,
        "created_at": _iso_utc(call.created_at),
        "person": (
            {"id": call.person_id, "name": names.get(call.person_id, DELETED_PERSON_NAME)} if call.person_id else None
        ),
        "message_id": call.message_id,
        "activity": call.activity,
        "model": call.model,
        "status": call.status,
        "http_status": call.http_status,
        "duration_ms": call.duration_ms,
        "error_message": call.error_message,
        "prompt_tokens": call.prompt_tokens or 0,
        "output_tokens": call.output_tokens or 0,
        "thinking_tokens": call.thinking_tokens or 0,
        "cached_tokens": call.cached_tokens or 0,
        "cost_eur": book.cost(call),
        "has_content": bool(call.request_body or call.response_body),
    }
    if with_content:
        data["request"] = _parse_json(call.request_body)
        data["response"] = _parse_json(call.response_body)
    return data


def _parse_json(text: str | None):
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return text


def list_calls(
    db: Session,
    *,
    person_id: int | None = None,
    status: str | None = None,
    activity: str | None = None,
    message_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
) -> dict:
    query = db.query(AiCall)
    if person_id:
        query = query.filter(AiCall.person_id == person_id)
    if status:
        query = query.filter(AiCall.status == status)
    if activity:
        query = query.filter(AiCall.activity == activity)
    if message_id:
        query = query.filter(AiCall.message_id == message_id)
    start, end = _period_bounds(date_from, date_to)
    if start:
        query = query.filter(AiCall.created_at >= start)
    if end:
        query = query.filter(AiCall.created_at < end)
    total = query.count()
    page = max(1, page)
    calls = query.order_by(AiCall.id.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
    book = PriceBook(db)
    names = _person_names(db)
    return {
        "items": [call_to_dict(c, book, names) for c in calls],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "activities": sorted(a for (a,) in db.query(AiCall.activity).distinct() if a),
    }


def get_call(db: Session, call_id: int) -> dict | None:
    call = db.get(AiCall, call_id)
    if call is None:
        return None
    return call_to_dict(call, PriceBook(db), _person_names(db), with_content=True)


# --- cost overview (REQ-BE-097) ------------------------------------------------------------------


def _bucket() -> dict:
    return {
        "calls": 0,
        "prompt_tokens": 0,
        "output_tokens": 0,
        "thinking_tokens": 0,
        "cost_eur": 0.0,
        "unpriced_calls": 0,
    }


def _add(bucket: dict, call: AiCall, cost: float | None) -> None:
    bucket["calls"] += 1
    bucket["prompt_tokens"] += call.prompt_tokens or 0
    bucket["output_tokens"] += call.output_tokens or 0
    bucket["thinking_tokens"] += call.thinking_tokens or 0
    if cost is None:
        bucket["unpriced_calls"] += 1
    else:
        bucket["cost_eur"] += cost


def cost_report(db: Session, date_from: date | None = None, date_to: date | None = None) -> dict:
    today = today_local()
    if date_from is None and date_to is None:
        date_from = today.replace(day=1)
        date_to = (date_from + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    date_from = date_from or date_to
    date_to = date_to or date_from
    if date_to < date_from:
        raise ValueError("De einddatum ligt voor de begindatum")

    start, end = _period_bounds(date_from, date_to)
    calls = db.query(AiCall).filter(AiCall.created_at >= start, AiCall.created_at < end).all()
    book = PriceBook(db)
    names = _person_names(db)

    total = _bucket()
    by_activity: dict[str, dict] = {}
    by_model: dict[str, dict] = {}
    by_person: dict[int | None, dict] = {}
    by_day: dict[date, dict] = {}
    day = date_from
    while day <= date_to:
        by_day[day] = {"calls": 0, "cost_eur": 0.0, "unpriced_calls": 0}
        day += timedelta(days=1)

    for call in calls:
        cost = book.cost(call)
        _add(total, call, cost)
        _add(by_activity.setdefault(call.activity, _bucket()), call, cost)
        _add(by_model.setdefault(call.model, _bucket()), call, cost)
        _add(by_person.setdefault(call.person_id, _bucket()), call, cost)
        bucket = by_day.setdefault(local_day(call.created_at), {"calls": 0, "cost_eur": 0.0, "unpriced_calls": 0})
        bucket["calls"] += 1
        if cost is None:
            bucket["unpriced_calls"] += 1
        else:
            bucket["cost_eur"] += cost

    active_users = len([p for p in by_person if p is not None])
    by_cost = lambda item: (-item["cost_eur"], -item["calls"])  # noqa: E731
    return {
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "summary": {
            **total,
            "active_users": active_users,
            "avg_cost_per_user": total["cost_eur"] / active_users if active_users else 0.0,
        },
        "by_activity": sorted(({"activity": a, **b} for a, b in by_activity.items()), key=by_cost),
        "by_model": sorted(
            (
                {
                    "model": m,
                    **b,
                    "current_price": price_to_dict(p) if (p := book.price_on(m, today)) else None,
                }
                for m, b in by_model.items()
            ),
            key=by_cost,
        ),
        "by_user": sorted(
            (
                {
                    "person_id": p,
                    "name": names.get(p, DELETED_PERSON_NAME) if p else DELETED_PERSON_NAME,
                    **b,
                }
                for p, b in by_person.items()
            ),
            key=by_cost,
        ),
        "by_day": [{"date": d.isoformat(), **b} for d, b in sorted(by_day.items())],
    }
