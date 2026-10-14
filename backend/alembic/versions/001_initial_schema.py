"""Initial Buddyplan schema (fresh install)."""

from collections.abc import Sequence

from sqlalchemy import text

from alembic import op

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    import app.models  # noqa: F401
    from app.database import Base

    Base.metadata.create_all(bind=op.get_bind())

    conn = op.get_bind()
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_agenda_items_anchor_date ON agenda_items (anchor_date)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_agenda_items_end_date ON agenda_items (end_date)"))


def downgrade() -> None:
    import app.models  # noqa: F401
    from app.database import Base

    Base.metadata.drop_all(bind=op.get_bind())
