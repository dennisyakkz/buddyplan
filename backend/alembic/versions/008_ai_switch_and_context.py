"""Add the AI buddy on/off switch and the number of context messages (REQ-BE-081, REQ-BE-087)."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "008_ai_switch_and_context"
down_revision: str | None = "007_ai_monitoring"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 001 builds the schema from the current models, so fresh databases already have these columns
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("ai_config")}
    with op.batch_alter_table("ai_config") as batch_op:
        if "enabled" not in columns:
            batch_op.add_column(sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "context_messages" not in columns:
            batch_op.add_column(sa.Column("context_messages", sa.Integer(), nullable=False, server_default="20"))


def downgrade() -> None:
    with op.batch_alter_table("ai_config") as batch_op:
        batch_op.drop_column("context_messages")
        batch_op.drop_column("enabled")
