from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME_DISPLAY
from app.database import SessionLocal
from app.services.dashboard_service import PersonService

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.globals["app_name"] = APP_NAME_DISPLAY


def _login_or_setup_url() -> str:
    db = SessionLocal()
    try:
        if not PersonService(db).has_login_users():
            return "/setup"
    finally:
        db.close()
    return "/login"


def _require_login(request: Request):
    if not request.session.get("person_id"):
        return RedirectResponse(url=_login_or_setup_url(), status_code=303)
    return None


def _require_admin(request: Request):
    redirect = _require_login(request)
    if redirect:
        return redirect
    person_id = request.session.get("person_id")
    db = SessionLocal()
    try:
        person = PersonService(db).get(int(person_id))
        if not person or not getattr(person, "is_admin", False):
            return RedirectResponse(url="/dashboard", status_code=303)
    finally:
        db.close()
    return None


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    redirect = _require_login(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("dashboard.html", {"request": request, "page": "dashboard"})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    redirect = _require_login(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("dashboard.html", {"request": request, "page": "dashboard"})


@router.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    redirect = _require_login(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("tasks.html", {"request": request, "page": "tasks"})


@router.get("/agenda", response_class=HTMLResponse)
def agenda_page(request: Request):
    redirect = _require_login(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("agenda.html", {"request": request, "page": "agenda"})


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    redirect = _require_login(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("profile.html", {"request": request, "page": "profile"})


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("admin_users.html", {"request": request, "page": "admin"})


@router.get("/admin/afvalwijzer", response_class=HTMLResponse)
def admin_afvalwijzer_page(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("admin_afvalwijzer.html", {"request": request, "page": "admin"})


@router.get("/admin/user/new", response_class=HTMLResponse)
def admin_user_new_page(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "admin_user_detail.html",
        {"request": request, "page": "admin", "user_id": None},
    )


@router.get("/admin/user/{user_id}", response_class=HTMLResponse)
def admin_user_detail_page(request: Request, user_id: int):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "admin_user_detail.html",
        {"request": request, "page": "admin", "user_id": user_id},
    )

@router.get("/admin/google-calendar-api", response_class=HTMLResponse)
def admin_google_calendar_page(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("admin_google_calendar.html", {"request": request, "page": "admin"})


@router.get("/admin/upgrades", response_class=HTMLResponse)
def admin_upgrades_page(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("admin_upgrades.html", {"request": request, "page": "admin"})


@router.get("/google/callback", response_class=HTMLResponse)
def google_oauth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    redirect = _require_login(request)
    if redirect:
        return redirect

    return_to = request.session.pop("gcal_oauth_return_to", "/profile")
    person_id = request.session.pop("gcal_oauth_person_id", None)
    stored_nonce = request.session.pop("gcal_oauth_nonce", None)

    if error:
        return RedirectResponse(url=f"{return_to}?google_error={error}", status_code=303)

    if not code or not person_id:
        return RedirectResponse(url=f"{return_to}?google_error=invalid_callback", status_code=303)

    if stored_nonce and state != stored_nonce:
        return RedirectResponse(url=f"{return_to}?google_error=state_mismatch", status_code=303)

    db = SessionLocal()
    try:
        from app.models import GoogleApiConfig, PersonGoogleAuth
        from app.services.google_calendar_service import exchange_code, get_userinfo
        from datetime import datetime, timedelta, timezone

        cfg = db.query(GoogleApiConfig).first()
        if not cfg or not cfg.client_id or not cfg.client_secret:
            return RedirectResponse(url=f"{return_to}?google_error=no_config", status_code=303)

        base = str(request.base_url).rstrip("/")
        redirect_uri = cfg.redirect_uri_override or f"{base}/google/callback"

        token_data = exchange_code(cfg.client_id, cfg.client_secret, redirect_uri, code)

        try:
            userinfo = get_userinfo(token_data["access_token"])
            google_email = userinfo.get("email")
        except Exception:
            google_email = None

        auth = db.query(PersonGoogleAuth).filter(PersonGoogleAuth.person_id == person_id).first()
        if not auth:
            auth = PersonGoogleAuth(person_id=person_id)
            db.add(auth)

        now = datetime.now(timezone.utc)
        auth.access_token = token_data.get("access_token")
        auth.refresh_token = token_data.get("refresh_token", auth.refresh_token)
        expires_in = int(token_data.get("expires_in", 3600))
        auth.token_expiry = now + timedelta(seconds=expires_in)
        auth.google_email = google_email
        auth.updated_at = now
        db.commit()
    except Exception:
        return RedirectResponse(url=f"{return_to}?google_error=exchange_failed", status_code=303)
    finally:
        db.close()

    return RedirectResponse(url=f"{return_to}?google_linked=1", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    db = SessionLocal()
    try:
        if not PersonService(db).has_login_users():
            return RedirectResponse(url="/setup", status_code=303)
    finally:
        db.close()
    return templates.TemplateResponse("login.html", {"request": request, "page": "login"})


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request):
    db = SessionLocal()
    try:
        if PersonService(db).has_login_users():
            return RedirectResponse(url="/login", status_code=303)
    finally:
        db.close()
    return templates.TemplateResponse("setup.html", {"request": request, "page": "setup"})


@router.post("/setup")
async def setup_submit(request: Request):
    db = SessionLocal()
    try:
        if PersonService(db).has_login_users():
            return RedirectResponse(url="/login", status_code=303)

        form = await request.form()
        name = (form.get("name") or "").strip()
        username = (form.get("username") or "").strip()
        password = (form.get("password") or "").strip()

        if not name or not username or not password:
            return templates.TemplateResponse(
                "setup.html",
                {
                    "request": request,
                    "page": "setup",
                    "error": "Naam, username en wachtwoord zijn verplicht",
                },
                status_code=400,
            )

        try:
            PersonService(db).bootstrap_admin(name, username, password)
        except ValueError as exc:
            return templates.TemplateResponse(
                "setup.html",
                {"request": request, "page": "setup", "error": str(exc)},
                status_code=400,
            )
    finally:
        db.close()

    return RedirectResponse(url="/login", status_code=303)


@router.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    username = (form.get("username") or "").strip()
    password = (form.get("password") or "").strip()

    if not username or not password:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "page": "login", "error": "Username en wachtwoord zijn verplicht"},
            status_code=400,
        )

    db = SessionLocal()
    try:
        person = PersonService(db).verify_login(username, password)
    finally:
        db.close()

    if not person:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "page": "login", "error": "Onjuiste gegevens of inloggen niet toegestaan"},
            status_code=401,
        )

    request.session["person_id"] = person.id
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/logout", response_class=HTMLResponse)
def logout_page(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
