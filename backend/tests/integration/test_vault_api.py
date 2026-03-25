from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.models import CoverLetter
from app.resume.models import ResumeVersion


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"vault-api-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login_resp.json()["access_token"]
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me_resp.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_vault_resume_and_cover_letter_updates_persist(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, user_id = await _register_and_login(client)
    user_uuid = uuid.UUID(user_id)

    resume = ResumeVersion(
        user_id=user_uuid,
        filename="resume.pdf",
        label="Base Resume",
        parsed_text="Original resume text",
        is_default=False,
    )
    letter = CoverLetter(
        user_id=user_uuid,
        content="Original cover letter body",
        style="professional",
    )
    db_session.add_all([resume, letter])
    await db_session.commit()
    await db_session.refresh(resume)
    await db_session.refresh(letter)

    resume_resp = await client.patch(
        f"/api/v1/vault/resumes/{resume.id}",
        headers=_auth(token),
        params={"label": "Staff Resume"},
    )
    letter_resp = await client.patch(
        f"/api/v1/vault/cover-letters/{letter.id}",
        headers=_auth(token),
        params={"content": "Updated cover letter body"},
    )

    assert resume_resp.status_code == 200
    assert resume_resp.json()["label"] == "Staff Resume"
    assert letter_resp.status_code == 200
    assert letter_resp.json()["content"] == "Updated cover letter body"

    await db_session.refresh(resume)
    await db_session.refresh(letter)
    assert resume.label == "Staff Resume"
    assert letter.content == "Updated cover letter body"


@pytest.mark.asyncio
async def test_vault_updates_require_auth(client: AsyncClient) -> None:
    missing_auth_resume = await client.patch(
        f"/api/v1/vault/resumes/{uuid.uuid4()}",
        params={"label": "Nope"},
    )
    missing_auth_letter = await client.patch(
        f"/api/v1/vault/cover-letters/{uuid.uuid4()}",
        params={"content": "Nope"},
    )

    assert missing_auth_resume.status_code == 401
    assert missing_auth_letter.status_code == 401
