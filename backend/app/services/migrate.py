from pathlib import Path

from alembic.config import Config

from alembic import command


def run_migrations() -> None:
    """Run Alembic migrations to bring the database schema to head."""
    alembic_ini = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    cfg = Config(str(alembic_ini))
    command.upgrade(cfg, "head")
