"""Add AI call records, model prices and the debug log settings (REQ-BE-091..096)."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "007_ai_monitoring"
down_revision: str | None = "006_ai_buddy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 001 builds the schema from the current models, so fresh databases already have all of this
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns("ai_config")}
    with op.batch_alter_table("ai_config") as batch_op:
        if "debug_log_enabled" not in columns:
            batch_op.add_column(sa.Column("debug_log_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "debug_retention_days" not in columns:
            batch_op.add_column(sa.Column("debug_retention_days", sa.Integer(), nullable=False, server_default="7"))

    if not inspector.has_table("ai_calls"):
        op.create_table(
            "ai_calls",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("person_id", sa.Integer(), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("message_id", sa.Integer(), sa.ForeignKey("ai_messages.id", ondelete="SET NULL"), nullable=True),
            sa.Column("activity", sa.String(length=30), nullable=False),
            sa.Column("model", sa.String(length=100), nullable=False),
            sa.Column("status", sa.String(length=10), nullable=False),
            sa.Column("http_status", sa.Integer(), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("prompt_tokens", sa.Integer(), nullable=True),
            sa.Column("output_tokens", sa.Integer(), nullable=True),
            sa.Column("thinking_tokens", sa.Integer(), nullable=True),
            sa.Column("cached_tokens", sa.Integer(), nullable=True),
            sa.Column("request_body", sa.Text(), nullable=True),
            sa.Column("response_body", sa.Text(), nullable=True),
        )
        op.create_index("ix_ai_calls_created_at", "ai_calls", ["created_at"])
        op.create_index("ix_ai_calls_person_id", "ai_calls", ["person_id"])
        op.create_index("ix_ai_calls_message_id", "ai_calls", ["message_id"])

    if not inspector.has_table("ai_model_prices"):
        op.create_table(
            "ai_model_prices",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("model", sa.String(length=100), nullable=False),
            sa.Column("input_price_per_1m", sa.Float(), nullable=False),
            sa.Column("output_price_per_1m", sa.Float(), nullable=False),
            sa.Column("valid_from", sa.Date(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_ai_model_prices_model", "ai_model_prices", ["model"])


def downgrade() -> None:
    op.drop_index("ix_ai_model_prices_model", table_name="ai_model_prices")
    op.drop_table("ai_model_prices")
    op.drop_index("ix_ai_calls_message_id", table_name="ai_calls")
    op.drop_index("ix_ai_calls_person_id", table_name="ai_calls")
    op.drop_index("ix_ai_calls_created_at", table_name="ai_calls")
    op.drop_table("ai_calls")
    with op.batch_alter_table("ai_config") as batch_op:
        batch_op.drop_column("debug_retention_days")
        batch_op.drop_column("debug_log_enabled")
