from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models so Base.metadata is populated
from app.auth.models import User  # noqa: F401
from app.auto_apply.models import AutoApplyProfile, AutoApplyRule, AutoApplyRun  # noqa: F401
from app.canonical_jobs.models import CanonicalJob, RawJobSource  # noqa: F401
from app.companies.models import Company  # noqa: F401
from app.config import settings
from app.copilot.models import CoverLetter  # noqa: F401
from app.database import Base
from app.followup.models import FollowupReminder  # noqa: F401
from app.interview.models import InterviewSession  # noqa: F401
from app.jobs.models import Job  # noqa: F401
from app.notifications.models import Notification  # noqa: F401
from app.pipeline.models import Application, ApplicationStatusHistory  # noqa: F401
from app.profile.models import UserProfile  # noqa: F401
from app.resume.models import ResumeVersion  # noqa: F401
from app.salary.models import SalaryCache  # noqa: F401
from app.scraping.models import ScrapeAttempt, ScraperRun, ScrapeTarget  # noqa: F401
from app.search_expansion.models import (  # noqa: F401
    ExpansionRule,
    QueryPerformance,
    QueryTemplate,
)
from app.settings.models import SavedSearch  # noqa: F401
from app.source_health.models import SourceCheckLog, SourceRegistry  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    db_url = settings.database_url
    # SQLite fallback
    if db_url.startswith("sqlite"):
        from sqlalchemy import create_engine

        connectable = create_engine(db_url.replace("+aiosqlite", ""))
        with connectable.connect() as connection:
            do_run_migrations(connection)
        connectable.dispose()
        return

    connectable = create_async_engine(db_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
