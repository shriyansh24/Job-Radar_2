from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.resume.models import ResumeVersion
from app.resume.renderer import ResumeRenderer
from app.resume.service import ResumeService
from app.shared.errors import ValidationError


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
async def test_resume_service_lists_templates_and_renders_preview(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid.uuid4()
    version = ResumeVersion(
        user_id=user_id,
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

    service = ResumeService(db_session)

    templates = await service.list_templates()
    preview = await service.render_preview(version.id, user_id, "modern")
    pdf_bytes, filename = await service.export_pdf(version.id, user_id, "minimal")

    assert [template["id"] for template in templates] == [
        "professional",
        "modern",
        "minimal",
    ]
    assert preview["template_id"] == "modern"
    assert "Jane Doe" in preview["html"]
    assert "Built a shared UI platform" in preview["html"]
    assert pdf_bytes == b"%PDF-test"
    assert filename == "Staff-Resume-minimal.pdf"


@pytest.mark.asyncio
async def test_resume_service_preview_rejects_unknown_template(
    db_session: AsyncSession,
) -> None:
    user_id = uuid.uuid4()
    version = ResumeVersion(
        user_id=user_id,
        filename="resume.pdf",
        parsed_text="Jane Doe",
        parsed_structured=_structured_resume(),
        is_default=True,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)

    service = ResumeService(db_session)

    with pytest.raises(ValidationError, match="Unknown template"):
        await service.render_preview(version.id, user_id, "nonexistent")
