from __future__ import annotations

from app.scraping.deduplication import DeduplicationService
from app.scraping.port import ScrapedJob


def _job(
    title: str = "Software Engineer",
    company: str = "Acme Inc",
    url: str | None = None,
    description: str | None = None,
) -> ScrapedJob:
    return ScrapedJob(
        title=title,
        company_name=company,
        source="test",
        source_url=url,
        description_raw=description,
    )


class TestContentHash:
    """Layer 1: exact content hash dedup."""

    def test_identical_jobs_deduped(self):
        svc = DeduplicationService()
        jobs = [_job(), _job()]
        result = svc.deduplicate(jobs)
        assert len(result) == 1

    def test_different_jobs_kept(self):
        svc = DeduplicationService()
        jobs = [_job(title="Frontend Engineer"), _job(title="Backend Engineer")]
        result = svc.deduplicate(jobs)
        assert len(result) == 2

    def test_case_insensitive(self):
        svc = DeduplicationService()
        jobs = [
            _job(title="Software Engineer", company="Acme Inc"),
            _job(title="software engineer", company="acme inc"),
        ]
        result = svc.deduplicate(jobs)
        assert len(result) == 1


class TestURLDedup:
    """Layer 2: URL dedup."""

    def test_same_url_deduped(self):
        svc = DeduplicationService()
        jobs = [
            _job(title="Job A", url="https://example.com/jobs/123"),
            _job(title="Job B", url="https://example.com/jobs/123"),
        ]
        result = svc.deduplicate(jobs)
        assert len(result) == 1

    def test_tracking_params_stripped(self):
        svc = DeduplicationService()
        jobs = [
            _job(title="Job A", url="https://example.com/jobs/123"),
            _job(
                title="Job B",
                url="https://example.com/jobs/123?utm_source=google&utm_medium=cpc",
            ),
        ]
        result = svc.deduplicate(jobs)
        assert len(result) == 1

    def test_different_urls_kept(self):
        svc = DeduplicationService()
        jobs = [
            _job(title="Job A", company="Foo", url="https://example.com/jobs/123"),
            _job(title="Job B", company="Bar", url="https://example.com/jobs/456"),
        ]
        result = svc.deduplicate(jobs)
        assert len(result) == 2


class TestSimhash:
    """Layer 3: simhash near-duplicate detection."""

    def test_near_duplicates_deduped(self):
        svc = DeduplicationService()
        desc = "We are looking for a talented software engineer to join our team."
        jobs = [
            _job(
                title="Software Dev",
                company="Foo",
                url="https://a.com/1",
                description=desc,
            ),
            _job(
                title="Software Dev",
                company="Foo",
                url="https://b.com/2",
                description=desc + " Apply today!",
            ),
        ]
        result = svc.deduplicate(jobs)
        # Should be deduped as near-duplicates
        assert len(result) == 1

    def test_very_different_kept(self):
        svc = DeduplicationService()
        jobs = [
            _job(
                title="Data Scientist",
                company="Alpha",
                url="https://a.com/1",
                description="Machine learning, Python, TensorFlow, deep learning research.",
            ),
            _job(
                title="Chef",
                company="Beta Restaurant",
                url="https://b.com/2",
                description="Culinary arts, kitchen management, Italian cuisine.",
            ),
        ]
        result = svc.deduplicate(jobs)
        assert len(result) == 2


class TestHammingDistance:
    def test_same_fingerprint(self):
        svc = DeduplicationService()
        assert svc._hamming_distance(0, 0) == 0

    def test_one_bit_different(self):
        svc = DeduplicationService()
        assert svc._hamming_distance(0b1000, 0b0000) == 1

    def test_all_bits_different(self):
        svc = DeduplicationService()
        assert svc._hamming_distance(0, (1 << 64) - 1) == 64
