from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import ALL models so Base.metadata is fully populated
import app.analytics.models  # noqa: F401
import app.auth.models  # noqa: F401
import app.auto_apply.form_learning  # noqa: F401
import app.auto_apply.models  # noqa: F401
import app.companies.models  # noqa: F401
import app.copilot.models  # noqa: F401
import app.email.models  # noqa: F401
import app.interview.models  # noqa: F401
import app.jobs.models  # noqa: F401
import app.networking.models  # noqa: F401
import app.pipeline.models  # noqa: F401
import app.profile.models  # noqa: F401
import app.resume.archetypes  # noqa: F401
import app.resume.models  # noqa: F401
import app.salary.models  # noqa: F401
import app.scraping.dedup_feedback  # noqa: F401
import app.scraping.models  # noqa: F401
import app.settings.models  # noqa: F401
import app.source_health.models  # noqa: F401
from app.database import Base
from app.dependencies import get_db

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
