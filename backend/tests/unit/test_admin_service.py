from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.service import AdminService
from app.auth.models import User
from app.jobs.models import Job
from app.pipeline.models import Application


async def _create_user(db_session: AsyncSession, email: str = "admin-unit@example.com") -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_health_check_reports_connected_database(db_session: AsyncSession) -> None:
    service = AdminService(db_session)

    result = await service.health_check()

    assert result == {"status": "ok", "database": "connected"}


@pytest.mark.asyncio
async def test_diagnostics_counts_jobs_and_applications(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    db_session.add(Job(id="admin-job", user_id=user.id, source="manual", title="Admin Role"))
    db_session.add(
        Application(
            user_id=user.id,
            job_id="admin-job",
            company_name="AdminCo",
            position_title="Admin Role",
            source="manual",
        )
    )
    await db_session.commit()

    service = AdminService(db_session)
    diagnostics = await service.diagnostics()

    assert diagnostics["job_count"] == 1
    assert diagnostics["application_count"] == 1
    assert isinstance(diagnostics["python_version"], str)
    assert isinstance(diagnostics["platform"], str)


@pytest.mark.asyncio
async def test_export_data_returns_only_user_owned_records(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, "export-owner@example.com")
    other_user = await _create_user(db_session, "export-other@example.com")

    db_session.add_all(
        [
            Job(
                id="owned-job",
                user_id=user.id,
                source="manual",
                title="Owned Job",
                company_name="OwnedCo",
            ),
            Job(
                id="other-job",
                user_id=other_user.id,
                source="manual",
                title="Other Job",
                company_name="OtherCo",
            ),
        ]
    )
    db_session.add_all(
        [
            Application(
                user_id=user.id,
                job_id="owned-job",
                company_name="OwnedCo",
                position_title="Owned Job",
                source="manual",
            ),
            Application(
                user_id=other_user.id,
                job_id="other-job",
                company_name="OtherCo",
                position_title="Other Job",
                source="manual",
            ),
        ]
    )
    await db_session.commit()

    service = AdminService(db_session)
    exported = await service.export_data(user.id)
    payload = json.loads(exported.decode())

    assert [job["id"] for job in payload["jobs"]] == ["owned-job"]
    assert [app["company_name"] for app in payload["applications"]] == ["OwnedCo"]
    stored_jobs = (await db_session.scalars(select(Job))).all()
    assert len(stored_jobs) == 2
