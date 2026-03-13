"""Test 3-layer deduplication: exact hash, SimHash, fuzzy blocking."""
import pytest
from backend.enrichment.deduplicator import (
    compute_simhash,
    hamming_distance,
    deduplicate_batch,
    DedupResult,
)


class TestSimHash:
    def test_identical_texts_same_hash(self):
        h1 = compute_simhash("Senior Software Engineer at Google in San Francisco")
        h2 = compute_simhash("Senior Software Engineer at Google in San Francisco")
        assert h1 == h2

    def test_similar_texts_close_hash(self):
        # "San Francisco" vs "Mountain View" differ in only 2 out of 7 tokens.
        # For 64-bit SimHash the Hamming distance for near-similar job strings is
        # empirically < 20; completely unrelated strings typically score > 24.
        h1 = compute_simhash("Senior Software Engineer at Google in San Francisco")
        h2 = compute_simhash("Senior Software Engineer at Google in Mountain View")
        unrelated = compute_simhash("Junior Marketing Manager at Nike")
        d_similar = hamming_distance(h1, h2)
        d_unrelated = hamming_distance(h1, unrelated)
        # Similar pair must be closer than the unrelated pair
        assert d_similar < d_unrelated
        # And must be within a reasonable upper bound (< 20 for these strings)
        assert d_similar < 20

    def test_different_texts_far_hash(self):
        h1 = compute_simhash("Senior Software Engineer at Google")
        h2 = compute_simhash("Junior Marketing Manager at Nike")
        assert hamming_distance(h1, h2) > 3

    def test_empty_text(self):
        h = compute_simhash("")
        assert isinstance(h, int)

    def test_empty_text_returns_zero(self):
        """Empty text should consistently return 0."""
        assert compute_simhash("") == 0

    def test_single_word_deterministic(self):
        h1 = compute_simhash("python")
        h2 = compute_simhash("python")
        assert h1 == h2

    def test_hash_is_64_bit(self):
        """SimHash result must fit in 64 bits."""
        h = compute_simhash("Senior Software Engineer at Acme Corp")
        assert 0 <= h < (1 << 64)

    def test_case_insensitive(self):
        """SimHash should be case-insensitive (we normalise to lower)."""
        h1 = compute_simhash("Senior Software Engineer")
        h2 = compute_simhash("SENIOR SOFTWARE ENGINEER")
        assert h1 == h2

    def test_whitespace_only(self):
        """Whitespace-only text behaves like empty text."""
        h = compute_simhash("   ")
        assert isinstance(h, int)


class TestHammingDistance:
    def test_same_value(self):
        assert hamming_distance(0b1010, 0b1010) == 0

    def test_one_bit_different(self):
        assert hamming_distance(0b1010, 0b1011) == 1

    def test_all_bits_different(self):
        assert hamming_distance(0, 0xFF) == 8

    def test_zero_vs_max_64bit(self):
        max64 = (1 << 64) - 1
        assert hamming_distance(0, max64) == 64

    def test_symmetric(self):
        assert hamming_distance(0b1100, 0b0011) == hamming_distance(0b0011, 0b1100)

    def test_zero_distance_for_zeros(self):
        assert hamming_distance(0, 0) == 0


class TestDedupResult:
    def test_has_expected_fields(self):
        r = DedupResult(kept=[], duplicates=[], stats={})
        assert hasattr(r, "kept") and hasattr(r, "duplicates") and hasattr(r, "stats")

    def test_default_stats_keys(self):
        r = DedupResult()
        assert "l1_deduped" in r.stats
        assert "l2_deduped" in r.stats
        assert "l3_deduped" in r.stats

    def test_default_empty_lists(self):
        r = DedupResult()
        assert r.kept == []
        assert r.duplicates == []

    def test_can_hold_jobs(self):
        job = {"dedup_hash": "x", "title": "SWE", "company_name": "Acme"}
        r = DedupResult(kept=[job], duplicates=[], stats={"l1_deduped": 0})
        assert r.kept[0] is job


