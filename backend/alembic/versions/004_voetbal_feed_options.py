"""Add voetbal.nl options to iCal feeds: is_voetbal, home_away_mode and own_team."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_voetbal_feed_options"
down_revision: str | None = "003_person_profile_color"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_COLUMNS = ("is_voetbal", "home_away_mode", "own_team")


def upgrade() -> None:
    conn = op.get_bind()
    # 001 builds the schema from the current models, so fresh databases already have these columns
    columns = {col["name"] for col in sa.inspect(conn).get_columns("person_calendar_feeds")}
    with op.batch_alter_table("person_calendar_feeds") as batch_op:
        if "is_voetbal" not in columns:
            batch_op.add_column(sa.Column("is_voetbal", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "home_away_mode" not in columns:
            batch_op.add_column(sa.Column("home_away_mode", sa.Boolean(), nullable=False, server_default=sa.true()))
        if "own_team" not in columns:
            batch_op.add_column(sa.Column("own_team", sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("person_calendar_feeds") as batch_op:
        for column in NEW_COLUMNS:
            batch_op.drop_column(column)
