from pathlib import Path
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import APP_NAME, env_secret
from app.database import Base, SessionLocal, engine
from app.routers import api, pages
from app.services.migrate import run_migrations
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.seed import seed_database

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "static"


def _session_secret_key() -> str:
    return env_secret("SESSION_SECRET_KEY")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(title=f"{APP_NAME} Backend", lifespan=lifespan)

    run_migrations()
    Base.metadata.create_all(bind=engine)

    app.add_middleware(
        SessionMiddleware,
        secret_key=_session_secret_key(),
        session_cookie="buddyplan_session",
        https_only=False,
        same_site="lax",
    )

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(pages.router)
    app.include_router(api.router)

    return app


app = create_app()
