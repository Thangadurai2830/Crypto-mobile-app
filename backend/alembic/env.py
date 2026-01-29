"""Alembic environment."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from src.core.config import get_settings
from src.core.database import Base
from src.models import *  # noqa: F401, F403 - register all models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
# Sync URL for Alembic (SQLite or PostgreSQL with psycopg2)
database_url = settings.database_url.replace("+aiosqlite", "").replace("+asyncpg", "")
if "sqlite" in database_url and not database_url.startswith("sqlite"):
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
