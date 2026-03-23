"""Tests for Multi-Resume Archetype Strategy (B5)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.resume.archetypes import (
    ArchetypeCreate,
    ArchetypeService,
    _score_archetype,
    _tokenize,
)
from app.resume.models import ResumeVersion
from app.shared.errors import NotFoundError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_resume(db: AsyncSession, user_id: uuid.UUID) -> ResumeVersion:
    rv = ResumeVersion(
        user_id=user_id,
        label="Test Resume",
        filename="test.txt",
        parsed_text="Python developer with 5 years of experience in machine learning.",
        parsed_structured={"skills": ["python", "machine learning", "tensorflow"]},
    )
    db.add(rv)
    return rv


def _make_job(db: AsyncSession, user_id: uuid.UUID, job_id: str = "abc123") -> Job:
    job = Job(
        id=job_id,
        user_id=user_id,
        source="test",
        title="Senior ML Engineer",
        company_name="TestCorp",
        description_clean="Looking for an ML engineer with Python and TensorFlow experience.",
        skills_required=["python", "tensorflow", "kubernetes"],
    )
    db.add(job)
    return job


# ---------------------------------------------------------------------------
# Unit tests for scoring helpers
# ---------------------------------------------------------------------------


class TestTokenize:
    def test_basic(self) -> None:
        tokens = _tokenize("Hello World python")
        assert "hello" in tokens
        assert "world" in tokens
        assert "python" in tokens

    def test_strips_punctuation(self) -> None:
        tokens = _tokenize("python, tensorflow; kubernetes!")
        assert "python" in tokens
        assert "tensorflow" in tokens
        assert "kubernetes" in tokens

    def test_short_words_excluded(self) -> None:
        tokens = _tokenize("a be or not to Python")
        assert "python" in tokens
        assert "or" not in tokens
        assert "be" not in tokens


class TestScoreArchetype:
    def _make_arch(self, **kwargs: object) -> object:
        """Build a lightweight stand-in with the same attributes _score_archetype reads."""
        from types import SimpleNamespace

        defaults = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "name": "Test",
            "keyword_priorities": ["python", "tensorflow"],
            "emphasis_sections": ["machine learning"],
            "target_role_type": "ML Engineer",
            "base_ir_json": {"text": "Python ML engineer"},
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_scores_with_overlap(self) -> None:
        arch = self._make_arch()
        job_tokens = _tokenize("Looking for ML Engineer with Python and TensorFlow")
        score, reason = _score_archetype(arch, job_tokens)
        assert score > 0
        assert isinstance(reason, str)

    def test_zero_score_no_overlap(self) -> None:
        arch = self._make_arch(
            keyword_priorities=["cobol"],
            emphasis_sections=["mainframe"],
            target_role_type="COBOL Developer",
            base_ir_json={"text": "COBOL developer"},
        )
        job_tokens = _tokenize("Rust systems programmer embedded firmware")
        score, _ = _score_archetype(arch, job_tokens)
        # Very little overlap expected
        assert score < 0.5

    def test_empty_tokens_returns_zero(self) -> None:
        arch = self._make_arch(
            keyword_priorities=[],
            emphasis_sections=[],
            target_role_type=None,
            base_ir_json={},
        )
        score, reason = _score_archetype(arch, set())
        assert score == 0.0
        assert "Insufficient" in reason


# ---------------------------------------------------------------------------
# Integration tests using DB session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_archetype(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    resume = _make_resume(db_session, user_id)
    await db_session.flush()

    svc = ArchetypeService(db_session)
    arch = await svc.create_archetype(
        user_id,
        ArchetypeCreate(
            name="ML Research",
            base_resume_id=resume.id,
            target_role="Machine Learning Researcher",
            keyword_priorities=["pytorch", "transformers"],
        ),
    )
    assert arch.name == "ML Research"
    assert arch.target_role_type == "Machine Learning Researcher"
    assert arch.base_ir_json is not None
    assert "text" in arch.base_ir_json
    assert arch.keyword_priorities == ["pytorch", "transformers"]


@pytest.mark.asyncio
async def test_list_archetypes(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    resume = _make_resume(db_session, user_id)
    await db_session.flush()

    svc = ArchetypeService(db_session)
    await svc.create_archetype(
        user_id,
        ArchetypeCreate(name="A1", base_resume_id=resume.id),
    )
    await svc.create_archetype(
        user_id,
        ArchetypeCreate(name="A2", base_resume_id=resume.id),
    )

    items = await svc.list_archetypes(user_id)
    assert len(items) == 2
    names = {a.name for a in items}
    assert names == {"A1", "A2"}


@pytest.mark.asyncio
async def test_get_archetype(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    resume = _make_resume(db_session, user_id)
    await db_session.flush()

    svc = ArchetypeService(db_session)
    created = await svc.create_archetype(
        user_id,
        ArchetypeCreate(name="Test", base_resume_id=resume.id),
    )
    fetched = await svc.get_archetype(created.id, user_id)
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_archetype_wrong_user(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    resume = _make_resume(db_session, user_id)
    await db_session.flush()

    svc = ArchetypeService(db_session)
    created = await svc.create_archetype(
        user_id,
        ArchetypeCreate(name="Test", base_resume_id=resume.id),
    )
    with pytest.raises(NotFoundError):
        await svc.get_archetype(created.id, other_user_id)


@pytest.mark.asyncio
async def test_delete_archetype(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    resume = _make_resume(db_session, user_id)
    await db_session.flush()

    svc = ArchetypeService(db_session)
    arch = await svc.create_archetype(
        user_id,
        ArchetypeCreate(name="ToDelete", base_resume_id=resume.id),
    )
    await svc.delete_archetype(user_id, arch.id)

    items = await svc.list_archetypes(user_id)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_delete_archetype_not_found(db_session: AsyncSession) -> None:
    svc = ArchetypeService(db_session)
    with pytest.raises(NotFoundError):
        await svc.delete_archetype(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_create_archetype_bad_resume(db_session: AsyncSession) -> None:
    svc = ArchetypeService(db_session)
    with pytest.raises(NotFoundError):
        await svc.create_archetype(
            uuid.uuid4(),
            ArchetypeCreate(name="Bad", base_resume_id=uuid.uuid4()),
        )


@pytest.mark.asyncio
async def test_select_best_archetype(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    resume = _make_resume(db_session, user_id)
    job = _make_job(db_session, user_id)
    await db_session.flush()

    svc = ArchetypeService(db_session)
    # Create two archetypes — one matching, one not
    await svc.create_archetype(
        user_id,
        ArchetypeCreate(
            name="COBOL Dev",
            base_resume_id=resume.id,
            target_role="COBOL Developer",
            keyword_priorities=["cobol", "mainframe"],
        ),
    )
    await svc.create_archetype(
        user_id,
        ArchetypeCreate(
            name="ML Engineer",
            base_resume_id=resume.id,
            target_role="ML Engineer",
            keyword_priorities=["python", "tensorflow", "kubernetes"],
        ),
    )

    best, score, reason = await svc.select_best_archetype(user_id, job.id)
    assert best.name == "ML Engineer"
    assert score > 0
    assert isinstance(reason, str)


@pytest.mark.asyncio
async def test_select_best_archetype_no_archetypes(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    job = _make_job(db_session, user_id)
    await db_session.flush()

    svc = ArchetypeService(db_session)
    with pytest.raises(NotFoundError, match="No archetypes"):
        await svc.select_best_archetype(user_id, job.id)


@pytest.mark.asyncio
async def test_select_best_archetype_bad_job(db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    svc = ArchetypeService(db_session)
    # No archetypes exist but job also doesn't exist — should raise for job first
    with pytest.raises(NotFoundError):
        await svc.select_best_archetype(user_id, "nonexistent")
