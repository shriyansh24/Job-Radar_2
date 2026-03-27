from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.resume.ir_schema import ContactInfo, ResumeIR
from app.resume.service import ResumeService


@pytest.mark.asyncio
async def test_upload_resume_parses_supported_file() -> None:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    user_id = uuid.uuid4()
    parsed = ResumeIR(
        contact=ContactInfo(name="Jane Doe", email="jane@example.com"),
        raw_text="Jane Doe\njane@example.com\nEngineer",
    )

    with patch("app.resume.service.ResumeParser") as parser_cls:
        parser = parser_cls.return_value
        parser.parse = AsyncMock(return_value=parsed)
        service = ResumeService(db, llm_client=MagicMock())
        version = await service.upload_resume("resume.txt", b"ignored", user_id)

    parser.parse.assert_awaited_once_with(b"ignored", "resume.txt")
    added = db.add.call_args.args[0]
    assert version is added
    assert added.parsed_text == parsed.raw_text
    assert added.parsed_structured is not None
    assert added.parsed_structured["contact"]["name"] == "Jane Doe"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(added)


@pytest.mark.asyncio
async def test_upload_resume_falls_back_for_unsupported_format() -> None:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    user_id = uuid.uuid4()

    with patch("app.resume.service.ResumeParser") as parser_cls:
        parser = parser_cls.return_value
        parser.parse = AsyncMock(
            side_effect=ValueError("Unsupported resume format '.jpg'")
        )
        service = ResumeService(db, llm_client=MagicMock())
        version = await service.upload_resume("resume.jpg", b"raw-bytes", user_id)

    added = db.add.call_args.args[0]
    assert version is added
    assert added.parsed_text == "raw-bytes"
    assert added.parsed_structured is None
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(added)
