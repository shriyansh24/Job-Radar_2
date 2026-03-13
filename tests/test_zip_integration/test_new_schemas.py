"""Test new Pydantic schemas for zip integration."""
import pytest
from backend.schemas import (
    DimensionScoreSchema,
    CouncilScoreResponse,
    ResumeVersionResponse,
    AutoApplyRunRequest,
    ApplicationResultResponse,
    AutoApplyAnalysis,
    ApplicationProfileRequest,
    ApplicationProfileResponse,
    CopilotRequest,
)


class TestDimensionScoreSchema:
    def test_create_valid(self):
        d = DimensionScoreSchema(
            grade="A", score=92, rationale="Strong match",
            gaps=["missing AWS"], suggestions=["Add AWS cert"]
        )
        assert d.grade == "A"
        assert d.score == 92

    def test_rejects_invalid_score(self):
        with pytest.raises(Exception):
            DimensionScoreSchema(grade="A", score=150, rationale="", gaps=[], suggestions=[])


class TestCouncilScoreResponse:
    def test_create_valid(self):
        dim = {"grade": "B", "score": 80, "rationale": "Good", "gaps": [], "suggestions": []}
        c = CouncilScoreResponse(
            skill_alignment=dim, experience_level=dim, impact_language=dim,
            ats_keyword_density=dim, structural_quality=dim, cultural_signals=dim,
            growth_trajectory=dim, overall_grade="B", overall_score=80,
            top_gaps=[], missing_keywords=[], strong_points=[], suggested_bullets=[],
            council_consensus=0.85,
        )
        assert c.overall_grade == "B"


class TestResumeVersionResponse:
    def test_create_valid(self):
        r = ResumeVersionResponse(
            id="01ARZ3NDEKTSV4RRFFQ69G5FAV", filename="resume.pdf",
            format="pdf", version_label="v1", is_default=True,
            parsed_text_preview="John Doe...", created_at="2026-03-13T00:00:00"
        )
        assert r.format == "pdf"


class TestAutoApplyRunRequest:
    def test_default_submit_false(self):
        r = AutoApplyRunRequest(job_id="abc123")
        assert r.submit is False

    def test_submit_explicit_true(self):
        r = AutoApplyRunRequest(job_id="abc123", submit=True)
        assert r.submit is True


class TestCopilotRequestTailorResume:
    def test_tailor_resume_tool_accepted(self):
        r = CopilotRequest(tool="tailorResume", job_id="abc123")
        assert r.tool == "tailorResume"
