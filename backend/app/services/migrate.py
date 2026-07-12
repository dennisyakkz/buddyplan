from pathlib import Path

from alembic import command
from alembic.config import Config


def run_migrations() -> None:
    """Run Alembic migrations to bring the database schema to head."""
    alembic_ini = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    cfg = Config(str(alembic_ini))
    command.upgrade(cfg, "head")
