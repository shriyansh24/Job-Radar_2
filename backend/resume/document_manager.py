"""Resume document manager — file storage, ULID-based versioning, ingestion."""
import os
import time
from dataclasses import dataclass, field
from backend.resume.parser import extract_resume_text, parse_resume_sections, detect_resume_format

RESUME_DIR = os.path.join("data", "resumes")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@dataclass
class ResumeDocument:
    id: str
    filename: str
    format: str
    file_path: str
    parsed_text: str
    parsed_structured: dict
    version_label: str = "v1"
    is_default: bool = False


def generate_resume_id() -> str:
    """Generate a 26-character ULID (Universally Unique Lexicographically Sortable Identifier)."""
    import random
    ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    t = int(time.time() * 1000)
    # Timestamp: 10 chars
    ts_chars = []
    for _ in range(10):
        ts_chars.append(ENCODING[t & 31])
        t >>= 5
    ts_chars.reverse()
    # Random: 16 chars
    rand_chars = [ENCODING[random.randint(0, 31)] for _ in range(16)]
    return "".join(ts_chars) + "".join(rand_chars)


def get_resume_storage_dir() -> str:
    """Return the resume storage directory, creating it if needed."""
    os.makedirs(RESUME_DIR, exist_ok=True)
    return RESUME_DIR


def ingest_resume(
    file_bytes: bytes, filename: str, version_label: str = "v1"
) -> ResumeDocument:
    """Ingest a resume: validate, store on disk, parse text and sections."""
    if not filename:
        raise ValueError("Filename is required")

    fmt = detect_resume_format(filename)
    if fmt is None:
        raise ValueError(f"Unsupported format: {filename}")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large (max {MAX_FILE_SIZE // (1024 * 1024)}MB)"
        )

    resume_id = generate_resume_id()
    storage_dir = get_resume_storage_dir()
    disk_filename = f"{resume_id}.{fmt}"
    file_path = os.path.join(storage_dir, disk_filename)

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract text
    parsed_text = extract_resume_text(file_bytes, filename)

    # Parse sections
    parsed_structured = parse_resume_sections(parsed_text)

    return ResumeDocument(
        id=resume_id,
        filename=filename,
        format=fmt,
        file_path=f"data/resumes/{disk_filename}",
        parsed_text=parsed_text,
        parsed_structured=parsed_structured,
        version_label=version_label,
        is_default=False,
    )


def delete_resume(resume_id: str, fmt: str) -> None:
    """Delete a resume file from disk. No-op if file does not exist."""
    file_path = os.path.join(get_resume_storage_dir(), f"{resume_id}.{fmt}")
    if os.path.exists(file_path):
        os.remove(file_path)


def list_resume_versions(storage_dir: str | None = None) -> list[str]:
    """List all resume files in the storage directory."""
    d = storage_dir or get_resume_storage_dir()
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if not f.startswith("."))


def get_resume_by_id(resume_id: str, fmt: str) -> bytes | None:
    """Read raw bytes of a stored resume file."""
    file_path = os.path.join(get_resume_storage_dir(), f"{resume_id}.{fmt}")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        return f.read()


def set_default_resume(resume_id: str) -> None:
    """Mark a resume as default. DB update handled by caller."""
    pass  # Actual DB update is in the router layer
