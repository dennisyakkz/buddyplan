"""AI buddy API (REQ-BE-080..089): chat for logged-in users, settings and monitoring (REQ-BE-090..097) for administrators."""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import ai_buddy, ai_monitoring
from app.services.current_user import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


class AiMessageCreate(BaseModel):
    text: str


class AiConfigUpdate(BaseModel):
    # An empty or missing key keeps the stored one: the page never receives it back (REQ-BE-081).
    api_key: str | None = None
    clear_api_key: bool = False
    model: str | None = None
    # Empty means the model's own default; only applied for Gemini 3/4 models (REQ-BE-098).
    thinking_level: str | None = None
    # Empty restores the default prompt (REQ-BE-082).
    system_prompt: str | None = None
    # Debug log (REQ-BE-092, REQ-BE-093); missing keeps the current setting.
    debug_log_enabled: bool | None = None
    debug_retention_days: int | None = None
    # On/off switch and context size (REQ-BE-081, REQ-BE-087); missing keeps the current setting.
    enabled: bool | None = None
    context_messages: int | None = None


class AiModelsRequest(BaseModel):
    api_key: str | None = None


class AiPriceCreate(BaseModel):
    model: str
    input_price_per_1m: float = Field(ge=0)
    output_price_per_1m: float = Field(ge=0)
    valid_from: date


@router.get("/ai/status")
def ai_status(_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return {"configured": ai_buddy.is_configured(db)}


@router.get("/ai/messages")
def list_ai_messages(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return [ai_buddy.message_to_dict(m) for m in ai_buddy.conversation(db, user.id)]


@router.post("/ai/messages")
def send_ai_message(data: AiMessageCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user_message, reply = ai_buddy.send_message(db, user, data.text)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ai_buddy.AiNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except ai_buddy.AiUnavailable as exc:
        logger.warning("AI buddy request failed: %s", exc)
        raise HTTPException(502, ai_buddy.UNAVAILABLE_MESSAGE) from exc
    return {"user_message": ai_buddy.message_to_dict(user_message), "reply": ai_buddy.message_to_dict(reply)}


@router.delete("/ai/messages")
def clear_ai_messages(user=Depends(get_current_user), db: Session = Depends(get_db)):
    ai_buddy.clear_conversation(db, user.id)
    return {"ok": True}


@router.get("/admin/ai/config")
def admin_get_ai_config(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    return ai_buddy.config_to_dict(ai_buddy.get_config(db))


@router.put("/admin/ai/config")
def admin_update_ai_config(data: AiConfigUpdate, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    try:
        cfg = ai_buddy.update_config(
            db,
            api_key=data.api_key,
            clear_api_key=data.clear_api_key,
            model=data.model,
            thinking_level=data.thinking_level,
            system_prompt=data.system_prompt,
            debug_log_enabled=data.debug_log_enabled,
            debug_retention_days=data.debug_retention_days,
            enabled=data.enabled,
            context_messages=data.context_messages,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return ai_buddy.config_to_dict(cfg)


@router.post("/admin/ai/models")
def admin_list_ai_models(data: AiModelsRequest, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    """Models for the key typed on the page, or for the stored key."""
    api_key = (data.api_key or "").strip()
    if not api_key:
        cfg = ai_buddy.get_config(db)
        api_key = (cfg.api_key if cfg else None) or ""
    if not api_key:
        raise HTTPException(400, "Vul eerst een Gemini API-key in")
    try:
        return ai_buddy.list_models(api_key)
    except ai_buddy.AiUnavailable as exc:
        raise HTTPException(502, f"Modellen ophalen mislukt: {exc}") from exc


# --- monitoring (REQ-BE-090..097) -----------------------------------------------------------------


@router.get("/admin/ai/calls")
def admin_list_ai_calls(
    person_id: int | None = None,
    status: str | None = None,
    activity: str | None = None,
    message_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    if status and status not in ai_monitoring.STATUSES:
        raise HTTPException(400, "Onbekende status")
    return ai_monitoring.list_calls(
        db,
        person_id=person_id,
        status=status,
        activity=activity,
        message_id=message_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
    )


@router.delete("/admin/ai/calls/content")
def admin_clear_ai_call_content(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    return {"cleared": ai_monitoring.clear_all_content(db)}


@router.get("/admin/ai/calls/{call_id}")
def admin_get_ai_call(call_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    call = ai_monitoring.get_call(db, call_id)
    if call is None:
        raise HTTPException(404, "Aanroep niet gevonden")
    return call


@router.get("/admin/ai/prices")
def admin_list_ai_prices(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    return ai_monitoring.list_prices(db)


@router.post("/admin/ai/prices", status_code=201)
def admin_add_ai_price(data: AiPriceCreate, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    try:
        price = ai_monitoring.add_price(
            db, data.model, data.input_price_per_1m, data.output_price_per_1m, data.valid_from
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return ai_monitoring.price_to_dict(price)


@router.delete("/admin/ai/prices/{price_id}")
def admin_delete_ai_price(price_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    if not ai_monitoring.delete_price(db, price_id):
        raise HTTPException(404, "Prijs niet gevonden")
    return {"ok": True}


@router.get("/admin/ai/costs")
def admin_ai_costs(
    date_from: date | None = None,
    date_to: date | None = None,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return ai_monitoring.cost_report(db, date_from, date_to)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
