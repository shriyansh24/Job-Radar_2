import asyncio
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base

# Import ALL models so Base.metadata is fully populated
from importlib import import_module
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

from app.auth.models import User
from app.jobs.models import Job
from app.pipeline.models import Application
from app.analytics.service import AnalyticsService

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = uuid.uuid4()

    async with async_session() as session:
        user = User(id=user_id, email="test@example.com", password_hash="hash")
        session.add(user)

        jobs = []
        for i in range(500):
            jobs.append(
                Job(
                    id=f"job-{i}",
                    user_id=user_id,
                    company_name="Test",
                    source="manual", # FIX NOT NULL CONSTRAINT
                    title="Eng",
                    is_active=i % 2 == 0,
                    is_enriched=i % 3 == 0,
                    scraped_at=datetime.now(timezone.utc)
                )
            )
        session.add_all(jobs)

        apps = []
        statuses = ["saved", "applied", "screening", "interviewing", "offer", "accepted", "rejected"]
        for i in range(500):
            apps.append(
                Application(
                    user_id=user_id,
                    job_id=f"job-{i}",
                    company_name="Test Co",
                    position_title="Engineer",
                    status=statuses[i % len(statuses)]
                )
            )
        session.add_all(apps)
        await session.commit()

    async with async_session() as session:
        svc = AnalyticsService(session)

        # Warmup
        await svc.get_funnel(user_id)
        await svc.get_overview(user_id)

        start_funnel = time.perf_counter()
        for _ in range(100):
            await svc.get_funnel(user_id)
        end_funnel = time.perf_counter()
        print(f"BASELINE: get_funnel 100 iterations: {end_funnel - start_funnel:.4f} seconds")

        start_ov = time.perf_counter()
        for _ in range(100):
            await svc.get_overview(user_id)
        end_ov = time.perf_counter()
        print(f"BASELINE: get_overview 100 iterations: {end_ov - start_ov:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
