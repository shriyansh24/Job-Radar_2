from __future__ import annotations

import hashlib

from app.scraping.deduplication import compute_ats_composite_key, derive_ats_identity
from app.scraping.port import ScrapedJob


def test_compute_ats_composite_key_is_deterministic() -> None:
    key_one = compute_ats_composite_key("example.com", "greenhouse", "12345")
    key_two = compute_ats_composite_key("example.com", "greenhouse", "12345")

    assert key_one == key_two
    assert key_one is not None
    assert len(key_one) == 64


def test_compute_ats_composite_key_matches_sha256() -> None:
    raw = "example.com|greenhouse|12345"
    expected = hashlib.sha256(raw.encode()).hexdigest()

    assert compute_ats_composite_key("example.com", "greenhouse", "12345") == expected


def test_compute_ats_composite_key_returns_none_without_required_parts() -> None:
    assert compute_ats_composite_key("example.com", None, "12345") is None
    assert compute_ats_composite_key("example.com", "greenhouse", None) is None
    assert compute_ats_composite_key(None, None, None) is None


def test_derive_ats_identity_prefers_explicit_scraped_fields() -> None:
    scraped = ScrapedJob(
        title="Software Engineer",
        company_name="Acme",
        source="greenhouse",
        source_url="https://boards.greenhouse.io/acme/jobs/54321",
        ats_provider="greenhouse",
        ats_job_id="12345",
        company_domain="example.com",
    )

    identity = derive_ats_identity(scraped)

    assert identity["ats_provider"] == "greenhouse"
    assert identity["ats_job_id"] == "12345"
    assert identity["ats_composite_key"] == compute_ats_composite_key(
        "example.com", "greenhouse", "12345"
    )


def test_derive_ats_identity_falls_back_to_url_shape() -> None:
    scraped = ScrapedJob(
        title="Backend Engineer",
        company_name="Acme",
        source="lever",
        source_url="https://jobs.lever.co/acme/abcdef12-3456-7890-abcd-ef1234567890",
    )

    identity = derive_ats_identity(scraped)

    assert identity["ats_provider"] == "lever"
    assert identity["ats_job_id"] == "abcdef12-3456-7890-abcd-ef1234567890"
    assert identity["ats_composite_key"] == compute_ats_composite_key(
        "acme",
        "lever",
        "abcdef12-3456-7890-abcd-ef1234567890",
    )
