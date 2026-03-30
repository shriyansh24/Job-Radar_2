from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.resume.ir_schema import ContactInfo, Education, ResumeIR, WorkExperience
from app.resume.parser import ResumeParser


class TestResumeIRSchema:
    def test_valid_minimal(self) -> None:
        ir = ResumeIR(contact=ContactInfo(name="Jane Doe"))
        assert ir.contact.name == "Jane Doe"
        assert ir.work == []
        assert ir.skills == []
        assert ir.raw_text == ""

    def test_valid_full(self) -> None:
        ir = ResumeIR(
            contact=ContactInfo(
                name="Jane Doe",
                email="jane@example.com",
                phone="555-1234",
                location="New York, NY",
                linkedin="https://linkedin.com/in/janedoe",
            ),
            summary="Senior engineer with 10 years experience.",
            work=[
                WorkExperience(
                    company="Acme Corp",
                    title="Staff Engineer",
                    start_date="Jan 2020",
                    end_date="Present",
                    bullets=["Led platform migration", "Reduced latency by 40%"],
                    tech_stack=["Python", "PostgreSQL"],
                    metrics=["40% latency reduction"],
                )
            ],
            education=[
                Education(
                    institution="MIT",
                    degree="BS",
                    field="Computer Science",
                    end_date="2015",
                )
            ],
            skills=["Python", "Rust", "SQL"],
            skill_categories={"Languages": ["Python", "Rust"], "Databases": ["SQL"]},
            certifications=["AWS Solutions Architect"],
            languages=["English", "Spanish"],
        )
        assert len(ir.work) == 1
        assert ir.work[0].company == "Acme Corp"
        assert ir.education[0].institution == "MIT"
        assert "Python" in ir.skills

    def test_missing_contact_name_fails(self) -> None:
        with pytest.raises(Exception):
            ContactInfo()  # type: ignore[call-arg]

    def test_contact_name_required_in_ir(self) -> None:
        with pytest.raises(Exception):
            ResumeIR(contact=ContactInfo())  # type: ignore[call-arg]

    def test_json_roundtrip(self) -> None:
        ir = ResumeIR(
            contact=ContactInfo(name="Test User"),
            skills=["Python"],
            work=[WorkExperience(company="Co", title="Dev")],
        )
        restored = ResumeIR(**ir.model_dump())
        assert restored.contact.name == "Test User"
        assert restored.skills == ["Python"]


class TestFormatDetection:
    def test_pdf(self) -> None:
        assert ResumeParser._detect_format("resume.pdf") == ".pdf"

    def test_docx(self) -> None:
        assert ResumeParser._detect_format("Resume_Final.docx") == ".docx"

    def test_tex(self) -> None:
        assert ResumeParser._detect_format("cv.tex") == ".tex"

    def test_txt(self) -> None:
        assert ResumeParser._detect_format("resume.txt") == ".txt"

    def test_case_insensitive(self) -> None:
        assert ResumeParser._detect_format("resume.PDF") == ".pdf"

    def test_unsupported_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported resume format"):
            ResumeParser._detect_format("resume.jpg")


class TestParserWithMockedLLM:
    @pytest.fixture()
    def mock_llm(self) -> AsyncMock:
        llm = AsyncMock()
        llm.chat_json = AsyncMock(
            return_value={
                "contact": {"name": "Jane Doe", "email": "jane@example.com"},
                "summary": "Experienced engineer.",
                "work": [
                    {
                        "company": "Acme",
                        "title": "Engineer",
                        "bullets": ["Built systems"],
                        "tech_stack": ["Python"],
                        "metrics": [],
                    }
                ],
                "education": [
                    {"institution": "State U", "degree": "BS", "field": "CS"}
                ],
                "skills": ["Python", "Go"],
                "skill_categories": {"Languages": ["Python", "Go"]},
                "projects": [],
                "certifications": [],
                "publications": [],
                "languages": ["English"],
            }
        )
        return llm

    @pytest.mark.asyncio
    async def test_parse_txt(self, mock_llm: AsyncMock) -> None:
        parser = ResumeParser(llm_client=mock_llm)
        ir = await parser.parse(
            b"Jane Doe\njane@example.com\nExperienced engineer.", "resume.txt"
        )
        assert ir.contact.name == "Jane Doe"
        assert ir.contact.email == "jane@example.com"
        assert len(ir.work) == 1
        assert ir.work[0].company == "Acme"
        assert "Python" in ir.skills
        assert "Jane Doe" in ir.raw_text

    @pytest.mark.asyncio
    async def test_parse_txt_empty(self, mock_llm: AsyncMock) -> None:
        parser = ResumeParser(llm_client=mock_llm)
        ir = await parser.parse(b"", "resume.txt")
        assert ir.contact.name == "Unknown"
        assert ir.parse_warnings

    @pytest.mark.asyncio
    async def test_llm_empty_response(self) -> None:
        llm = AsyncMock()
        llm.chat_json = AsyncMock(return_value={})
        parser = ResumeParser(llm_client=llm)
        ir = await parser.parse(b"Some resume text", "resume.txt")
        assert ir.contact.name == "Unknown"
        assert ir.parse_warnings

    @pytest.mark.asyncio
    async def test_parse_docx_calls_extract(self, mock_llm: AsyncMock) -> None:
        parser = ResumeParser(llm_client=mock_llm)
        with patch.object(
            parser, "_parse_docx", return_value="Jane Doe\nSoftware Engineer"
        ) as mock_docx:
            ir = await parser.parse(b"fake-docx-bytes", "resume.docx")
            mock_docx.assert_called_once_with(b"fake-docx-bytes")
            assert ir.contact.name == "Jane Doe"

    @pytest.mark.asyncio
    async def test_parse_pdf_calls_extract(self, mock_llm: AsyncMock) -> None:
        parser = ResumeParser(llm_client=mock_llm)
        with patch.object(
            parser, "_parse_pdf", return_value="Jane Doe\nSoftware Engineer"
        ) as mock_pdf:
            ir = await parser.parse(b"fake-pdf-bytes", "resume.pdf")
            mock_pdf.assert_called_once_with(b"fake-pdf-bytes")
            assert ir.contact.name == "Jane Doe"

    @pytest.mark.asyncio
    async def test_parse_latex_calls_extract(self, mock_llm: AsyncMock) -> None:
        parser = ResumeParser(llm_client=mock_llm)
        with patch.object(
            parser, "_parse_latex", return_value="Jane Doe\nSoftware Engineer"
        ) as mock_tex:
            ir = await parser.parse(b"fake-tex-bytes", "cv.tex")
            mock_tex.assert_called_once_with(b"fake-tex-bytes")
            assert ir.contact.name == "Jane Doe"

    @pytest.mark.asyncio
    async def test_unsupported_format_raises(self, mock_llm: AsyncMock) -> None:
        parser = ResumeParser(llm_client=mock_llm)
        with pytest.raises(ValueError, match="Unsupported"):
            await parser.parse(b"data", "resume.png")
