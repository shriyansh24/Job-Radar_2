"""Tests for the WeasyPrint PDF renderer (B3)."""

from __future__ import annotations

import pytest

from app.resume.renderer import ResumeRenderer, _DictWrapper


def _can_import_weasyprint() -> bool:
    try:
        import weasyprint  # noqa: F401
        return True
    except (ImportError, OSError):
        return False


def _make_ir() -> dict:
    return {
        "contact": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/janedoe",
            "github": "github.com/janedoe",
        },
        "summary": "Experienced software engineer with 5 years of Python expertise.",
        "work": [
            {
                "company": "Acme Corp",
                "title": "Senior Engineer",
                "start_date": "Jan 2020",
                "end_date": "Present",
                "bullets": [
                    "Led team of 5 engineers building microservices",
                    "Reduced deploy time by 40% through CI/CD improvements",
                ],
            }
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "BS",
                "field": "Computer Science",
                "end_date": "2019",
                "gpa": "3.8",
            }
        ],
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "projects": [
            {
                "name": "OpenSource Tool",
                "description": "A CLI tool for developers",
                "bullets": ["Built with Python", "500+ stars on GitHub"],
            }
        ],
        "certifications": ["AWS Solutions Architect"],
        "languages": ["English", "Spanish"],
    }


class TestResumeRenderer:
    def test_get_templates(self):
        renderer = ResumeRenderer()
        templates = renderer.get_templates()
        assert len(templates) >= 1
        assert templates[0]["id"] == "professional"
        assert "name" in templates[0]
        assert "description" in templates[0]

    def test_render_html_produces_valid_html(self):
        renderer = ResumeRenderer()
        html = renderer.render_html(_make_ir())
        assert "<html>" in html
        assert "Jane Doe" in html
        assert "jane@example.com" in html
        assert "Acme Corp" in html
        assert "Senior Engineer" in html
        assert "Python" in html
        assert "MIT" in html

    def test_render_html_includes_all_sections(self):
        renderer = ResumeRenderer()
        html = renderer.render_html(_make_ir())
        assert "Experience" in html
        assert "Education" in html
        assert "Skills" in html
        assert "Projects" in html
        assert "Certifications" in html
        assert "Languages" in html

    @pytest.mark.skipif(
        not _can_import_weasyprint(),
        reason="WeasyPrint not installed or system deps missing",
    )
    def test_render_pdf_returns_pdf_bytes(self):
        renderer = ResumeRenderer()
        pdf = renderer.render_pdf(_make_ir())
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 1000

    def test_render_html_handles_minimal_ir(self):
        minimal_ir = {
            "contact": {"name": "Test User"},
        }
        renderer = ResumeRenderer()
        html = renderer.render_html(minimal_ir)
        assert "Test User" in html
        # Should not crash with missing sections
        assert "<html>" in html

    def test_render_html_handles_empty_contact(self):
        ir = {"contact": {}}
        renderer = ResumeRenderer()
        html = renderer.render_html(ir)
        assert "<html>" in html

    def test_render_html_with_skill_categories(self):
        ir = _make_ir()
        ir["skill_categories"] = {
            "Languages": ["Python", "Go"],
            "Databases": ["PostgreSQL", "Redis"],
        }
        # Remove flat skills to test categories
        ir["skills"] = []
        renderer = ResumeRenderer()
        html = renderer.render_html(ir)
        assert "Languages" in html
        assert "Databases" in html


class TestDictWrapper:
    def test_attribute_access(self):
        w = _DictWrapper({"name": "Jane", "age": 30})
        assert w.name == "Jane"
        assert w.age == 30

    def test_nested_dict(self):
        w = _DictWrapper({"contact": {"name": "Jane", "email": "j@e.com"}})
        assert w.contact.name == "Jane"

    def test_list_of_dicts(self):
        w = _DictWrapper({"work": [{"company": "Acme"}, {"company": "Beta"}]})
        assert w.work[0].company == "Acme"
        assert w.work[1].company == "Beta"

    def test_missing_key_returns_none(self):
        w = _DictWrapper({"name": "Jane"})
        assert w.missing_key is None

    def test_bool_true_for_nonempty(self):
        assert bool(_DictWrapper({"a": 1}))

    def test_bool_false_for_empty(self):
        assert not bool(_DictWrapper({}))

    def test_none_data(self):
        w = _DictWrapper(None)
        assert not bool(w)
        assert w.anything is None
