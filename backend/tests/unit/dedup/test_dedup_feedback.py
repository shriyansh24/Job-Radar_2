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
from app.shared.errors import NotFoundError

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
        user_id=user_id,
        title=title,
        company_name=company,
        source="test",
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

    @pytest.mark.asyncio
    async def test_record_feedback_rejects_jobs_outside_current_workspace(
        self,
        db_session: AsyncSession,
    ) -> None:
        owner = await _create_user(db_session, "-owner")
        other = await _create_user(db_session, "-other")
        owned_job = await _create_job(db_session, "Owned", "Co A", owner.id)
        foreign_job = await _create_job(db_session, "Foreign", "Co B", other.id)

        svc = DedupFeedbackService(db_session)

        with pytest.raises(NotFoundError, match="current workspace"):
            await svc.record_feedback(owned_job.id, foreign_job.id, "same", owner.id)


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

        result = await svc.lookup_pair(job_a.id, job_b.id, user_id=user.id)
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
        result = await svc.lookup_pair(job_b.id, job_a.id, user_id=user.id)
        assert result is not None
        assert result.is_duplicate is False

    @pytest.mark.asyncio
    async def test_lookup_nonexistent(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        svc = DedupFeedbackService(db_session)
        result = await svc.lookup_pair(
            "nonexistent_a",
            "nonexistent_b",
            user_id=user.id,
        )
        assert result is None


# ---------------------------------------------------------------------------
# accuracy_stats tests
# ---------------------------------------------------------------------------


class TestAccuracyStats:
    @pytest.mark.asyncio
    async def test_empty_stats(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        svc = DedupFeedbackService(db_session)
        stats = await svc.get_accuracy_stats(user_id=user.id)

        assert stats.total_feedback == 0
        assert stats.confirmed_duplicates == 0
        assert stats.confirmed_different == 0
        assert stats.system_precision is None
        assert stats.system_recall is None

    @pytest.mark.asyncio
    async def test_stats_with_feedback(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)

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

        stats = await svc.get_accuracy_stats(user_id=user.id)
        assert stats.total_feedback == 12
        assert stats.confirmed_duplicates == 6
        assert stats.confirmed_different == 6

    @pytest.mark.asyncio
    async def test_accuracy_stats_are_scoped_to_current_user(
        self,
        db_session: AsyncSession,
    ) -> None:
        primary = await _create_user(db_session, "-primary")
        secondary = await _create_user(db_session, "-secondary")
        svc = DedupFeedbackService(db_session)

        primary_a = await _create_job(db_session, "Role A", "Company A", primary.id)
        primary_b = await _create_job(db_session, "Role B", "Company A", primary.id)
        secondary_a = await _create_job(db_session, "Role C", "Company B", secondary.id)
        secondary_b = await _create_job(db_session, "Role D", "Company B", secondary.id)

        await svc.record_feedback(primary_a.id, primary_b.id, "same", primary.id)
        await svc.record_feedback(secondary_a.id, secondary_b.id, "different", secondary.id)

        primary_stats = await svc.get_accuracy_stats(user_id=primary.id)
        secondary_stats = await svc.get_accuracy_stats(user_id=secondary.id)

        assert primary_stats.total_feedback == 1
        assert primary_stats.confirmed_duplicates == 1
        assert primary_stats.confirmed_different == 0
        assert secondary_stats.total_feedback == 1
        assert secondary_stats.confirmed_duplicates == 0
        assert secondary_stats.confirmed_different == 1


class TestPendingReviews:
    @pytest.mark.asyncio
    async def test_pending_reviews_are_scoped_to_current_user(
        self,
        db_session: AsyncSession,
    ) -> None:
        primary = await _create_user(db_session, "-primary")
        secondary = await _create_user(db_session, "-secondary")
        svc = DedupFeedbackService(db_session)

        own_a = await _create_job(db_session, "Backend Engineer", "Acme", primary.id)
        own_b = await _create_job(db_session, "Backend Developer", "Acme Corp", primary.id)
        await _create_job(db_session, "Data Analyst", "Globex", secondary.id)
        await _create_job(db_session, "Data Scientist", "Globex Corp", secondary.id)

        pending = await svc.get_pending_reviews(user_id=primary.id, limit=10)

        assert pending
        pair_ids = {(item.job_a_id, item.job_b_id) for item in pending}
        assert any({own_a.id, own_b.id} == {job_a_id, job_b_id} for job_a_id, job_b_id in pair_ids)
        assert all(own_a.id in pair or own_b.id in pair for pair in pair_ids)


# ---------------------------------------------------------------------------
# adjust_thresholds tests
# ---------------------------------------------------------------------------


class TestAdjustThresholds:
    @pytest.mark.asyncio
    async def test_insufficient_data(self, db_session: AsyncSession) -> None:
        user = await _create_user(db_session)
        svc = DedupFeedbackService(db_session)
        result = await svc.adjust_thresholds(user_id=user.id)

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

        result = await svc.adjust_thresholds(user_id=user.id)
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
