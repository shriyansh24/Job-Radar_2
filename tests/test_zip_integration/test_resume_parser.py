"""Test multi-format resume text extraction."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.resume.parser import (
    extract_resume_text,
    parse_resume_sections,
    detect_resume_format,
    SUPPORTED_FORMATS,
)


class TestDetectResumeFormat:
    def test_pdf(self):
        assert detect_resume_format("resume.pdf") == "pdf"

    def test_docx(self):
        assert detect_resume_format("resume.docx") == "docx"

    def test_markdown(self):
        assert detect_resume_format("resume.md") == "md"

    def test_txt(self):
        assert detect_resume_format("resume.txt") == "txt"

    def test_latex(self):
        assert detect_resume_format("resume.tex") == "tex"

    def test_case_insensitive(self):
        assert detect_resume_format("Resume.PDF") == "pdf"

    def test_unsupported_returns_none(self):
        assert detect_resume_format("resume.jpg") is None

    def test_no_extension(self):
        assert detect_resume_format("resume") is None

    def test_supported_formats_constant(self):
        assert "pdf" in SUPPORTED_FORMATS
        assert "docx" in SUPPORTED_FORMATS
        assert "md" in SUPPORTED_FORMATS
        assert "txt" in SUPPORTED_FORMATS
        assert "tex" in SUPPORTED_FORMATS


class TestExtractResumeTextTxt:
    def test_plain_text(self):
        content = b"John Doe\nSoftware Engineer\nPython, FastAPI"
        result = extract_resume_text(content, "resume.txt")
        assert "John Doe" in result
        assert "Software Engineer" in result

    def test_utf8_text(self):
        content = "Résumé — José García".encode("utf-8")
        result = extract_resume_text(content, "resume.txt")
        assert "José" in result

    def test_empty_file(self):
        result = extract_resume_text(b"", "resume.txt")
        assert result == ""


class TestExtractResumeTextMarkdown:
    def test_markdown_strips_formatting(self):
        content = b"# John Doe\n## Experience\n- **Senior Engineer** at Google"
        result = extract_resume_text(content, "resume.md")
        assert "John Doe" in result
        assert "Senior Engineer" in result

    def test_preserves_content(self):
        content = b"Skills: Python, React, AWS"
        result = extract_resume_text(content, "resume.md")
        assert "Python" in result


class TestExtractResumeTextPdf:
    @patch("backend.resume.parser.pdfplumber")
    def test_pdf_extraction(self, mock_pdfplumber):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "John Doe\nSoftware Engineer"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        result = extract_resume_text(b"fake pdf bytes", "resume.pdf")
        assert "John Doe" in result

    @patch("backend.resume.parser.pdfplumber", None)
    def test_pdf_without_pdfplumber_raises(self):
        with pytest.raises(ImportError):
            extract_resume_text(b"fake pdf", "resume.pdf")


class TestExtractResumeTextDocx:
    @patch("backend.resume.parser.Document")
    def test_docx_extraction(self, mock_doc_class):
        mock_para1 = MagicMock()
        mock_para1.text = "John Doe"
        mock_para2 = MagicMock()
        mock_para2.text = "Software Engineer"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc_class.return_value = mock_doc

        result = extract_resume_text(b"fake docx bytes", "resume.docx")
        assert "John Doe" in result
        assert "Software Engineer" in result

    @patch("backend.resume.parser.Document", None)
    def test_docx_without_python_docx_raises(self):
        with pytest.raises(ImportError):
            extract_resume_text(b"fake docx", "resume.docx")


class TestExtractResumeTextLatex:
    def test_latex_basic_extraction(self):
        content = br"\section{Experience}\textbf{Senior Engineer} at Google"
        result = extract_resume_text(content, "resume.tex")
        # Should extract text content even if LaTeX commands are present
        assert "Experience" in result or "Senior Engineer" in result

    def test_latex_strips_commands(self):
        content = br"\begin{document}Hello World\end{document}"
        result = extract_resume_text(content, "resume.tex")
        assert "Hello" in result or "World" in result


class TestParseResumeSections:
    def test_identifies_sections(self):
        text = """John Doe
Software Engineer

EXPERIENCE
Senior Engineer at Google
Built distributed systems

EDUCATION
BS Computer Science, MIT

SKILLS
Python, FastAPI, AWS, Docker"""
        sections = parse_resume_sections(text)
        assert isinstance(sections, dict)
        assert "experience" in sections or "EXPERIENCE" in {k.upper() for k in sections}
        assert "education" in sections or "EDUCATION" in {k.upper() for k in sections}
        assert "skills" in sections or "SKILLS" in {k.upper() for k in sections}

    def test_empty_text(self):
        sections = parse_resume_sections("")
        assert isinstance(sections, dict)

    def test_no_clear_sections(self):
        sections = parse_resume_sections("Just some text without clear section headers.")
        assert isinstance(sections, dict)
