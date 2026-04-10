"""Tests for simhash determinism.

Simhash must produce identical fingerprints for identical input across
calls and across process restarts. This requires using a deterministic
hash function (hashlib.md5) instead of Python's built-in hash() which
is randomized via PYTHONHASHSEED.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from app.scraping.deduplication import DeduplicationService
from app.scraping.port import ScrapedJob


def _make_job(title: str, company: str, desc: str = "") -> ScrapedJob:
    return ScrapedJob(
        title=title,
        company_name=company,
        source="test",
        description_raw=desc,
    )


def test_simhash_deterministic_across_calls():
    """Simhash must produce the same value for the same input."""
    svc = DeduplicationService()
    job = _make_job("Senior ML Engineer", "Google", "Mountain View role")
    h1 = svc._compute_simhash(job)
    h2 = svc._compute_simhash(job)
    assert h1 == h2


def test_simhash_different_for_different_input():
    """Distinct jobs must produce different simhash fingerprints."""
    svc = DeduplicationService()
    h1 = svc._compute_simhash(_make_job("ML Engineer", "Google"))
    h2 = svc._compute_simhash(_make_job("Data Scientist", "Meta"))
    assert h1 != h2


def test_simhash_similar_for_similar_input():
    """Near-duplicate jobs should have a smaller Hamming distance than
    completely different jobs.  With short texts simhash distances can be
    large, so we compare *relative* distances rather than using a fixed
    threshold."""
    svc = DeduplicationService()

    base_desc = (
        "Mountain View office. Build machine learning models for search ranking. "
        "5+ years experience required. Python, TensorFlow, distributed systems."
    )
    variant_desc = (
        "Mountain View office. Build machine learning models for search ranking. "
        "5+ years experience required. Python, PyTorch, distributed systems."
    )

    h_base = svc._compute_simhash(_make_job("Senior ML Engineer", "Google", base_desc))
    h_similar = svc._compute_simhash(_make_job("Senior ML Engineer", "Google", variant_desc))
    h_different = svc._compute_simhash(
        _make_job(
            "Marketing Manager",
            "Amazon",
            "Lead brand campaigns across EMEA region. MBA preferred.",
        )
    )

    dist_similar = bin(h_base ^ h_similar).count("1")
    dist_different = bin(h_base ^ h_different).count("1")

    # Similar jobs must be closer than completely different jobs
    assert dist_similar < dist_different, (
        f"similar distance ({dist_similar}) should be < different distance ({dist_different})"
    )


def test_simhash_returns_int():
    """Simhash must return a non-negative integer."""
    svc = DeduplicationService()
    h = svc._compute_simhash(_make_job("Engineer", "Acme"))
    assert isinstance(h, int)
    assert h >= 0


def test_simhash_known_value():
    """Simhash of a fixed input must produce a fixed known value.

    This test will fail if the hash function is non-deterministic across
    process restarts (e.g., using Python's built-in hash() with random seed).
    The expected value was recorded after switching to hashlib.md5.
    """
    svc = DeduplicationService()
    job = _make_job("Software Engineer", "TestCorp", "Build great software")
    h = svc._compute_simhash(job)
    assert h == 2119042606782065073


def test_simhash_deterministic_across_processes():
    """Simhash must be identical across separate Python processes with
    different PYTHONHASHSEED values.  This is the key regression test:
    Python's built-in hash() is randomized per-process, so using it would
    make this test fail."""
    repo_root = Path(__file__).resolve().parents[3]
    python_executable = Path(sys.executable)
    pyvenv_cfg = python_executable.parent.parent / "pyvenv.cfg"
    if not pyvenv_cfg.exists():
        python_executable = Path(
            getattr(sys, "_base_executable", "") or shutil.which("python") or sys.executable
        )

    script = dedent(
        """
        import sys
        import types

        try:
            import structlog  # noqa: F401
        except ModuleNotFoundError:
            structlog = types.ModuleType("structlog")

            class _Logger:
                def info(self, *args, **kwargs):
                    return None

            structlog.get_logger = lambda: _Logger()
            sys.modules["structlog"] = structlog

        from app.scraping.deduplication import DeduplicationService
        from app.scraping.port import ScrapedJob

        svc = DeduplicationService()
        job = ScrapedJob(
            title="Software Engineer",
            company_name="TestCorp",
            source="test",
            description_raw="Build great software",
        )
        print(svc._compute_simhash(job))
        """
    )
    results = []
    for seed in ("111", "999"):
        proc = subprocess.run(
            [str(python_executable), "-c", script],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "PYTHONHASHSEED": seed,
                "PYTHONPATH": (
                    str(repo_root)
                    if not os.environ.get("PYTHONPATH")
                    else f"{repo_root}{os.pathsep}{os.environ['PYTHONPATH']}"
                ),
            },
            cwd=str(repo_root),
        )
        assert proc.returncode == 0, proc.stderr
        results.append(int(proc.stdout.strip()))

    assert results[0] == results[1], (
        f"Simhash differs across processes: seed=111 -> {results[0]}, seed=999 -> {results[1]}"
    )
