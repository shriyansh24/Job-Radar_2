"""Multi-format resume text extraction and section parsing."""
import io
import re

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from pylatexenc.latex2text import LatexNodes2Text
except ImportError:
    LatexNodes2Text = None


SUPPORTED_FORMATS = frozenset({"pdf", "docx", "md", "txt", "tex"})

SECTION_PATTERNS = [
    re.compile(r"^(experience|work\s*experience|professional\s*experience|employment)", re.IGNORECASE),
    re.compile(r"^(education|academic|qualifications)", re.IGNORECASE),
    re.compile(r"^(skills|technical\s*skills|core\s*competencies|technologies)", re.IGNORECASE),
    re.compile(r"^(projects|personal\s*projects|open\s*source)", re.IGNORECASE),
    re.compile(r"^(certifications?|licenses?)", re.IGNORECASE),
    re.compile(r"^(summary|objective|profile|about)", re.IGNORECASE),
    re.compile(r"^(awards?|honors?|achievements?)", re.IGNORECASE),
    re.compile(r"^(publications?|papers?|research)", re.IGNORECASE),
    re.compile(r"^(volunteer|community|leadership)", re.IGNORECASE),
    re.compile(r"^(interests?|hobbies?|activities?)", re.IGNORECASE),
]


def detect_resume_format(filename: str) -> str | None:
    """Return the lowercase extension if supported, else None."""
    if not filename or "." not in filename:
        return None
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext if ext in SUPPORTED_FORMATS else None


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from resume bytes based on file format."""
    fmt = detect_resume_format(filename)
    if fmt is None:
        raise ValueError(f"Unsupported format: {filename}")

    if fmt == "txt":
        return file_bytes.decode("utf-8", errors="ignore")

    if fmt == "md":
        # Decode and strip common markdown formatting markers
        text = file_bytes.decode("utf-8", errors="ignore")
        # Remove markdown headers but keep text
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        # Remove bold/italic markers but keep text
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
        # Remove list markers
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        return text

    if fmt == "pdf":
        if pdfplumber is None:
            raise ImportError(
                "pdfplumber is required for PDF parsing. Install with: pip install pdfplumber"
            )
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)

    if fmt == "docx":
        if Document is None:
            raise ImportError(
                "python-docx is required for DOCX parsing. Install with: pip install python-docx"
            )
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    if fmt == "tex":
        raw = file_bytes.decode("utf-8", errors="ignore")
        if LatexNodes2Text is not None:
            try:
                return LatexNodes2Text().latex_to_text(raw)
            except Exception:
                pass
        # Fallback: strip common LaTeX commands
        text = re.sub(r"\\(?:begin|end)\{[^}]*\}", "", raw)
        text = re.sub(r"\\[a-zA-Z]+\*?\{([^}]*)\}", r"\1", text)
        text = re.sub(r"\\[a-zA-Z]+\*?", "", text)
        text = re.sub(r"[{}]", "", text)
        return text.strip()

    return ""


def parse_resume_sections(text: str) -> dict[str, str]:
    """Parse a resume text into labelled sections."""
    if not text.strip():
        return {}

    lines = text.split("\n")
    sections: dict[str, str] = {}
    current_section = "header"
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue

        matched = False
        for pattern in SECTION_PATTERNS:
            m = pattern.match(stripped)
            if m:
                # Save previous section
                if current_lines:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = m.group(1).lower().strip()
                current_lines = []
                matched = True
                break

        if not matched:
            # Check if line looks like an all-caps section header
            if stripped.isupper() and len(stripped.split()) <= 4 and len(stripped) > 2:
                if current_lines:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = stripped.lower()
                current_lines = []
            else:
                current_lines.append(line)

    # Save last section
    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    return sections
