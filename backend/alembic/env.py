from logging.config import fileConfig

from alembic import context
from app.database import Base
from app.database import engine as app_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", str(app_engine.url))


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = app_engine

    with connectable.connect() as connection:
        # REQ-BE-071: batch migrations rebuild a table by dropping the old one. With foreign keys on,
        # that drop fires ON DELETE CASCADE and wipes the child rows (e.g. every imported agenda item
        # of person_calendar_feeds). The pragma only takes effect outside a transaction.
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()
        try:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
            )

            with context.begin_transaction():
                context.run_migrations()

            violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError(f"Foreign key violations after migration: {violations[:10]}")
        finally:
            connection.rollback()
            # The connection goes back to the pool; later sessions rely on foreign keys being on.
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
