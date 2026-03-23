from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from app.scraping.deduplication import (
    EMBEDDING_COSINE_THRESHOLD,
    LOCATION_SIMILARITY_THRESHOLD,
    TITLE_SIMILARITY_THRESHOLD,
    CompanyBlock,
    DedupDecision,
    DeduplicationResult,
    SixStageDeduplicator,
    _compute_ats_key,
)
from app.scraping.port import ScrapedJob

# ── Helpers ──────────────────────────────────────────────────────────────

def _job(
    title: str = "Software Engineer",
    company: str = "Acme Inc",
    url: str | None = None,
    description: str | None = None,
    location: str | None = None,
    ats_provider: str | None = None,
    ats_job_id: str | None = None,
    company_domain: str | None = None,
    extra_data: dict | None = None,
) -> ScrapedJob:
    return ScrapedJob(
        title=title,
        company_name=company,
        source="test",
        source_url=url,
        description_raw=description,
        location=location,
        ats_provider=ats_provider,
        ats_job_id=ats_job_id,
        company_domain=company_domain,
        extra_data=extra_data or {},
    )


def _run_async(coro):
    """Run an async coroutine synchronously for tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Threshold constants are exported ─────────────────────────────────────

class TestThresholdConstants:
    def test_title_threshold_value(self) -> None:
        assert TITLE_SIMILARITY_THRESHOLD == 70

    def test_embedding_threshold_value(self) -> None:
        assert EMBEDDING_COSINE_THRESHOLD == 0.92

    def test_location_threshold_value(self) -> None:
        assert LOCATION_SIMILARITY_THRESHOLD == 70


# ── ATS composite key ───────────────────────────────────────────────────

class TestComputeAtsKey:
    def test_returns_none_when_missing_fields(self) -> None:
        assert _compute_ats_key(None, "greenhouse", "123") is None
        assert _compute_ats_key("example.com", None, "123") is None
        assert _compute_ats_key("example.com", "greenhouse", None) is None

    def test_returns_deterministic_hash(self) -> None:
        key1 = _compute_ats_key("example.com", "greenhouse", "123")
        key2 = _compute_ats_key("example.com", "greenhouse", "123")
        assert key1 is not None
        assert key1 == key2
        assert len(key1) == 64  # SHA-256 hex

    def test_case_insensitive_domain_provider(self) -> None:
        key1 = _compute_ats_key("Example.COM", "Greenhouse", "123")
        key2 = _compute_ats_key("example.com", "greenhouse", "123")
        assert key1 == key2


# ── CompanyBlock ─────────────────────────────────────────────────────────

class TestCompanyBlock:
    def test_add_and_all_pairs(self) -> None:
        block = CompanyBlock(company_key="acme")
        block.add(_job(title="A"))
        block.add(_job(title="B"))
        block.add(_job(title="C"))
        pairs = block.all_pairs()
        assert len(pairs) == 3  # C(3,2) = 3
        assert (0, 1) in pairs
        assert (0, 2) in pairs
        assert (1, 2) in pairs

    def test_single_job_no_pairs(self) -> None:
        block = CompanyBlock(company_key="solo")
        block.add(_job())
        assert block.all_pairs() == []


# ── Stage 1: ATS Composite Key Exact Match ──────────────────────────────

class TestStage1AtsMatch:
    def test_ats_key_dedup_within_batch(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(
                title="SWE",
                company="Google",
                ats_provider="greenhouse",
                ats_job_id="12345",
                company_domain="google.com",
            ),
            _job(
                title="Software Engineer",
                company="Google LLC",
                ats_provider="greenhouse",
                ats_job_id="12345",
                company_domain="google.com",
            ),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 1
        assert result.stats.get("stage1_ats_dupes", 0) == 1

    def test_different_ats_keys_kept(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(
                title="SWE",
                company="Google",
                ats_provider="greenhouse",
                ats_job_id="111",
                company_domain="google.com",
            ),
            _job(
                title="SWE",
                company="Google",
                ats_provider="greenhouse",
                ats_job_id="222",
                company_domain="google.com",
            ),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        # Different ATS IDs -> different jobs (though title is same,
        # they pass stage 1, then may be caught by later stages)
        assert result.stats.get("stage1_ats_dupes", 0) == 0

    def test_no_ats_info_passes_through(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [_job(title="Designer"), _job(title="Engineer")]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 2


# ── Stage 2: RapidFuzz Title Fast-Reject ─────────────────────────────────

class TestStage2TitleFastReject:
    def test_dissimilar_titles_not_duped(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(title="Software Engineer", company="Acme"),
            _job(title="Marketing Director", company="Acme"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 2
        assert result.stats.get("stage2_title_rejected", 0) >= 1

    def test_similar_titles_pass_stage2(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(title="Senior Software Engineer", company="Acme"),
            _job(title="Sr. Software Engineer", company="Acme"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        # With title normalization, "Sr." -> "Senior", so these should
        # be very similar and pass stage 2
        assert result.stats.get("stage2_title_passed", 0) >= 1

    def test_exact_same_title_same_company(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(title="Software Engineer", company="Acme"),
            _job(title="Software Engineer", company="Acme"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        # Same title, same company -> should be deduped (passes all stages)
        assert len(result.unique_jobs) == 1


# ── Stage 3: Embedding Cosine ───────────────────────────────────────────

class TestStage3EmbeddingCosine:
    def test_with_mock_embedder_high_similarity(self) -> None:
        mock_embedder = MagicMock()
        # Return identical embeddings -> cosine = 1.0
        mock_embedder.embed_text.return_value = [1.0, 0.0, 0.0]

        deduper = SixStageDeduplicator(embedding_service=mock_embedder)
        jobs = [
            _job(title="Software Engineer", company="Acme", description="Build stuff"),
            _job(title="Software Engineer", company="Acme", description="Build things"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 1
        assert result.stats.get("stage3_embedding_passed", 0) >= 1

    def test_with_mock_embedder_low_similarity(self) -> None:
        mock_embedder = MagicMock()
        # Return orthogonal embeddings -> cosine = 0.0
        call_count = 0

        def _alternate_embeddings(text: str) -> list[float]:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:
                return [1.0, 0.0, 0.0]
            return [0.0, 1.0, 0.0]

        mock_embedder.embed_text.side_effect = _alternate_embeddings

        deduper = SixStageDeduplicator(embedding_service=mock_embedder)
        jobs = [
            _job(title="Software Engineer", company="Acme", description="Build stuff"),
            _job(title="Software Engineer", company="Acme", description="Cook food"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 2

    def test_no_embedder_falls_back_to_title(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(title="Software Engineer", company="Acme"),
            _job(title="Software Engineer", company="Acme"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        # Without embedder, exact title match (100% > 90%) should still
        # catch duplicates via fallback
        assert len(result.unique_jobs) == 1


# ── Stage 4: Location/Department Disambiguation ─────────────────────────

class TestStage4Disambiguation:
    def test_different_locations_not_duped(self) -> None:
        mock_embedder = MagicMock()
        mock_embedder.embed_text.return_value = [1.0, 0.0, 0.0]

        deduper = SixStageDeduplicator(embedding_service=mock_embedder)
        jobs = [
            _job(
                title="Software Engineer",
                company="Google",
                location="San Francisco, CA",
                description="Build search",
            ),
            _job(
                title="Software Engineer",
                company="Google",
                location="Tokyo, Japan",
                description="Build search",
            ),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 2
        assert result.stats.get("stage4_disambiguated", 0) >= 1

    def test_different_departments_not_duped(self) -> None:
        mock_embedder = MagicMock()
        mock_embedder.embed_text.return_value = [1.0, 0.0, 0.0]

        deduper = SixStageDeduplicator(embedding_service=mock_embedder)
        jobs = [
            _job(
                title="Software Engineer",
                company="Google",
                location="Mountain View",
                description="Build things",
                extra_data={"department": "Cloud"},
            ),
            _job(
                title="Software Engineer",
                company="Google",
                location="Mountain View",
                description="Build things",
                extra_data={"department": "DeepMind"},
            ),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 2
        assert result.stats.get("stage4_disambiguated", 0) >= 1

    def test_same_location_same_department_deduped(self) -> None:
        mock_embedder = MagicMock()
        mock_embedder.embed_text.return_value = [1.0, 0.0, 0.0]

        deduper = SixStageDeduplicator(embedding_service=mock_embedder)
        jobs = [
            _job(
                title="Software Engineer",
                company="Google",
                location="Mountain View, CA",
                description="Build search",
                extra_data={"department": "Search"},
            ),
            _job(
                title="Software Engineer",
                company="Google",
                location="Mountain View, CA",
                description="Build search",
                extra_data={"department": "Search"},
            ),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 1

    def test_no_location_no_department_still_deduped(self) -> None:
        mock_embedder = MagicMock()
        mock_embedder.embed_text.return_value = [1.0, 0.0, 0.0]

        deduper = SixStageDeduplicator(embedding_service=mock_embedder)
        jobs = [
            _job(title="Software Engineer", company="Acme", description="Build"),
            _job(title="Software Engineer", company="Acme", description="Build"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 1


# ── Stage 5: Merge Groups ───────────────────────────────────────────────

class TestStage5MergeGroups:
    def test_merge_group_formed(self) -> None:
        mock_embedder = MagicMock()
        mock_embedder.embed_text.return_value = [1.0, 0.0, 0.0]

        deduper = SixStageDeduplicator(embedding_service=mock_embedder)
        jobs = [
            _job(title="Software Engineer", company="Acme", description="Build stuff"),
            _job(title="Software Engineer", company="Acme", description="Build stuff"),
            _job(title="Software Engineer", company="Acme", description="Build stuff"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert result.stats.get("merge_groups", 0) >= 1
        assert len(result.unique_jobs) == 1


# ── Stage 6: Confidence Scoring ──────────────────────────────────────────

class TestStage6Confidence:
    def test_confidence_with_embeddings(self) -> None:
        score = SixStageDeduplicator._compute_confidence(
            title_sim=95.0, cos_sim=0.98
        )
        # 0.4 * 0.95 + 0.6 * 0.98 = 0.38 + 0.588 = 0.968
        assert 0.96 <= score <= 0.97

    def test_confidence_without_embeddings(self) -> None:
        score = SixStageDeduplicator._compute_confidence(
            title_sim=90.0, cos_sim=0.0
        )
        assert score == 0.9

    def test_confidence_clamped_to_1(self) -> None:
        score = SixStageDeduplicator._compute_confidence(
            title_sim=100.0, cos_sim=1.0
        )
        assert score == 1.0

    def test_confidence_in_dedup_decisions(self) -> None:
        mock_embedder = MagicMock()
        mock_embedder.embed_text.return_value = [1.0, 0.0, 0.0]

        deduper = SixStageDeduplicator(embedding_service=mock_embedder)
        jobs = [
            _job(title="Software Engineer", company="Acme", description="Build"),
            _job(title="Software Engineer", company="Acme", description="Build"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        confirmed = [d for d in result.duplicate_pairs if d.is_duplicate]
        assert len(confirmed) >= 1
        for decision in confirmed:
            assert 0.0 <= decision.confidence <= 1.0


# ── Company Blocking ────────────────────────────────────────────────────

class TestCompanyBlocking:
    def test_different_companies_not_compared(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(title="Software Engineer", company="Google"),
            _job(title="Software Engineer", company="Meta"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 2

    def test_company_normalization_groups_correctly(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(title="Software Engineer", company="Google LLC"),
            _job(title="Software Engineer", company="Google Inc"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        # Both normalize to "google" -> same block -> deduplicated
        assert len(result.unique_jobs) == 1


# ── Edge Cases ───────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_input(self) -> None:
        deduper = SixStageDeduplicator()
        result = _run_async(deduper.deduplicate([]))
        assert len(result.unique_jobs) == 0
        assert len(result.duplicate_pairs) == 0

    def test_single_job(self) -> None:
        deduper = SixStageDeduplicator()
        result = _run_async(deduper.deduplicate([_job()]))
        assert len(result.unique_jobs) == 1

    def test_all_different_jobs(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(title="Software Engineer", company="Google"),
            _job(title="Data Scientist", company="Meta"),
            _job(title="Product Manager", company="Amazon"),
            _job(title="Designer", company="Apple"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        assert len(result.unique_jobs) == 4

    def test_result_stats_populated(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [_job(), _job()]
        result = _run_async(deduper.deduplicate(jobs))
        assert "total_input" in result.stats
        assert "total_unique" in result.stats
        assert result.stats["total_input"] == 2

    def test_mixed_ats_and_non_ats(self) -> None:
        deduper = SixStageDeduplicator()
        jobs = [
            _job(
                title="SWE",
                company="Google",
                ats_provider="greenhouse",
                ats_job_id="111",
                company_domain="google.com",
            ),
            _job(title="SWE", company="Google"),  # no ATS info
            _job(title="Designer", company="Meta"),
        ]
        result = _run_async(deduper.deduplicate(jobs))
        # The two Google SWE jobs may or may not be deduped depending on
        # title similarity and fallback; but all should process without error
        assert result.stats["total_input"] == 3


# ── Cosine Similarity ───────────────────────────────────────────────────

class TestCosineSimilarity:
    def test_identical_vectors(self) -> None:
        sim = SixStageDeduplicator._cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert abs(sim - 1.0) < 1e-6

    def test_orthogonal_vectors(self) -> None:
        sim = SixStageDeduplicator._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert abs(sim) < 1e-6

    def test_opposite_vectors(self) -> None:
        sim = SixStageDeduplicator._cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert abs(sim + 1.0) < 1e-6

    def test_zero_vector(self) -> None:
        sim = SixStageDeduplicator._cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert sim == 0.0


# ── DeduplicationResult dataclass ────────────────────────────────────────

class TestDeduplicationResult:
    def test_default_fields(self) -> None:
        result = DeduplicationResult()
        assert result.unique_jobs == []
        assert result.duplicate_pairs == []
        assert result.updated_jobs == []
        assert result.merged_groups == []
        assert result.stats == {}


# ── DedupDecision dataclass ──────────────────────────────────────────────

class TestDedupDecision:
    def test_fields(self) -> None:
        a = _job(title="A")
        b = _job(title="B")
        d = DedupDecision(
            job_a=a,
            job_b=b,
            is_duplicate=True,
            confidence=0.95,
            stage_decided=3,
            reason="embedding_match",
        )
        assert d.is_duplicate is True
        assert d.confidence == 0.95
        assert d.stage_decided == 3
