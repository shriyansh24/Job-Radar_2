from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.resume.models import ResumeVersion
from app.resume.renderer import ResumeRenderer


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"resume-api-{uuid.uuid4().hex[:8]}@test.com"
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


def _structured_resume() -> dict[str, object]:
    return {
        "contact": {
            "name": "Jane Doe",
            "email": "jane@example.com",
        },
        "summary": "Staff frontend engineer with design-system experience.",
        "work": [
            {
                "company": "Acme",
                "title": "Staff Frontend Engineer",
                "bullets": ["Built a shared UI platform"],
            }
        ],
        "skills": ["React", "TypeScript", "Design Systems"],
    }


@pytest.mark.asyncio
async def test_resume_templates_preview_and_export(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token, user_id = await _register_and_login(client)
    user_uuid = uuid.UUID(user_id)

    version = ResumeVersion(
        user_id=user_uuid,
        filename="resume-2026.pdf",
        label="Staff Resume",
        parsed_text="Jane Doe\nStaff frontend engineer",
        parsed_structured=_structured_resume(),
        is_default=True,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)

    monkeypatch.setattr(
        ResumeRenderer,
        "render_pdf",
        lambda self, ir, template_id="professional": b"%PDF-test",
    )

    templates_resp = await client.get("/api/v1/resume/templates", headers=_auth(token))
    preview_resp = await client.get(
        f"/api/v1/resume/versions/{version.id}/preview",
        params={"template_id": "modern"},
        headers=_auth(token),
    )
    export_resp = await client.get(
        f"/api/v1/resume/versions/{version.id}/export",
        params={"template_id": "minimal"},
        headers=_auth(token),
    )

    assert templates_resp.status_code == 200
    template_ids = [item["id"] for item in templates_resp.json()]
    assert template_ids == ["professional", "modern", "minimal"]

    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["template_id"] == "modern"
    assert "Jane Doe" in preview_data["html"]
    assert "Built a shared UI platform" in preview_data["html"]

    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"] == "application/pdf"
    assert 'attachment; filename="Staff-Resume-minimal.pdf"' == export_resp.headers[
        "content-disposition"
    ]
    assert export_resp.content == b"%PDF-test"


@pytest.mark.asyncio
async def test_resume_preview_rejects_unknown_template(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, user_id = await _register_and_login(client)
    user_uuid = uuid.UUID(user_id)

    version = ResumeVersion(
        user_id=user_uuid,
        filename="resume.pdf",
        parsed_text="Jane Doe",
        parsed_structured=_structured_resume(),
        is_default=True,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)

    preview_resp = await client.get(
        f"/api/v1/resume/versions/{version.id}/preview",
        params={"template_id": "nonexistent"},
        headers=_auth(token),
    )

    assert preview_resp.status_code == 422
    assert "Unknown template" in preview_resp.json()["detail"]
