"""Tests for the PersonalRAG pipeline with mock DB, embedder, and LLM."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.analytics.rag import PersonalRAG

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_row(mapping: dict[str, Any]) -> Any:
    """Create a fake SA row with ._mapping attribute."""
    row = MagicMock()
    row._mapping = mapping
    return row


def _fake_result(rows: Sequence[dict[str, Any]]) -> Any:
    """Build a mock result that iterates over fake rows."""
    result = MagicMock()
    result.__iter__ = lambda self: iter([_make_row(r) for r in rows])
    return result


FAKE_EMBEDDING = [0.1] * 384
USER_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetContexts:
    @pytest.mark.asyncio
    async def test_returns_job_and_resume_contexts(self) -> None:
        job_rows = [
            {
                "title": "Backend Engineer",
                "company_name": "Acme Corp",
                "summary_ai": "Python role",
                "status": "interviewing",
                "salary_offered": None,
                "notes": "Good fit",
                "similarity": 0.92,
            },
        ]
        resume_rows = [
            {
                "label": "Main Resume",
                "filename": "resume.pdf",
                "parsed_text": "5 years Python experience...",
            },
        ]

        db = AsyncMock()
        # First call -> jobs, second call -> resumes
        db.execute = AsyncMock(
            side_effect=[_fake_result(job_rows), _fake_result(resume_rows)]
        )

        embedder = MagicMock()
        llm = AsyncMock()

        rag = PersonalRAG(db=db, embedder=embedder, llm=llm)
        contexts = await rag.get_contexts(FAKE_EMBEDDING, USER_ID)

        assert len(contexts) == 2
        assert "Backend Engineer" in contexts[0]
        assert "Acme Corp" in contexts[0]
        assert "interviewing" in contexts[0]
        assert "Main Resume" in contexts[1]

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_data(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[_fake_result([]), _fake_result([])]
        )

        rag = PersonalRAG(db=db, embedder=MagicMock(), llm=AsyncMock())
        contexts = await rag.get_contexts(FAKE_EMBEDDING, USER_ID)

        assert contexts == []

    @pytest.mark.asyncio
    async def test_handles_db_error_gracefully(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("connection lost"))

        rag = PersonalRAG(db=db, embedder=MagicMock(), llm=AsyncMock())
        contexts = await rag.get_contexts(FAKE_EMBEDDING, USER_ID)

        # Should not raise, returns empty
        assert contexts == []

    @pytest.mark.asyncio
    async def test_salary_offered_included(self) -> None:
        job_rows = [
            {
                "title": "SRE",
                "company_name": "BigCo",
                "summary_ai": None,
                "status": "offer",
                "salary_offered": 150000,
                "notes": None,
                "similarity": 0.88,
            },
        ]
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[_fake_result(job_rows), _fake_result([])]
        )

        rag = PersonalRAG(db=db, embedder=MagicMock(), llm=AsyncMock())
        contexts = await rag.get_contexts(FAKE_EMBEDDING, USER_ID)

        assert "$150,000" in contexts[0]


class TestQuery:
    @pytest.mark.asyncio
    async def test_full_rag_flow(self) -> None:
        job_rows = [
            {
                "title": "Data Engineer",
                "company_name": "DataCo",
                "summary_ai": "ETL pipelines",
                "status": "rejected",
                "salary_offered": None,
                "notes": "No Spark experience",
                "similarity": 0.85,
            },
        ]

        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[_fake_result(job_rows), _fake_result([])]
        )

        embedder = MagicMock()
        embedder.embed_text = MagicMock(return_value=FAKE_EMBEDDING)

        llm = AsyncMock()
        llm.chat = AsyncMock(return_value="You should learn Spark.")

        rag = PersonalRAG(db=db, embedder=embedder, llm=llm)
        answer = await rag.query("Why did DataCo reject me?", USER_ID)

        assert answer == "You should learn Spark."
        embedder.embed_text.assert_called_once_with("Why did DataCo reject me?")
        llm.chat.assert_called_once()

        # Verify prompt contains the context
        call_kwargs = llm.chat.call_args
        messages = (
            call_kwargs.kwargs.get("messages")
            or call_kwargs[1].get("messages")
            or call_kwargs[0][0]
        )
        user_msg = [m for m in messages if m["role"] == "user"][0]
        assert "Data Engineer" in user_msg["content"]
        assert "DataCo" in user_msg["content"]

    @pytest.mark.asyncio
    async def test_returns_fallback_when_embedder_unavailable(self) -> None:
        embedder = MagicMock()
        embedder.embed_text = MagicMock(return_value=None)

        rag = PersonalRAG(db=AsyncMock(), embedder=embedder, llm=AsyncMock())
        answer = await rag.query("anything", USER_ID)

        assert "not available" in answer.lower()

    @pytest.mark.asyncio
    async def test_returns_fallback_when_no_contexts(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[_fake_result([]), _fake_result([])]
        )

        embedder = MagicMock()
        embedder.embed_text = MagicMock(return_value=FAKE_EMBEDDING)

        rag = PersonalRAG(db=db, embedder=embedder, llm=AsyncMock())
        answer = await rag.query("why no interviews?", USER_ID)

        assert "enough data" in answer.lower()

    @pytest.mark.asyncio
    async def test_handles_llm_error(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _fake_result([{
                    "title": "Eng",
                    "company_name": "Co",
                    "summary_ai": None,
                    "status": "applied",
                    "salary_offered": None,
                    "notes": None,
                    "similarity": 0.9,
                }]),
                _fake_result([]),
            ]
        )

        embedder = MagicMock()
        embedder.embed_text = MagicMock(return_value=FAKE_EMBEDDING)

        llm = AsyncMock()
        llm.chat = AsyncMock(side_effect=RuntimeError("LLM down"))

        rag = PersonalRAG(db=db, embedder=embedder, llm=llm)
        answer = await rag.query("test?", USER_ID)

        assert "error" in answer.lower()
