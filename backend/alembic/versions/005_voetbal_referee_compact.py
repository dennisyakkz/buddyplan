"""Add the voetbal.nl referee compact mode and club to iCal feeds (REQ-BE-047, REQ-BE-048)."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005_voetbal_referee_compact"
down_revision: str | None = "004_voetbal_feed_options"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_COLUMNS = ("referee_compact", "club")


def upgrade() -> None:
    conn = op.get_bind()
    # 001 builds the schema from the current models, so fresh databases already have these columns
    columns = {col["name"] for col in sa.inspect(conn).get_columns("person_calendar_feeds")}
    with op.batch_alter_table("person_calendar_feeds") as batch_op:
        if "referee_compact" not in columns:
            batch_op.add_column(sa.Column("referee_compact", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "club" not in columns:
            batch_op.add_column(sa.Column("club", sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("person_calendar_feeds") as batch_op:
        for column in NEW_COLUMNS:
            batch_op.drop_column(column)