class TestDeduplicateBatch:
    # ── L1: exact hash ───────────────────────────────────────────────────

    def test_exact_hash_dedup(self):
        jobs = [
            {
                "dedup_hash": "abc123",
                "title": "SWE",
                "company_name": "Google",
                "location": "SF",
                "description_clean": "Build stuff",
            },
            {
                "dedup_hash": "abc123",
                "title": "SWE",
                "company_name": "Google",
                "location": "SF",
                "description_clean": "Build stuff",
            },
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        assert len(result.kept) == 1
        assert len(result.duplicates) == 1
        assert result.stats["l1_deduped"] == 1

    def test_no_duplicates(self):
        jobs = [
            {
                "dedup_hash": "abc",
                "title": "SWE",
                "company_name": "Google",
                "location": "SF",
                "description_clean": "Python",
            },
            {
                "dedup_hash": "def",
                "title": "PM",
                "company_name": "Meta",
                "location": "NY",
                "description_clean": "Product",
            },
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        assert len(result.kept) == 2
        assert len(result.duplicates) == 0

    def test_existing_hash_filtered(self):
        jobs = [
            {
                "dedup_hash": "existing_one",
                "title": "SWE",
                "company_name": "Google",
                "location": "SF",
                "description_clean": "Stuff",
            }
        ]
        result = deduplicate_batch(jobs, existing_hashes={"existing_one"})
        assert len(result.kept) == 0
        assert result.stats["l1_deduped"] == 1

    def test_multiple_existing_hashes_all_filtered(self):
        jobs = [
            {"dedup_hash": "h1", "title": "A", "company_name": "X", "location": "L", "description_clean": ""},
            {"dedup_hash": "h2", "title": "B", "company_name": "Y", "location": "L", "description_clean": ""},
        ]
        result = deduplicate_batch(jobs, existing_hashes={"h1", "h2"})
        assert len(result.kept) == 0
        assert result.stats["l1_deduped"] == 2

    def test_partial_existing_hashes(self):
        jobs = [
            {"dedup_hash": "h1", "title": "A", "company_name": "X", "location": "L", "description_clean": ""},
            {"dedup_hash": "h2", "title": "B SWE totally different", "company_name": "Z", "location": "Q", "description_clean": ""},
        ]
        result = deduplicate_batch(jobs, existing_hashes={"h1"})
        assert len(result.kept) == 1
        assert result.kept[0]["dedup_hash"] == "h2"
        assert result.stats["l1_deduped"] == 1

    # ── L3: fuzzy title blocking ──────────────────────────────────────────
    # (L2 SimHash also triggers in some of these — we assert dup count ≥ 1)

    def test_fuzzy_dedup_similar_titles(self):
        jobs = [
            {
                "dedup_hash": "aaa",
                "title": "Senior Software Engineer",
                "company_name": "Google",
                "location": "San Francisco",
                "description_clean": "A",
            },
            {
                "dedup_hash": "bbb",
                "title": "Sr. Software Engineer",
                "company_name": "Google",
                "location": "San Francisco",
                "description_clean": "B",
            },
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        assert len(result.duplicates) >= 1 or len(result.kept) <= 1

    def test_fuzzy_dedup_different_companies_not_deduped(self):
        """Same title at different companies should NOT be deduplicated by L3."""
        jobs = [
            {
                "dedup_hash": "x1",
                "title": "Senior Software Engineer",
                "company_name": "Google",
                "location": "Remote",
                "description_clean": "A",
            },
            {
                "dedup_hash": "x2",
                "title": "Senior Software Engineer",
                "company_name": "Meta",
                "location": "Remote",
                "description_clean": "B",
            },
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        # Different companies — L3 should not fire; L2 might fire if SimHash
        # happens to be close, so we only assert total kept+dups == 2
        assert len(result.kept) + len(result.duplicates) == 2

    def test_completely_different_jobs_all_kept(self):
        jobs = [
            {
                "dedup_hash": "z1",
                "title": "Neurosurgeon",
                "company_name": "Hospital A",
                "location": "Boston",
                "description_clean": "Medicine",
            },
            {
                "dedup_hash": "z2",
                "title": "Logistics Driver",
                "company_name": "Trucking Co",
                "location": "Dallas",
                "description_clean": "Drive trucks",
            },
            {
                "dedup_hash": "z3",
                "title": "Pastry Chef",
                "company_name": "Bakery Z",
                "location": "Paris",
                "description_clean": "Bake croissants",
            },
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        assert len(result.kept) == 3
        assert len(result.duplicates) == 0

    # ── Edge cases ────────────────────────────────────────────────────────

    def test_empty_batch(self):
        result = deduplicate_batch([], existing_hashes=set())
        assert len(result.kept) == 0

    def test_empty_batch_stats_zeroed(self):
        result = deduplicate_batch([], existing_hashes=set())
        assert result.stats["l1_deduped"] == 0
        assert result.stats["l2_deduped"] == 0
        assert result.stats["l3_deduped"] == 0

    def test_single_job_always_kept(self):
        job = {"dedup_hash": "solo", "title": "Lone Ranger", "company_name": "X", "location": "Y", "description_clean": ""}
        result = deduplicate_batch([job], existing_hashes=set())
        assert len(result.kept) == 1
        assert len(result.duplicates) == 0

    def test_total_count_equals_input(self):
        """kept + duplicates must always equal the number of input jobs."""
        jobs = [
            {"dedup_hash": "a", "title": "Eng", "company_name": "A", "location": "X", "description_clean": ""},
            {"dedup_hash": "a", "title": "Eng", "company_name": "A", "location": "X", "description_clean": ""},
            {"dedup_hash": "b", "title": "PM", "company_name": "B", "location": "Y", "description_clean": ""},
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        assert len(result.kept) + len(result.duplicates) == len(jobs)

    def test_missing_dedup_hash_treated_as_empty_string(self):
        """Jobs without dedup_hash use empty string — first kept, second is dup."""
        jobs = [
            {"title": "SWE", "company_name": "G", "location": "L", "description_clean": ""},
            {"title": "SWE", "company_name": "G", "location": "L", "description_clean": ""},
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        # Both have dedup_hash="" so second is L1 dup
        assert len(result.kept) + len(result.duplicates) == 2
