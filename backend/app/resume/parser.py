"""Multi-format resume parser producing an IR schema.

Supports PDF, DOCX, LaTeX (.tex), and plain-text (.txt) inputs.
Text extraction is synchronous; LLM structuring is async.
"""

from __future__ import annotations

import io
from pathlib import PurePosixPath

import structlog

from app.enrichment.llm_client import LLMClient
from app.resume.ir_schema import ResumeIR

logger = structlog.get_logger()

# Prompt sent to the LLM to convert raw resume text into structured JSON.
_STRUCTURING_SYSTEM_PROMPT = "You are a resume-parsing assistant. Return ONLY valid JSON."

_STRUCTURING_USER_PROMPT = """\
Parse the following resume text into a structured JSON object with these fields:
- contact: {{name (required), email, phone, location, linkedin, github, website}}
- summary: a brief professional summary if present
- work: list of {{company, title, start_date, end_date, location, description, bullets, \
tech_stack, metrics}}
- education: list of {{institution, degree, field, start_date, end_date, gpa, highlights}}
- skills: flat list of skill strings
- skill_categories: dict mapping category names to skill lists
- projects: list of {{name, description, tech_stack, url, bullets}}
- certifications: list of strings
- publications: list of strings
- languages: list of strings

If a field is missing from the resume, use null or an empty list/object as appropriate.
Dates should be strings like "Jan 2022" or "2022".

Resume text:
---
{resume_text}
---
"""

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".tex", ".txt"}


class ResumeParser:
    """Extracts text from various resume formats and structures it via LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client

    async def parse(self, file_bytes: bytes, filename: str) -> ResumeIR:
        """Parse a resume file into the IR schema.

        Args:
            file_bytes: Raw file contents.
            filename: Original filename (used to detect format).

        Returns:
            A validated ``ResumeIR`` instance.
        """
        ext = self._detect_format(filename)
        logger.info("resume_parser.parse", filename=filename, format=ext)

        raw_text = self._extract_text(file_bytes, ext)
        if not raw_text.strip():
            logger.warning("resume_parser.empty_text", filename=filename)
            return ResumeIR(
                contact={"name": "Unknown"},  # type: ignore[arg-type]
                raw_text="",
                parse_warnings=["No text could be extracted from the file."],
            )

        ir = await self._structure_with_llm(raw_text)
        ir.raw_text = raw_text
        return ir

    # ------------------------------------------------------------------
    # Format detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_format(filename: str) -> str:
        """Return the lowercase extension (e.g. '.pdf') for *filename*."""
        ext = PurePosixPath(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported resume format '{ext}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        return ext

    # ------------------------------------------------------------------
    # Text extraction per format
    # ------------------------------------------------------------------

    def _extract_text(self, data: bytes, ext: str) -> str:
        if ext == ".pdf":
            return self._parse_pdf(data)
        if ext == ".docx":
            return self._parse_docx(data)
        if ext == ".tex":
            return self._parse_latex(data)
        # .txt fallback
        return data.decode(errors="replace")

    @staticmethod
    def _parse_pdf(data: bytes) -> str:
        """Extract markdown-formatted text from a PDF using pymupdf4llm."""
        import pymupdf4llm
        return pymupdf4llm.to_markdown(data)  # type: ignore[arg-type]

    @staticmethod
    def _parse_docx(data: bytes) -> str:
        """Extract text from a DOCX file using python-docx."""
        import docx
        doc = docx.Document(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    @staticmethod
    def _parse_latex(data: bytes) -> str:
        """Strip LaTeX markup and return plain text."""
        from pylatexenc.latex2text import LatexNodes2Text
        raw = data.decode(errors="replace")
        return LatexNodes2Text().latex_to_text(raw)

    # ------------------------------------------------------------------
    # LLM structuring
    # ------------------------------------------------------------------

    async def _structure_with_llm(self, raw_text: str) -> ResumeIR:
        """Send raw resume text to the LLM and parse the response into ResumeIR."""
        truncated = raw_text[:8000]  # keep within reasonable token limits

        result = await self._llm.chat_json(
            messages=[
                {"role": "system", "content": _STRUCTURING_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _STRUCTURING_USER_PROMPT.format(resume_text=truncated),
                },
            ],
            temperature=0.1,
            max_tokens=3000,
        )

        if not result:
            logger.warning("resume_parser.llm_empty_response")
            return ResumeIR(
                contact={"name": "Unknown"},  # type: ignore[arg-type]
                raw_text=raw_text,
                parse_warnings=["LLM returned an empty response."],
            )

        return self._dict_to_ir(result, raw_text)

    @staticmethod
    def _dict_to_ir(data: dict, raw_text: str) -> ResumeIR:
        """Best-effort conversion of an LLM JSON dict into a ResumeIR."""
        warnings: list[str] = []

        # Ensure contact has at least a name
        contact = data.get("contact") or {}
        if not isinstance(contact, dict):
            contact = {}
        if "name" not in contact or not contact["name"]:
            contact["name"] = "Unknown"
            warnings.append("Could not extract contact name from resume.")

        try:
            ir = ResumeIR(
                contact=contact,  # type: ignore[arg-type]
                summary=data.get("summary"),
                work=data.get("work") or [],
                education=data.get("education") or [],
                skills=data.get("skills") or [],
                skill_categories=data.get("skill_categories") or {},
                projects=data.get("projects") or [],
                certifications=data.get("certifications") or [],
                publications=data.get("publications") or [],
                languages=data.get("languages") or [],
                raw_text=raw_text,
                parse_warnings=warnings,
            )
        except Exception as exc:
            logger.warning("resume_parser.ir_validation_failed", error=str(exc))
            ir = ResumeIR(
                contact={"name": contact.get("name", "Unknown")},  # type: ignore[arg-type]
                raw_text=raw_text,
                parse_warnings=[f"IR validation error: {exc}"],
            )
        return ir
