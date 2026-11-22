"""Add the AI buddy tables: settings, conversations and pending deletions (REQ-BE-081..087)."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "006_ai_buddy"
down_revision: str | None = "005_voetbal_referee_compact"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 001 builds the schema from the current models, so fresh databases already have these tables
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("ai_config"):
        op.create_table(
            "ai_config",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("api_key", sa.String(length=255), nullable=True),
            sa.Column("model", sa.String(length=100), nullable=True),
            sa.Column("system_prompt", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
    if not inspector.has_table("ai_messages"):
        op.create_table(
            "ai_messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("person_id", sa.Integer(), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_ai_messages_person_id", "ai_messages", ["person_id"])
    if not inspector.has_table("ai_pending_deletions"):
        op.create_table(
            "ai_pending_deletions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("person_id", sa.Integer(), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False),
            sa.Column("kind", sa.String(length=20), nullable=False),
            sa.Column("item_id", sa.Integer(), nullable=False),
            sa.Column("proposed_in_message_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_ai_pending_deletions_person_id", "ai_pending_deletions", ["person_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_pending_deletions_person_id", table_name="ai_pending_deletions")
    op.drop_table("ai_pending_deletions")
    op.drop_index("ix_ai_messages_person_id", table_name="ai_messages")
    op.drop_table("ai_messages")
    op.drop_table("ai_config")
