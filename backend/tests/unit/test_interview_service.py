from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.interview.schemas import GenerateQuestionsRequest
from app.interview.service import InterviewService
from app.shared.errors import AppError


@pytest.mark.asyncio
async def test_generate_questions_surfaces_llm_failure():
    router = MagicMock()
    router.complete_json = AsyncMock(side_effect=RuntimeError("llm unavailable"))
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    with patch("app.interview.service._build_router", return_value=router):
        service = InterviewService(db)

    service._load_job_context = AsyncMock(return_value=("Engineer", "Acme", "desc"))

    with pytest.raises(AppError) as exc_info:
        await service.generate_questions(
            GenerateQuestionsRequest(job_id="job-123", count=3, types=["behavioral"]),
            user_id=uuid.uuid4(),
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Question generation failed"
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
