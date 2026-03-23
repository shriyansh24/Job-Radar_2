"""Tests for resume renderer and all three templates."""

from __future__ import annotations

import pytest

from app.resume.ir_schema import (
    ContactInfo,
    Education,
    Project,
    ResumeIR,
    WorkExperience,
)
from app.resume.renderer import ResumeRenderer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _full_ir() -> ResumeIR:
    """A fully-populated ResumeIR for testing."""
    return ResumeIR(
        contact=ContactInfo(
            name="Jane Doe",
            email="jane@example.com",
            phone="(555) 123-4567",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/janedoe",
            github="github.com/janedoe",
            website="janedoe.dev",
        ),
        summary="Senior software engineer with 8+ years of experience in full-stack development.",
        work=[
            WorkExperience(
                company="Acme Corp",
                title="Senior Engineer",
                start_date="Jan 2020",
                end_date=None,
                location="Remote",
                bullets=[
                    "Led migration of monolith to microservices, reducing deploy time by 60%",
                    "Mentored team of 5 junior engineers",
                ],
                tech_stack=["Python", "Go", "Kubernetes"],
                metrics=["60% deploy time reduction"],
            ),
            WorkExperience(
                company="Startup Inc",
                title="Software Engineer",
                start_date="Mar 2016",
                end_date="Dec 2019",
                location="San Francisco, CA",
                bullets=["Built real-time data pipeline processing 1M events/day"],
            ),
        ],
        education=[
            Education(
                institution="MIT",
                degree="B.S.",
                field="Computer Science",
                end_date="2016",
                gpa="3.8",
                highlights=["Summa Cum Laude"],
            ),
        ],
        skills=["Python", "TypeScript", "Go", "Kubernetes", "PostgreSQL"],
        skill_categories={
            "Languages": ["Python", "TypeScript", "Go"],
            "Infrastructure": ["Kubernetes", "Docker", "Terraform"],
        },
        projects=[
            Project(
                name="OpenWidget",
                description="Open-source dashboard framework",
                tech_stack=["React", "Python"],
                url="github.com/janedoe/openwidget",
                bullets=["500+ GitHub stars", "Used by 3 companies in production"],
            ),
        ],
        certifications=["AWS Solutions Architect Professional"],
        publications=["Scaling Microservices at Acme (2023)"],
        languages=["English", "Spanish"],
    )


def _minimal_ir() -> ResumeIR:
    """A minimally-populated ResumeIR — only required fields."""
    return ResumeIR(
        contact=ContactInfo(name="John Smith"),
    )


TEMPLATE_IDS = ["professional", "modern", "minimal"]


# ---------------------------------------------------------------------------
# Renderer unit tests
# ---------------------------------------------------------------------------


class TestResumeRenderer:
    def setup_method(self) -> None:
        self.renderer = ResumeRenderer()

    def test_get_templates_returns_all_three(self) -> None:
        templates = self.renderer.get_templates()
        assert len(templates) == 3
        ids = {t["id"] for t in templates}
        assert ids == {"professional", "modern", "minimal"}
        for t in templates:
            assert "name" in t
            assert "description" in t
            assert len(t["description"]) > 10

    @pytest.mark.parametrize("template_id", TEMPLATE_IDS)
    def test_render_html_full_ir(self, template_id: str) -> None:
        ir = _full_ir()
        html = self.renderer.render_html(ir, template_id=template_id)
        assert "<!DOCTYPE html>" in html
        assert "Jane Doe" in html
        assert "jane@example.com" in html
        assert "Acme Corp" in html
        assert "Senior Engineer" in html

    @pytest.mark.parametrize("template_id", TEMPLATE_IDS)
    def test_render_html_minimal_ir(self, template_id: str) -> None:
        ir = _minimal_ir()
        html = self.renderer.render_html(ir, template_id=template_id)
        assert "<!DOCTYPE html>" in html
        assert "John Smith" in html
        # Should not contain section headers for empty sections
        assert "Acme Corp" not in html

    @pytest.mark.parametrize("template_id", TEMPLATE_IDS)
    def test_render_html_from_dict(self, template_id: str) -> None:
        ir_dict = _full_ir().model_dump()
        html = self.renderer.render_html(ir_dict, template_id=template_id)
        assert "Jane Doe" in html

    def test_render_html_unknown_template_raises(self) -> None:
        ir = _minimal_ir()
        with pytest.raises(ValueError, match="Unknown template"):
            self.renderer.render_html(ir, template_id="nonexistent")

    def test_render_html_invalid_input_raises(self) -> None:
        with pytest.raises(TypeError, match="Expected ResumeIR or dict"):
            self.renderer.render_html("not a dict")  # type: ignore[arg-type]

    @pytest.mark.parametrize("template_id", TEMPLATE_IDS)
    def test_missing_optional_sections_omitted(self, template_id: str) -> None:
        """Templates should not show section headers for empty sections."""
        ir = ResumeIR(
            contact=ContactInfo(name="Test User", email="test@test.com"),
            work=[
                WorkExperience(
                    company="SomeCo",
                    title="Dev",
                    bullets=["Did things"],
                )
            ],
            # No education, projects, certifications, etc.
        )
        html = self.renderer.render_html(ir, template_id=template_id)
        assert "Test User" in html
        assert "SomeCo" in html
        # These headers should not appear
        lower = html.lower()
        assert "certifications" not in lower
        assert "publications" not in lower
        assert "languages" not in lower

    @pytest.mark.parametrize("template_id", TEMPLATE_IDS)
    def test_skill_categories_rendered(self, template_id: str) -> None:
        ir = _full_ir()
        html = self.renderer.render_html(ir, template_id=template_id)
        assert "Languages" in html
        assert "Infrastructure" in html

    @pytest.mark.parametrize("template_id", TEMPLATE_IDS)
    def test_projects_rendered(self, template_id: str) -> None:
        ir = _full_ir()
        html = self.renderer.render_html(ir, template_id=template_id)
        assert "OpenWidget" in html

    @pytest.mark.parametrize("template_id", TEMPLATE_IDS)
    def test_education_rendered(self, template_id: str) -> None:
        ir = _full_ir()
        html = self.renderer.render_html(ir, template_id=template_id)
        assert "MIT" in html
        assert "Computer Science" in html

    def test_modern_has_two_column_layout(self) -> None:
        ir = _full_ir()
        html = self.renderer.render_html(ir, template_id="modern")
        assert "sidebar" in html
        assert "main" in html

    def test_minimal_has_no_color(self) -> None:
        ir = _full_ir()
        html = self.renderer.render_html(ir, template_id="minimal")
        # Minimal uses only black on white — no accent colors
        assert "--accent" not in html

    def test_professional_has_skill_tags(self) -> None:
        ir = _full_ir()
        html = self.renderer.render_html(ir, template_id="professional")
        assert "skill-tag" in html

    def test_modern_has_accent_color_variable(self) -> None:
        ir = _full_ir()
        html = self.renderer.render_html(ir, template_id="modern")
        assert "--accent" in html
