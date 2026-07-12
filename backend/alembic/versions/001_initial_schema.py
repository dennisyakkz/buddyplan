"""Initial Buddyplan schema (fresh install)."""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import app.models  # noqa: F401
    from app.database import Base

    Base.metadata.create_all(bind=op.get_bind())

    conn = op.get_bind()
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_agenda_items_anchor_date ON agenda_items (anchor_date)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_agenda_items_end_date ON agenda_items (end_date)"
    ))


def downgrade() -> None:
    import app.models  # noqa: F401
    from app.database import Base

    Base.metadata.drop_all(bind=op.get_bind())
