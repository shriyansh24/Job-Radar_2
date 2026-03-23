"""Tests for the 4-stage tailoring engine (B2)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.resume.models import ResumeVersion, TailoringSession
from app.resume.tailoring import TailoringEngine


def _make_ir() -> dict:
    return {
        "contact": {"name": "Jane Doe", "email": "jane@example.com", "phone": "555-1234"},
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
            }
        ],
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    }


def _make_job_mock() -> MagicMock:
    job = MagicMock()
    job.id = "abc123deadbeef"
    job.title = "Senior Backend Engineer"
    job.description_clean = "We are looking for a Python engineer with experience in FastAPI."
    return job


@pytest.fixture
def mock_llm() -> AsyncMock:
    llm = AsyncMock()
    # Default: return sequential stage results
    llm.chat_json = AsyncMock(
        side_effect=[
            # Stage 1
            {
                "must_haves": ["Python", "FastAPI"],
                "nice_to_haves": ["Docker"],
                "keywords": ["backend", "microservices"],
                "technologies": ["Python", "FastAPI"],
                "seniority_level": "senior",
                "culture_signals": [],
            },
            # Stage 2
            {
                "matched": ["Python", "FastAPI"],
                "partial": [],
                "missing": ["Kubernetes"],
                "keyword_coverage": {"present": ["Python"], "missing": ["Kubernetes"]},
                "strongest_sections": ["work"],
                "weakest_sections": ["skills"],
            },
            # Stage 3
            {
                "proposals": [
                    {
                        "id": 0,
                        "type": "add_skill",
                        "section": "skills",
                        "original": None,
                        "proposed": "Kubernetes",
                        "reason": "JD lists Kubernetes as nice-to-have",
                        "confidence": 0.7,
                        "source": "jd_keyword",
                    },
                    {
                        "id": 1,
                        "type": "rewrite_bullet",
                        "section": "work[0].bullets[0]",
                        "original": "Led team of 5 engineers building microservices",
                        "proposed": "Led team of 5 engineers building Python microservices "
                        "with FastAPI, serving 10K+ requests/sec",
                        "reason": "Inject target keywords and add metrics",
                        "confidence": 0.85,
                        "source": "resume_existing",
                    },
                ]
            },
        ]
    )
    return llm


class TestTailoringEngine:

    @pytest.mark.asyncio
    async def test_start_creates_session_with_proposals(
        self, db_session, mock_llm
    ):
        """start() runs stages 1-3 and stores proposals in a session."""
        # Create a resume version
        resume_id = uuid.uuid4()
        user_id = uuid.uuid4()
        version = ResumeVersion(
            id=resume_id,
            user_id=user_id,
            filename="test.pdf",
            ir_json=_make_ir(),
            is_default=True,
        )
        db_session.add(version)
        await db_session.commit()

        # Mock job lookup
        job_mock = _make_job_mock()
        with patch.object(TailoringEngine, "_get_job", return_value=job_mock):
            engine = TailoringEngine(db_session, mock_llm)
            session = await engine.start(resume_id, "abc123", user_id)

        assert session.status == "proposals_ready"
        assert session.proposals is not None
        assert len(session.proposals) == 2
        assert session.stage1_result is not None
        assert session.stage2_result is not None
        assert session.id is not None

    @pytest.mark.asyncio
    async def test_approve_all_creates_tailored_version(
        self, db_session, mock_llm
    ):
        """approve() with all True applies changes and creates a new version."""
        resume_id = uuid.uuid4()
        user_id = uuid.uuid4()
        version = ResumeVersion(
            id=resume_id,
            user_id=user_id,
            filename="test.pdf",
            ir_json=_make_ir(),
            is_default=True,
        )
        db_session.add(version)

        session_id = uuid.uuid4()
        session = TailoringSession(
            id=session_id,
            resume_version_id=resume_id,
            job_id="abc123deadbeef",
            user_id=user_id,
            status="proposals_ready",
            stage1_result={"must_haves": ["Python"]},
            stage2_result={"matched": ["Python"]},
            proposals=[
                {
                    "id": 0,
                    "type": "add_skill",
                    "section": "skills",
                    "original": None,
                    "proposed": "Kubernetes",
                    "reason": "JD keyword",
                    "confidence": 0.7,
                    "source": "jd_keyword",
                },
            ],
        )
        db_session.add(session)
        await db_session.commit()

        # Mock LLM for stage 4 apply
        tailored_ir = _make_ir()
        tailored_ir["skills"].append("Kubernetes")
        mock_llm.chat_json = AsyncMock(return_value=tailored_ir)

        engine = TailoringEngine(db_session, mock_llm)
        result = await engine.approve(session_id, [True], user_id)

        assert result.status == "approved"
        assert result.tailored_ir is not None
        assert result.tailored_version_id is not None
        assert "Kubernetes" in result.tailored_ir.get("skills", [])

    @pytest.mark.asyncio
    async def test_approve_none_keeps_original(self, db_session, mock_llm):
        """approve() with all False keeps the original IR unchanged."""
        resume_id = uuid.uuid4()
        user_id = uuid.uuid4()
        original_ir = _make_ir()
        version = ResumeVersion(
            id=resume_id,
            user_id=user_id,
            filename="test.pdf",
            ir_json=original_ir,
            is_default=True,
        )
        db_session.add(version)

        session_id = uuid.uuid4()
        session = TailoringSession(
            id=session_id,
            resume_version_id=resume_id,
            job_id="abc123deadbeef",
            user_id=user_id,
            status="proposals_ready",
            proposals=[
                {
                    "id": 0,
                    "type": "add_skill",
                    "section": "skills",
                    "original": None,
                    "proposed": "Kubernetes",
                    "reason": "test",
                    "confidence": 0.7,
                    "source": "jd_keyword",
                },
            ],
        )
        db_session.add(session)
        await db_session.commit()

        engine = TailoringEngine(db_session, mock_llm)
        result = await engine.approve(session_id, [False], user_id)

        assert result.status == "approved"
        # Should keep the original IR since no proposals approved
        assert result.tailored_ir == original_ir
        # LLM should NOT have been called for stage 4
        mock_llm.chat_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_approve_rejects_wrong_length(self, db_session, mock_llm):
        """approve() raises ValidationError if approvals length mismatches proposals."""
        resume_id = uuid.uuid4()
        user_id = uuid.uuid4()
        version = ResumeVersion(
            id=resume_id,
            user_id=user_id,
            filename="test.pdf",
            ir_json=_make_ir(),
            is_default=True,
        )
        db_session.add(version)

        session_id = uuid.uuid4()
        session = TailoringSession(
            id=session_id,
            resume_version_id=resume_id,
            job_id="abc123",
            user_id=user_id,
            status="proposals_ready",
            proposals=[{"id": 0}, {"id": 1}],
        )
        db_session.add(session)
        await db_session.commit()

        engine = TailoringEngine(db_session, mock_llm)
        with pytest.raises(Exception, match="Approvals length"):
            await engine.approve(session_id, [True], user_id)

    @pytest.mark.asyncio
    async def test_approve_rejects_wrong_status(self, db_session, mock_llm):
        """approve() raises ValidationError if session is not proposals_ready."""
        resume_id = uuid.uuid4()
        user_id = uuid.uuid4()
        version = ResumeVersion(
            id=resume_id,
            user_id=user_id,
            filename="test.pdf",
            ir_json=_make_ir(),
            is_default=True,
        )
        db_session.add(version)

        session_id = uuid.uuid4()
        session = TailoringSession(
            id=session_id,
            resume_version_id=resume_id,
            job_id="abc123",
            user_id=user_id,
            status="approved",  # Already approved
            proposals=[],
        )
        db_session.add(session)
        await db_session.commit()

        engine = TailoringEngine(db_session, mock_llm)
        with pytest.raises(Exception, match="proposals_ready"):
            await engine.approve(session_id, [], user_id)


class TestIRToText:
    def test_converts_ir_to_text(self):
        ir = _make_ir()
        text = TailoringEngine._ir_to_text(ir)
        assert "Jane Doe" in text
        assert "Acme Corp" in text
        assert "Python" in text
        assert "Led team" in text

    def test_handles_empty_ir(self):
        text = TailoringEngine._ir_to_text({})
        assert text == ""
