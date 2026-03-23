"""Unit tests for ATS composite key computation."""

from __future__ import annotations

import hashlib

from app.scraping.service import compute_ats_composite_key


class TestComputeAtsCompositeKey:
    """Verify the composite key is a deterministic SHA-256 and handles missing inputs."""

    def test_deterministic_sha256(self):
        """Same inputs always produce the same hash."""
        key1 = compute_ats_composite_key("example.com", "greenhouse", "12345")
        key2 = compute_ats_composite_key("example.com", "greenhouse", "12345")
        assert key1 == key2
        assert key1 is not None
        assert len(key1) == 64  # SHA-256 hex digest length

    def test_matches_manual_sha256(self):
        """Output matches a manually computed SHA-256."""
        raw = "example.com|greenhouse|12345"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        result = compute_ats_composite_key("example.com", "greenhouse", "12345")
        assert result == expected

    def test_case_and_whitespace_normalization(self):
        """Domain and provider are lowercased; job_id is stripped."""
        key1 = compute_ats_composite_key("EXAMPLE.COM", "Greenhouse", " 12345 ")
        key2 = compute_ats_composite_key("example.com", "greenhouse", "12345")
        assert key1 == key2

    def test_hash_when_company_domain_missing(self):
        raw = "|greenhouse|12345"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert compute_ats_composite_key(None, "greenhouse", "12345") == expected

    def test_hash_when_company_domain_empty(self):
        raw = "|greenhouse|12345"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert compute_ats_composite_key("", "greenhouse", "12345") == expected

    def test_none_when_ats_provider_missing(self):
        assert compute_ats_composite_key("example.com", None, "12345") is None

    def test_none_when_ats_job_id_missing(self):
        assert compute_ats_composite_key("example.com", "greenhouse", None) is None

    def test_none_when_all_missing(self):
        assert compute_ats_composite_key(None, None, None) is None

    def test_none_when_empty_string_provider(self):
        assert compute_ats_composite_key("example.com", "", "12345") is None

    def test_none_when_empty_string_job_id(self):
        assert compute_ats_composite_key("example.com", "greenhouse", "") is None

    def test_different_providers_produce_different_keys(self):
        key_gh = compute_ats_composite_key("example.com", "greenhouse", "12345")
        key_lv = compute_ats_composite_key("example.com", "lever", "12345")
        assert key_gh != key_lv

    def test_different_domains_produce_different_keys(self):
        key1 = compute_ats_composite_key("foo.com", "greenhouse", "12345")
        key2 = compute_ats_composite_key("bar.com", "greenhouse", "12345")
        assert key1 != key2

    def test_different_job_ids_produce_different_keys(self):
        key1 = compute_ats_composite_key("example.com", "greenhouse", "111")
        key2 = compute_ats_composite_key("example.com", "greenhouse", "222")
        assert key1 != key2
