from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auto_apply.field_mapper import FieldMapper
from app.auto_apply.form_learning import FormLearningService, _label_hash

# ---------------------------------------------------------------------------
# FormLearningService tests
# ---------------------------------------------------------------------------


class TestRecordMapping:
    @pytest.mark.asyncio
    async def test_creates_new_mapping(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        rule = await svc.record_mapping("greenhouse", "First Name", "first_name")
        assert rule.ats_provider == "greenhouse"
        assert rule.semantic_key == "first_name"
        assert rule.times_seen == 1
        assert rule.confidence == 0.8

    @pytest.mark.asyncio
    async def test_upsert_increments_times_seen(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        await svc.record_mapping("greenhouse", "First Name", "first_name")
        rule = await svc.record_mapping("greenhouse", "First Name", "first_name")
        assert rule.times_seen == 2
        # Confidence should have been bumped
        assert rule.confidence > 0.8

    @pytest.mark.asyncio
    async def test_user_confirmed_boosts_confidence(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        await svc.record_mapping("lever", "Compensation", "salary_expectation")
        rule = await svc.record_mapping(
            "lever", "Compensation", "salary_expectation", source="user_confirmed"
        )
        assert rule.source == "user_confirmed"
        # user_confirmed adds +0.1 on top of the +0.02 increment
        assert rule.confidence > 0.9

    @pytest.mark.asyncio
    async def test_different_providers_are_separate(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        r1 = await svc.record_mapping("greenhouse", "Email", "email")
        r2 = await svc.record_mapping("lever", "Email", "email")
        assert r1.id != r2.id


class TestLookupMapping:
    @pytest.mark.asyncio
    async def test_returns_none_below_threshold(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        # Only recorded once, default min_times_seen=3
        await svc.record_mapping("greenhouse", "Email", "email")
        result = await svc.lookup_mapping("greenhouse", "Email")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_key_at_threshold(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        for _ in range(3):
            await svc.record_mapping("greenhouse", "Email", "email")
        result = await svc.lookup_mapping("greenhouse", "Email")
        assert result == "email"

    @pytest.mark.asyncio
    async def test_case_insensitive_label(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        for _ in range(3):
            await svc.record_mapping("lever", "  Email Address  ", "email")
        result = await svc.lookup_mapping("lever", "email address")
        assert result == "email"


class TestListAndDeleteMappings:
    @pytest.mark.asyncio
    async def test_list_mappings(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        await svc.record_mapping("greenhouse", "Email", "email")
        await svc.record_mapping("greenhouse", "Phone", "phone")
        items = await svc.list_mappings()
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_delete_mapping(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        rule = await svc.record_mapping("greenhouse", "Email", "email")
        assert await svc.delete_mapping(rule.id) is True
        items = await svc.list_mappings()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        assert await svc.delete_mapping(uuid.uuid4()) is False


# ---------------------------------------------------------------------------
# ApplicationDedup tests
# ---------------------------------------------------------------------------


class TestApplicationDedup:
    @pytest.mark.asyncio
    async def test_has_applied_false_initially(self, db_session: AsyncSession) -> None:
        svc = FormLearningService(db_session)
        user_id = uuid.uuid4()
        assert await svc.has_applied(user_id, "abc123") is False

    @pytest.mark.asyncio
    async def test_record_and_check(self, db_session: AsyncSession) -> None:
        # We need a real user and job for FK constraints in SQLite
        from app.auth.models import User
        from app.jobs.models import Job

        user = User(id=uuid.uuid4(), email="test@test.com", password_hash="x", is_active=True)
        db_session.add(user)

        job = Job(id="sha256_test_hash", title="Test Job", source="test")
        db_session.add(job)
        await db_session.flush()

        svc = FormLearningService(db_session)
        await svc.record_application(user.id, job.id, ats_provider="greenhouse", url="https://apply.com")

        assert await svc.has_applied(user.id, job.id) is True
        assert await svc.has_applied(user.id, "other_job") is False


# ---------------------------------------------------------------------------
# FieldMapper Tier 1 + Tier 2 integration tests
# ---------------------------------------------------------------------------


class TestFieldMapper:
    @pytest.mark.asyncio
    async def test_tier1_regex(self) -> None:
        mapper = FieldMapper()
        assert await mapper.classify("First Name") == "first_name"
        assert await mapper.classify("Email Address") == "email"
        assert await mapper.classify("Phone Number") == "phone"

    @pytest.mark.asyncio
    async def test_tier1_returns_none_for_unknown(self) -> None:
        mapper = FieldMapper()
        assert await mapper.classify("Favorite Color") is None

    @pytest.mark.asyncio
    async def test_tier2_db_lookup(self, db_session: AsyncSession) -> None:
        # Seed a learned mapping with enough observations
        svc = FormLearningService(db_session)
        for _ in range(3):
            await svc.record_mapping("greenhouse", "Favorite Color", "custom_field_1")

        mapper = FieldMapper(db=db_session, ats_provider="greenhouse")
        result = await mapper.classify("Favorite Color")
        assert result == "custom_field_1"

    @pytest.mark.asyncio
    async def test_tier2_skipped_without_db(self) -> None:
        mapper = FieldMapper(db=None, ats_provider="greenhouse")
        # Unknown label, no DB -> None
        assert await mapper.classify("Favorite Color") is None


class TestLabelHash:
    def test_consistent(self) -> None:
        assert _label_hash("Email") == _label_hash("email")
        assert _label_hash("  Email  ") == _label_hash("email")

    def test_different_labels(self) -> None:
        assert _label_hash("Email") != _label_hash("Phone")
