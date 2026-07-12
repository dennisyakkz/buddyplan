"""Migrate agenda feed colors from hex to brandbook labels."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.services.color_palette import hex_to_label

revision: str = "002_color_labels"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _migrate_color_column(table: str, column: str) -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(f"SELECT id, {column} AS color_value FROM {table} WHERE {column} IS NOT NULL AND {column} != ''")
    )
    for row in rows:
        label = hex_to_label(row.color_value)
        conn.execute(
            sa.text(f"UPDATE {table} SET {column} = :label WHERE id = :id"),
            {"label": label, "id": row.id},
        )


def upgrade() -> None:
    with op.batch_alter_table("person_calendar_feeds") as batch_op:
        batch_op.alter_column(
            "color",
            existing_type=sa.String(7),
            type_=sa.String(20),
            existing_nullable=True,
        )

    with op.batch_alter_table("person_google_calendar_feeds") as batch_op:
        batch_op.alter_column(
            "calendar_color",
            existing_type=sa.String(7),
            type_=sa.String(20),
            existing_nullable=True,
        )

    _migrate_color_column("person_calendar_feeds", "color")
    _migrate_color_column("person_google_calendar_feeds", "calendar_color")


def downgrade() -> None:
    with op.batch_alter_table("person_google_calendar_feeds") as batch_op:
        batch_op.alter_column(
            "calendar_color",
            existing_type=sa.String(20),
            type_=sa.String(7),
            existing_nullable=True,
        )

    with op.batch_alter_table("person_calendar_feeds") as batch_op:
        batch_op.alter_column(
            "color",
            existing_type=sa.String(20),
            type_=sa.String(7),
            existing_nullable=True,
        )
