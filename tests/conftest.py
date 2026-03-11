"""Shared test fixtures for Phase 7A tests.

Provides an in-memory async SQLite engine and session for isolated testing.
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


@pytest_asyncio.fixture
async def async_engine():
    """Create an in-memory async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create an async session factory bound to the test engine."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def initialized_db(async_engine):
    """Create all tables (existing + migration table) in the test database.

    This simulates what init_db() does, but against the test engine.
    """
    from backend.database import Base
    from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Run Phase 7A migrations
        from backend.phase7a.migration import run_migrations
        await run_migrations(conn)

    yield async_engine
