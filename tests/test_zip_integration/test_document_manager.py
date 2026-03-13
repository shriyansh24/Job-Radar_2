"""Test resume document manager — ULID storage, ingestion, version management."""
import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from backend.resume.document_manager import (
    ResumeDocument,
    ingest_resume,
    get_resume_storage_dir,
    list_resume_versions,
    get_resume_by_id,
    delete_resume,
    set_default_resume,
    generate_resume_id,
)


class TestGenerateResumeId:
    def test_returns_26_char_string(self):
        rid = generate_resume_id()
        assert len(rid) == 26
        assert isinstance(rid, str)

    def test_unique_ids(self):
        ids = {generate_resume_id() for _ in range(100)}
        assert len(ids) == 100  # All unique

    def test_sortable(self):
        id1 = generate_resume_id()
        import time; time.sleep(0.01)
        id2 = generate_resume_id()
        assert id1 < id2  # ULIDs are time-sortable


class TestResumeDocument:
    def test_dataclass_fields(self):
        doc = ResumeDocument(
            id="01HXXXXXXXXXXXXXXXXXXXXXX",
            filename="resume.pdf",
            format="pdf",
            file_path="data/resumes/01HX.pdf",
            parsed_text="John Doe",
            parsed_structured={"header": "John Doe"},
            version_label="v1",
            is_default=True,
        )
        assert doc.id == "01HXXXXXXXXXXXXXXXXXXXXXX"
        assert doc.format == "pdf"
        assert doc.is_default is True


class TestGetResumeStorageDir:
    def test_returns_path(self):
        path = get_resume_storage_dir()
        assert "resumes" in path

    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", os.path.join(tmpdir, "resumes")):
                path = get_resume_storage_dir()
                assert os.path.isdir(path)


class TestIngestResume:
    def test_ingest_txt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                doc = ingest_resume(b"John Doe\nSoftware Engineer", "resume.txt")
                assert isinstance(doc, ResumeDocument)
                assert doc.filename == "resume.txt"
                assert doc.format == "txt"
                assert "John Doe" in doc.parsed_text
                assert len(doc.id) == 26
                # File should exist on disk
                assert os.path.exists(os.path.join(tmpdir, f"{doc.id}.txt"))

    def test_ingest_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                doc = ingest_resume(b"# John Doe\n## Skills\nPython", "resume.md")
                assert doc.format == "md"
                assert "John Doe" in doc.parsed_text

    def test_ingest_unsupported_raises(self):
        with pytest.raises(ValueError):
            ingest_resume(b"content", "resume.jpg")

    def test_ingest_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                doc = ingest_resume(b"Test content", "test.txt")
                file_path = os.path.join(tmpdir, f"{doc.id}.txt")
                assert os.path.exists(file_path)
                with open(file_path, "rb") as f:
                    assert f.read() == b"Test content"

    def test_version_label_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                doc = ingest_resume(b"content", "r.txt")
                assert doc.version_label == "v1"

    def test_custom_version_label(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                doc = ingest_resume(b"content", "r.txt", version_label="tailored-google")
                assert doc.version_label == "tailored-google"

    def test_large_file_raises(self):
        # 10MB file should be rejected (max 5MB)
        with pytest.raises(ValueError, match="too large"):
            ingest_resume(b"x" * (6 * 1024 * 1024), "big.txt")

    def test_empty_filename_raises(self):
        with pytest.raises(ValueError):
            ingest_resume(b"content", "")

    def test_parsed_structured_populated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                content = b"John Doe\n\nEXPERIENCE\nSenior Engineer at Google\n\nSKILLS\nPython, AWS"
                doc = ingest_resume(content, "resume.txt")
                assert isinstance(doc.parsed_structured, dict)


class TestDeleteResume:
    def test_delete_removes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                doc = ingest_resume(b"content", "test.txt")
                file_path = os.path.join(tmpdir, f"{doc.id}.txt")
                assert os.path.exists(file_path)
                delete_resume(doc.id, "txt")
                assert not os.path.exists(file_path)

    def test_delete_nonexistent_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                # Should not raise
                delete_resume("nonexistent_id", "txt")
