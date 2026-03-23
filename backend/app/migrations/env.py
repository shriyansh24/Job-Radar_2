from __future__ import annotations

import asyncio
from importlib import import_module
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import URL, Connection, make_url
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models so Base.metadata is populated
from app.config import settings
from app.database import Base

MODEL_MODULES = (
    "app.auth.models",
    "app.auto_apply.models",
    "app.canonical_jobs.models",
    "app.companies.models",
    "app.copilot.models",
    "app.followup.models",
    "app.interview.models",
    "app.jobs.models",
    "app.notifications.models",
    "app.pipeline.models",
    "app.profile.models",
    "app.resume.models",
    "app.salary.models",
    "app.scraping.models",
    "app.search_expansion.models",
    "app.settings.models",
    "app.source_health.models",
)

for module_name in MODEL_MODULES:
    import_module(module_name)

config = context.config
if config.config_file_name is not None:
    config_path = Path(config.config_file_name)
    if config_path.is_file():
        fileConfig(str(config_path), disable_existing_loggers=False)

target_metadata = Base.metadata


def _get_database_url() -> URL:
    return make_url(settings.database_url)


def run_migrations_offline() -> None:
    url = _get_database_url()
    context.configure(
        url=url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    db_url = _get_database_url()
    # SQLite fallback
    if db_url.get_backend_name() == "sqlite":
        sync_engine = create_engine(
            db_url.set(drivername=db_url.drivername.replace("+aiosqlite", "")),
        )
        with sync_engine.connect() as connection:
            do_run_migrations(connection)
        sync_engine.dispose()
        return

    async_engine = create_async_engine(db_url, poolclass=pool.NullPool)
    async with async_engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await async_engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
