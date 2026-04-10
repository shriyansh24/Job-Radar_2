"""Unit tests for CopilotService."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.models import CoverLetter
from app.copilot.service import CopilotService
from app.resume.models import ResumeVersion

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_resume(
    db: AsyncSession, user_id: uuid.UUID, *, text: str = "Alice Smith"
) -> ResumeVersion:
    rv = ResumeVersion(user_id=user_id, parsed_text=text)
    db.add(rv)
    await db.commit()
    await db.refresh(rv)
    return rv


# ---------------------------------------------------------------------------
# generate_cover_letter
# ---------------------------------------------------------------------------


class TestGenerateCoverLetter:
    @pytest.mark.asyncio
    async def test_no_api_key_stores_placeholder_content(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        await _make_resume(db_session, user_id, text="Some resume text")
        svc = CopilotService(db_session)

        with patch("app.copilot.service.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""
            result = await svc.generate_cover_letter("job-123", "professional", user_id)

        assert isinstance(result, CoverLetter)
        assert "OpenRouter API key" in result.content
        assert result.user_id == user_id
        assert result.style == "professional"

    @pytest.mark.asyncio
    async def test_no_resume_stores_upload_prompt(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        # No resume in DB for this user
        svc = CopilotService(db_session)

        with patch("app.copilot.service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-test"
            result = await svc.generate_cover_letter("job-xyz", "concise", user_id)

        assert "Please upload a resume" in result.content

    @pytest.mark.asyncio
    async def test_successful_llm_generation_stores_content(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        await _make_resume(db_session, user_id, text="My full resume text")
        svc = CopilotService(db_session)

        mock_cl_result = MagicMock()
        mock_cl_result.content = "Dear Hiring Manager, I am a great fit..."

        with (
            patch("app.copilot.service.settings") as mock_settings,
            patch(
                "app.copilot.service._generate_cover_letter",
                new=AsyncMock(return_value=mock_cl_result),
            ),
        ):
            mock_settings.openrouter_api_key = "sk-test"
            result = await svc.generate_cover_letter("job-001", "professional", user_id)

        assert result.content == "Dear Hiring Manager, I am a great fit..."
        assert result.job_id == "job-001"

    @pytest.mark.asyncio
    async def test_llm_error_stores_error_placeholder(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        await _make_resume(db_session, user_id, text="My resume text")
        svc = CopilotService(db_session)

        with (
            patch("app.copilot.service.settings") as mock_settings,
            patch(
                "app.copilot.service._generate_cover_letter",
                side_effect=Exception("API timeout"),
            ),
        ):
            mock_settings.openrouter_api_key = "sk-test"
            result = await svc.generate_cover_letter("job-002", "concise", user_id)

        assert "error" in result.content.lower()

    @pytest.mark.asyncio
    async def test_cover_letter_persisted_in_db(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        svc = CopilotService(db_session)

        with patch("app.copilot.service.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""
            result = await svc.generate_cover_letter("job-persist", "formal", user_id)

        # Verify we can retrieve it via a vault-style query
        assert result.id is not None
        fetched_letters = await svc.db.scalars(
            __import__("sqlalchemy").select(CoverLetter).where(CoverLetter.user_id == user_id)
        )
        letters = list(fetched_letters.all())
        assert len(letters) == 1
        assert letters[0].id == result.id


# ---------------------------------------------------------------------------
# chat (streaming)
# ---------------------------------------------------------------------------


class TestCopilotChat:
    @pytest.mark.asyncio
    async def test_yields_placeholder_when_llm_not_configured(self, db_session: AsyncSession):
        svc = CopilotService(db_session)

        with patch("app.copilot.service._build_llm_client", return_value=MagicMock(
            is_configured=False, close=AsyncMock()
        )):
            chunks = []
            async for chunk in svc.chat("Hello?", context=None, user_id=uuid.uuid4()):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert "not configured" in chunks[0].lower()

    @pytest.mark.asyncio
    async def test_streams_llm_chunks(self, db_session: AsyncSession):
        svc = CopilotService(db_session)

        async def _mock_stream(*args, **kwargs):
            for word in ["Hello", " ", "world"]:
                yield word

        mock_llm = MagicMock()
        mock_llm.is_configured = True
        mock_llm.chat_stream = _mock_stream
        mock_llm.close = AsyncMock()

        with patch("app.copilot.service._build_llm_client", return_value=mock_llm):
            chunks = []
            async for chunk in svc.chat("Hi", context=None, user_id=uuid.uuid4()):
                chunks.append(chunk)

        assert "".join(chunks) == "Hello world"

    @pytest.mark.asyncio
    async def test_error_in_stream_yields_error_message(self, db_session: AsyncSession):
        svc = CopilotService(db_session)

        async def _mock_stream_error(*args, **kwargs):
            raise RuntimeError("LLM failed")
            yield  # make it a generator

        mock_llm = MagicMock()
        mock_llm.is_configured = True
        mock_llm.chat_stream = _mock_stream_error
        mock_llm.close = AsyncMock()

        with patch("app.copilot.service._build_llm_client", return_value=mock_llm):
            chunks = []
            async for chunk in svc.chat("Hi", context=None, user_id=uuid.uuid4()):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert "error" in chunks[0].lower()
