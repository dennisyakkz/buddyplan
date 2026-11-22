"""Add the AI buddy thinking level (REQ-BE-098)."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "009_ai_thinking_level"
down_revision: str | None = "008_ai_switch_and_context"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 001 builds the schema from the current models, so fresh databases already have this column
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("ai_config")}
    if "thinking_level" not in columns:
        with op.batch_alter_table("ai_config") as batch_op:
            batch_op.add_column(sa.Column("thinking_level", sa.String(length=20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ai_config") as batch_op:
        batch_op.drop_column("thinking_level")
