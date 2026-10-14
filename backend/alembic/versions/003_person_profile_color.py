"""Add Person.profile_color and backfill from sort_order index."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.services.color_palette import BRAND_LABELS

revision: str = "003_person_profile_color"
down_revision: str | None = "002_color_labels"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("persons") as batch_op:
        batch_op.add_column(sa.Column("profile_color", sa.String(length=20), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, sort_order FROM persons ORDER BY sort_order, id")).fetchall()
    for index, row in enumerate(rows):
        # Preserve previous index-based assignment for existing users
        label = BRAND_LABELS[index % len(BRAND_LABELS)]
        conn.execute(
            sa.text("UPDATE persons SET profile_color = :label WHERE id = :id"),
            {"label": label, "id": row.id},
        )


def downgrade() -> None:
    with op.batch_alter_table("persons") as batch_op:
        batch_op.drop_column("profile_color")
