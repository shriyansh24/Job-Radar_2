from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from importlib import import_module

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import ALL models so Base.metadata is fully populated
from app.database import Base
from app.dependencies import get_db

MODEL_MODULES = (
    "app.auth.models",
    "app.auto_apply.form_learning",
    "app.auto_apply.models",
    "app.companies.models",
    "app.copilot.models",
    "app.interview.models",
    "app.jobs.models",
    "app.pipeline.models",
    "app.profile.models",
    "app.resume.models",
    "app.salary.models",
    "app.scraping.models",
    "app.settings.models",
    "app.source_health.models",
)

for module_name in MODEL_MODULES:
    import_module(module_name)

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
