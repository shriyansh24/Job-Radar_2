from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.jobs.models import Job
from app.scraping.dedup_feedback import (
    DedupFeedbackService,
    _string_similarity,
    check_feedback_override,
)
from app.scraping.deduplication import DeduplicationService
from app.scraping.port import ScrapedJob

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user(db: AsyncSession, suffix: str = "") -> User:
    user = User(
        email=f"dedup-test{suffix}@example.com",
        password_hash="unused",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _make_job_id(title: str, company: str) -> str:
    import hashlib

    return hashlib.sha256(f"{title}|{company}".encode()).hexdigest()


async def _create_job(
    db: AsyncSession,
    title: str = "Software Engineer",
    company: str = "Acme Inc",
    user_id: uuid.UUID | None = None,
) -> Job:
    job_id = _make_job_id(title, company)
    job = Job(
        id=job_id,
        title=title,
        company_name=company,
        source="test",
        user_id=user_id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# record_feedback tests
# ---------------------------------------------------------------------------


class TestRecordFeedback:
    @pytest.mark.asyncio
    async def test_record_same(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        job_a = await _create_job(db_session, "Engineer A", "Co A", user.id)
        job_b = await _create_job(db_session, "Engineer B", "Co B", user.id)

        svc = DedupFeedbackService(db_session)
        fb = await svc.record_feedback(job_a.id, job_b.id, "same", user.id)

        assert fb.is_duplicate is True
        assert fb.job_a_id == min(job_a.id, job_b.id)
        assert fb.job_b_id == max(job_a.id, job_b.id)

    @pytest.mark.asyncio
    async def test_record_different(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        job_a = await _create_job(db_session, "Engineer C", "Co C", user.id)
        job_b = await _create_job(db_session, "Chef D", "Restaurant D", user.id)

        svc = DedupFeedbackService(db_session)
        fb = await svc.record_feedback(job_a.id, job_b.id, "different", user.id)

        assert fb.is_duplicate is False

    @pytest.mark.asyncio
    async def test_canonical_ordering(self, db_session: AsyncSession) -> None:
        """(a,b) and (b,a) should produce the same canonical pair."""
        user = await _create_user(db_session)
        job_a = await _create_job(db_session, "Dev E", "Co E", user.id)
        job_b = await _create_job(db_session, "Dev F", "Co F", user.id)

        svc = DedupFeedbackService(db_session)
        fb1 = await svc.record_feedback(job_a.id, job_b.id, "same", user.id)
        fb2 = await svc.record_feedback(job_b.id, job_a.id, "different", user.id)

        # Both should have same canonical ordering
        assert fb1.job_a_id == fb2.job_a_id
        assert fb1.job_b_id == fb2.job_b_id

    @pytest.mark.asyncio
    async def test_computes_features(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        job_a = await _create_job(db_session, "Software Engineer", "Google", user.id)
        job_b = await _create_job(db_session, "Software Engineer", "Google Inc", user.id)

        svc = DedupFeedbackService(db_session)
        fb = await svc.record_feedback(job_a.id, job_b.id, "same", user.id)

        assert fb.title_similarity is not None
        assert fb.company_ratio is not None
        assert fb.title_similarity == 1.0  # Same title


# ---------------------------------------------------------------------------
# lookup_pair tests
# ---------------------------------------------------------------------------


class TestLookupPair:
    @pytest.mark.asyncio
    async def test_lookup_existing(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        job_a = await _create_job(db_session, "Lookup A", "Co A", user.id)
        job_b = await _create_job(db_session, "Lookup B", "Co B", user.id)

        svc = DedupFeedbackService(db_session)
        await svc.record_feedback(job_a.id, job_b.id, "same", user.id)

        result = await svc.lookup_pair(job_a.id, job_b.id, user.id)
        assert result is not None
        assert result.is_duplicate is True

    @pytest.mark.asyncio
    async def test_lookup_reversed_order(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        job_a = await _create_job(db_session, "RevA", "CoX", user.id)
        job_b = await _create_job(db_session, "RevB", "CoY", user.id)

        svc = DedupFeedbackService(db_session)
        await svc.record_feedback(job_a.id, job_b.id, "different", user.id)

        # Lookup in reversed order
        result = await svc.lookup_pair(job_b.id, job_a.id, user.id)
        assert result is not None
        assert result.is_duplicate is False

    @pytest.mark.asyncio
    async def test_lookup_nonexistent(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        svc = DedupFeedbackService(db_session)
        result = await svc.lookup_pair("nonexistent_a", "nonexistent_b", user.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_hidden_from_other_user(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session, "owner")
        other_user = await _create_user(db_session, "other")
        job_a = await _create_job(db_session, "Hidden A", "Hidden Co", user.id)
        job_b = await _create_job(db_session, "Hidden B", "Hidden Co", user.id)

        svc = DedupFeedbackService(db_session)
        await svc.record_feedback(job_a.id, job_b.id, "same", user.id)

        result = await svc.lookup_pair(job_a.id, job_b.id, other_user.id)
        assert result is None


# ---------------------------------------------------------------------------
# pending review tests
# ---------------------------------------------------------------------------


class TestPendingReviews:
    @pytest.mark.asyncio
    async def test_pending_reviews_are_user_scoped(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session, "owner")
        other_user = await _create_user(db_session, "other")

        user_a = await _create_job(db_session, "Software Engineer", "Acme", user.id)
        user_b = await _create_job(db_session, "Senior Engineer", "Acme LLC", user.id)
        other_a = await _create_job(db_session, "Data Analyst", "OtherCo", other_user.id)
        other_b = await _create_job(db_session, "Business Analyst", "OtherCo Inc", other_user.id)

        svc = DedupFeedbackService(db_session)
        reviews = await svc.get_pending_reviews(user.id, limit=10)

        user_pairs = {frozenset((item.job_a_id, item.job_b_id)) for item in reviews}
        assert frozenset((user_a.id, user_b.id)) in user_pairs
        assert frozenset((other_a.id, other_b.id)) not in user_pairs


# ---------------------------------------------------------------------------
# accuracy_stats tests
# ---------------------------------------------------------------------------


class TestAccuracyStats:
    @pytest.mark.asyncio
    async def test_empty_stats(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        svc = DedupFeedbackService(db_session)
        stats = await svc.get_accuracy_stats(user.id)

        assert stats.total_feedback == 0
        assert stats.confirmed_duplicates == 0
        assert stats.confirmed_different == 0
        assert stats.system_precision is None
        assert stats.system_recall is None

    @pytest.mark.asyncio
    async def test_stats_with_feedback(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        other_user = await _create_user(db_session, "other")

        # Create several job pairs with varying similarity
        pairs = []
        for i in range(12):
            a = await _create_job(db_session, f"Role {i}a", f"Company {i}", user.id)
            b = await _create_job(db_session, f"Role {i}b", f"Company {i}", user.id)
            pairs.append((a, b))

        svc = DedupFeedbackService(db_session)

        # Record some as same, some as different
        for i in range(6):
            await svc.record_feedback(pairs[i][0].id, pairs[i][1].id, "same", user.id)
        for i in range(6, 12):
            await svc.record_feedback(pairs[i][0].id, pairs[i][1].id, "different", user.id)

        other_a = await _create_job(db_session, "Other Role A", "Other Co", other_user.id)
        other_b = await _create_job(db_session, "Other Role B", "Other Co", other_user.id)
        await svc.record_feedback(other_a.id, other_b.id, "same", other_user.id)

        stats = await svc.get_accuracy_stats(user.id)
        assert stats.total_feedback == 12
        assert stats.confirmed_duplicates == 6
        assert stats.confirmed_different == 6


# ---------------------------------------------------------------------------
# adjust_thresholds tests
# ---------------------------------------------------------------------------


class TestAdjustThresholds:
    @pytest.mark.asyncio
    async def test_insufficient_data(self, db_session: AsyncSession) -> None:
        svc = DedupFeedbackService(db_session)
        result = await svc.adjust_thresholds()

        assert result["status"] == "insufficient_data"
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_with_enough_data(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)

        svc = DedupFeedbackService(db_session)

        # Create 10+ pairs
        for i in range(12):
            a = await _create_job(db_session, f"Adj {i}a", f"Corp {i}", user.id)
            b = await _create_job(db_session, f"Adj {i}b", f"Corp {i}", user.id)
            decision = "same" if i < 6 else "different"
            await svc.record_feedback(a.id, b.id, decision, user.id)

        result = await svc.adjust_thresholds()
        assert result["status"] == "ok"
        assert result["count"] == 12
        assert "suggested_thresholds" in result
        assert "title_similarity" in result["suggested_thresholds"]


# ---------------------------------------------------------------------------
# check_feedback_override tests
# ---------------------------------------------------------------------------


class TestCheckFeedbackOverride:
    def test_override_exists_same(self) -> None:
        lookup = {("aaa", "bbb"): True}
        assert check_feedback_override(lookup, "aaa", "bbb") is True

    def test_override_exists_different(self) -> None:
        lookup = {("aaa", "bbb"): False}
        assert check_feedback_override(lookup, "aaa", "bbb") is False

    def test_override_reversed_order(self) -> None:
        lookup = {("aaa", "bbb"): True}
        # Function uses sorted ordering
        assert check_feedback_override(lookup, "bbb", "aaa") is True

    def test_no_override(self) -> None:
        lookup = {("aaa", "bbb"): True}
        assert check_feedback_override(lookup, "xxx", "yyy") is None

    def test_empty_lookup(self) -> None:
        assert check_feedback_override({}, "a", "b") is None


# ---------------------------------------------------------------------------
# _string_similarity tests
# ---------------------------------------------------------------------------


class TestStringSimilarity:
    def test_identical(self) -> None:
        assert _string_similarity("hello", "hello") == 1.0

    def test_completely_different(self) -> None:
        sim = _string_similarity("abcdef", "zyxwvu")
        assert sim < 0.3

    def test_empty_strings(self) -> None:
        assert _string_similarity("", "") == 1.0

    def test_one_empty(self) -> None:
        assert _string_similarity("hello", "") == 0.0

    def test_case_insensitive(self) -> None:
        assert _string_similarity("Hello", "hello") == 1.0

    def test_partial_match(self) -> None:
        sim = _string_similarity("Software Engineer", "Software Developer")
        assert 0.5 < sim < 1.0


# ---------------------------------------------------------------------------
# DeduplicationService with feedback_overrides
# ---------------------------------------------------------------------------


class TestDeduplicationWithFeedback:
    def test_default_no_overrides(self) -> None:
        svc = DeduplicationService()
        assert svc._feedback_overrides == {}

    def test_accepts_overrides(self) -> None:
        overrides = {("a", "b"): True}
        svc = DeduplicationService(feedback_overrides=overrides)
        assert svc._feedback_overrides == overrides

    def test_basic_dedup_still_works(self) -> None:
        svc = DeduplicationService()
        jobs = [
            ScrapedJob(title="Engineer", company_name="Co", source="test"),
            ScrapedJob(title="Engineer", company_name="Co", source="test"),
        ]
        result = svc.deduplicate(jobs)
        assert len(result) == 1
