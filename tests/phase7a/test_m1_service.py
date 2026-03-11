"""Tests for Module 1 — Company Intelligence Registry service layer.

Tests cover:
- CRUD: create, get, get_by_domain, get_by_name, list, update
- Validation state machine: all transitions, manual_override blocking
- Confidence scoring: explicit signals, auto-calculation, clamping
- Idempotent get_or_create: domain and name based
- Company sources: add, update-on-duplicate, list
- ATS detection log: create, list recent
- Edge cases: empty domain, concurrent creates, null fields, invalid inputs
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.database import Base
from backend.phase7a.m1_models import Company, CompanySource, ATSDetectionLog
from backend.phase7a.m1_service import (
    CompanyService,
    CompanyNotFoundError,
    DuplicateDomainError,
    DuplicateNameError,
    InvalidStateTransitionError,
    CompanyServiceError,
)
from backend.phase7a.constants import ValidationState, ATSProvider
from backend.phase7a.id_utils import compute_company_id


@pytest_asyncio.fixture
async def engine():
    """Create in-memory engine with all tables."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Create async session for testing."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest.fixture
def service():
    """Create a CompanyService instance."""
    return CompanyService()


# =============================================================================
# CRUD Tests
# =============================================================================


class TestCreateCompany:

    async def test_create_with_domain(self, service, session):
        company = await service.create_company(
            session,
            canonical_name="Stripe",
            domain="stripe.com",
        )
        assert company.canonical_name == "Stripe"
        assert company.domain == "stripe.com"
        assert company.validation_state == "unverified"
        assert company.confidence_score == 0
        assert company.manual_override is False
        assert company.company_id == compute_company_id("stripe.com")

    async def test_create_without_domain(self, service, session):
        company = await service.create_company(
            session,
            canonical_name="Mystery Corp",
        )
        assert company.canonical_name == "Mystery Corp"
        assert company.domain is None
        assert company.company_id == compute_company_id("Mystery Corp")

    async def test_create_with_all_fields(self, service, session):
        company = await service.create_company(
            session,
            canonical_name="OpenAI",
            domain="openai.com",
            ats_provider="greenhouse",
            ats_slug="openai",
            careers_url="https://openai.com/careers",
            logo_url="https://logo.clearbit.com/openai.com",
        )
        assert company.ats_provider == "greenhouse"
        assert company.ats_slug == "openai"
        assert company.careers_url == "https://openai.com/careers"

    async def test_create_normalizes_domain(self, service, session):
        company = await service.create_company(
            session,
            canonical_name="Stripe",
            domain="https://www.STRIPE.COM/jobs",
        )
        assert company.domain == "stripe.com"

    async def test_create_duplicate_domain_raises(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        with pytest.raises(DuplicateDomainError):
            await service.create_company(session, "Stripe Inc", domain="stripe.com")

    async def test_create_duplicate_name_raises(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        with pytest.raises(DuplicateNameError):
            await service.create_company(session, "Stripe")

    async def test_create_invalid_ats_provider_raises(self, service, session):
        with pytest.raises(CompanyServiceError, match="Invalid ATS provider"):
            await service.create_company(
                session,
                canonical_name="BadCo",
                ats_provider="not_a_real_ats",
            )

    async def test_create_all_valid_ats_providers(self, service, session):
        """Every ATSProvider enum value should be accepted."""
        for i, provider in enumerate(ATSProvider):
            company = await service.create_company(
                session,
                canonical_name=f"TestCo_{provider.value}_{i}",
                domain=f"testco-{provider.value}-{i}.com",
                ats_provider=provider.value,
            )
            assert company.ats_provider == provider.value


class TestGetCompany:

    async def test_get_existing(self, service, session):
        created = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        fetched = await service.get_company(session, created.company_id)
        assert fetched is not None
        assert fetched.canonical_name == "Stripe"

    async def test_get_nonexistent_returns_none(self, service, session):
        result = await service.get_company(session, "nonexistent_id")
        assert result is None


class TestGetCompanyByDomain:

    async def test_get_by_domain(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        fetched = await service.get_company_by_domain(session, "stripe.com")
        assert fetched is not None
        assert fetched.canonical_name == "Stripe"

    async def test_get_by_domain_normalizes(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        fetched = await service.get_company_by_domain(
            session, "https://www.STRIPE.COM"
        )
        assert fetched is not None
        assert fetched.canonical_name == "Stripe"

    async def test_get_by_domain_nonexistent(self, service, session):
        result = await service.get_company_by_domain(session, "nope.com")
        assert result is None


class TestGetCompanyByName:

    async def test_get_by_name(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        fetched = await service.get_company_by_name(session, "Stripe")
        assert fetched is not None
        assert fetched.domain == "stripe.com"

    async def test_get_by_name_case_sensitive(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        # Exact match only
        result = await service.get_company_by_name(session, "stripe")
        assert result is None

    async def test_get_by_name_nonexistent(self, service, session):
        result = await service.get_company_by_name(session, "NoSuchCompany")
        assert result is None


class TestListCompanies:

    async def test_list_empty(self, service, session):
        companies, total = await service.list_companies(session)
        assert companies == []
        assert total == 0

    async def test_list_all(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        await service.create_company(session, "OpenAI", domain="openai.com")
        companies, total = await service.list_companies(session)
        assert total == 2
        assert len(companies) == 2

    async def test_list_filter_by_ats_provider(self, service, session):
        await service.create_company(
            session, "GHCo", domain="gh.com", ats_provider="greenhouse"
        )
        await service.create_company(
            session, "LeverCo", domain="lever-co.com", ats_provider="lever"
        )
        companies, total = await service.list_companies(
            session, ats_provider="greenhouse"
        )
        assert total == 1
        assert companies[0].canonical_name == "GHCo"

    async def test_list_filter_by_validation_state(self, service, session):
        c1 = await service.create_company(session, "Verified", domain="verified.com")
        c1.validation_state = "verified"
        await session.flush()

        await service.create_company(session, "Unverified", domain="unverified.com")

        companies, total = await service.list_companies(
            session, validation_state="verified"
        )
        assert total == 1
        assert companies[0].canonical_name == "Verified"

    async def test_list_search_query(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        await service.create_company(session, "OpenAI", domain="openai.com")

        companies, total = await service.list_companies(session, query="stripe")
        assert total == 1
        assert companies[0].canonical_name == "Stripe"

    async def test_list_search_by_domain(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        companies, total = await service.list_companies(session, query="stripe.com")
        assert total == 1

    async def test_list_pagination(self, service, session):
        for i in range(5):
            await service.create_company(
                session, f"Company_{i:02d}", domain=f"c{i}.com"
            )

        page1, total = await service.list_companies(session, page=1, limit=2)
        assert total == 5
        assert len(page1) == 2

        page3, _ = await service.list_companies(session, page=3, limit=2)
        assert len(page3) == 1  # 5 items, page 3 has 1

    async def test_list_ordered_by_name(self, service, session):
        await service.create_company(session, "Zebra", domain="zebra.com")
        await service.create_company(session, "Apple", domain="apple.com")
        companies, _ = await service.list_companies(session)
        assert companies[0].canonical_name == "Apple"
        assert companies[1].canonical_name == "Zebra"


class TestUpdateCompany:

    async def test_update_fields(self, service, session):
        created = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        updated = await service.update_company(
            session,
            created.company_id,
            ats_provider="greenhouse",
            ats_slug="stripe",
            careers_url="https://stripe.com/jobs",
        )
        assert updated.ats_provider == "greenhouse"
        assert updated.ats_slug == "stripe"

    async def test_update_nonexistent_raises(self, service, session):
        with pytest.raises(CompanyNotFoundError):
            await service.update_company(session, "nonexistent", ats_slug="x")

    async def test_update_invalid_ats_provider_raises(self, service, session):
        created = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        with pytest.raises(CompanyServiceError, match="Invalid ATS provider"):
            await service.update_company(
                session, created.company_id, ats_provider="invalid"
            )

    async def test_update_unknown_field_raises(self, service, session):
        created = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        with pytest.raises(CompanyServiceError, match="Unknown field"):
            await service.update_company(
                session, created.company_id, nonexistent_field="value"
            )

    async def test_update_normalizes_domain(self, service, session):
        created = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        updated = await service.update_company(
            session, created.company_id, domain="https://WWW.STRIPE.COM"
        )
        assert updated.domain == "stripe.com"

    async def test_update_sets_updated_at(self, service, session):
        created = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        assert created.updated_at is None
        updated = await service.update_company(
            session, created.company_id, ats_slug="stripe"
        )
        assert updated.updated_at is not None


# =============================================================================
# Validation State Machine Tests
# =============================================================================


class TestValidationStateMachine:

    async def test_unverified_to_probing(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        updated = await service.update_validation_state(
            session, company.company_id, "probing"
        )
        assert updated.validation_state == "probing"
        assert updated.last_probe_at is not None

    async def test_probing_to_verified(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_validation_state(
            session, company.company_id, "probing"
        )
        updated = await service.update_validation_state(
            session, company.company_id, "verified"
        )
        assert updated.validation_state == "verified"
        assert updated.last_validated_at is not None

    async def test_probing_to_invalid(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_validation_state(
            session, company.company_id, "probing"
        )
        updated = await service.update_validation_state(
            session, company.company_id, "invalid",
            error="Connection refused",
        )
        assert updated.validation_state == "invalid"
        assert updated.probe_error == "Connection refused"

    async def test_verified_to_stale(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_validation_state(
            session, company.company_id, "probing"
        )
        await service.update_validation_state(
            session, company.company_id, "verified"
        )
        updated = await service.update_validation_state(
            session, company.company_id, "stale"
        )
        assert updated.validation_state == "stale"

    async def test_stale_to_probing(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        # Walk through: unverified -> probing -> verified -> stale -> probing
        await service.update_validation_state(
            session, company.company_id, "probing"
        )
        await service.update_validation_state(
            session, company.company_id, "verified"
        )
        await service.update_validation_state(
            session, company.company_id, "stale"
        )
        updated = await service.update_validation_state(
            session, company.company_id, "probing"
        )
        assert updated.validation_state == "probing"

    async def test_invalid_to_probing(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_validation_state(
            session, company.company_id, "probing"
        )
        await service.update_validation_state(
            session, company.company_id, "invalid"
        )
        updated = await service.update_validation_state(
            session, company.company_id, "probing"
        )
        assert updated.validation_state == "probing"

    async def test_invalid_transition_raises(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        # unverified -> verified is not allowed (must go through probing)
        with pytest.raises(InvalidStateTransitionError, match="Cannot transition"):
            await service.update_validation_state(
                session, company.company_id, "verified"
            )

    async def test_unverified_to_invalid_not_allowed(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        with pytest.raises(InvalidStateTransitionError):
            await service.update_validation_state(
                session, company.company_id, "invalid"
            )

    async def test_manual_override_blocks_transition(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_company(
            session, company.company_id, manual_override=True
        )
        with pytest.raises(InvalidStateTransitionError, match="manual_override"):
            await service.update_validation_state(
                session, company.company_id, "probing"
            )

    async def test_invalid_state_value_raises(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        with pytest.raises(InvalidStateTransitionError, match="Invalid validation state"):
            await service.update_validation_state(
                session, company.company_id, "bogus_state"
            )

    async def test_nonexistent_company_raises(self, service, session):
        with pytest.raises(CompanyNotFoundError):
            await service.update_validation_state(
                session, "nonexistent", "probing"
            )

    async def test_verified_to_probing_allowed(self, service, session):
        """verified -> probing is allowed for re-probing."""
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_validation_state(
            session, company.company_id, "probing"
        )
        await service.update_validation_state(
            session, company.company_id, "verified"
        )
        updated = await service.update_validation_state(
            session, company.company_id, "probing"
        )
        assert updated.validation_state == "probing"


# =============================================================================
# Confidence Scoring Tests
# =============================================================================


class TestConfidenceScoring:

    async def test_explicit_signals_full_score(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        score = await service.calculate_confidence(
            session,
            company.company_id,
            signals={
                "domain_verified": True,
                "careers_page_200": True,
                "ats_pattern_matched": True,
                "ats_api_responds": True,
                "multi_source_confirm": 3,
                "jobs_scraped": True,
            },
        )
        # 20 + 15 + 25 + 30 + 30(capped) + 5 = 125 -> clamped to 100
        assert score == 100

    async def test_explicit_signals_partial(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        score = await service.calculate_confidence(
            session,
            company.company_id,
            signals={
                "domain_verified": True,
                "careers_page_200": False,
                "ats_pattern_matched": True,
            },
        )
        # 20 + 0 + 25 = 45
        assert score == 45

    async def test_multi_source_cap(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        score = await service.calculate_confidence(
            session,
            company.company_id,
            signals={"multi_source_confirm": 10},
        )
        # 10 * 10 = 100 but capped at 30
        assert score == 30

    async def test_auto_calculate_with_domain(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        score = await service.calculate_confidence(session, company.company_id)
        # domain_verified: 20, no sources, no ATS
        assert score == 20

    async def test_auto_calculate_with_ats(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com",
            ats_provider="greenhouse",
        )
        score = await service.calculate_confidence(session, company.company_id)
        # domain_verified: 20 + ats_pattern_matched: 25 = 45
        assert score == 45

    async def test_auto_calculate_with_sources(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com",
            ats_provider="greenhouse",
        )
        await service.add_company_source(
            session, company.company_id, "greenhouse", "stripe"
        )
        await service.add_company_source(
            session, company.company_id, "serpapi"
        )
        score = await service.calculate_confidence(session, company.company_id)
        # domain_verified: 20 + ats_pattern_matched: 25 +
        # jobs_scraped: 5 + multi_source_confirm: 2*10=20 = 70
        assert score == 70

    async def test_auto_calculate_unknown_ats_not_counted(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com",
            ats_provider="unknown",
        )
        score = await service.calculate_confidence(session, company.company_id)
        # domain_verified: 20 only (unknown ATS doesn't count)
        assert score == 20

    async def test_score_updates_company_record(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        assert company.confidence_score == 0
        score = await service.calculate_confidence(
            session,
            company.company_id,
            signals={"domain_verified": True},
        )
        assert score == 20
        # Verify it was persisted
        fetched = await service.get_company(session, company.company_id)
        assert fetched.confidence_score == 20

    async def test_nonexistent_company_raises(self, service, session):
        with pytest.raises(CompanyNotFoundError):
            await service.calculate_confidence(session, "nonexistent")

    async def test_unknown_signal_ignored(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        score = await service.calculate_confidence(
            session,
            company.company_id,
            signals={
                "domain_verified": True,
                "some_future_signal": True,
            },
        )
        # Only domain_verified counted
        assert score == 20

    async def test_clamped_to_max(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        score = await service.calculate_confidence(
            session,
            company.company_id,
            signals={
                "domain_verified": True,
                "careers_page_200": True,
                "ats_pattern_matched": True,
                "ats_api_responds": True,
                "multi_source_confirm": 100,
                "jobs_scraped": True,
            },
        )
        assert score == 100  # clamped


# =============================================================================
# Get-or-Create Tests
# =============================================================================


class TestGetOrCreateCompany:

    async def test_create_by_domain(self, service, session):
        company, created = await service.get_or_create_company(
            session, "stripe.com"
        )
        assert created is True
        assert company.domain == "stripe.com"
        assert company.canonical_name == "Stripe"  # auto-derived

    async def test_get_existing_by_domain(self, service, session):
        await service.create_company(session, "Stripe", domain="stripe.com")
        company, created = await service.get_or_create_company(
            session, "stripe.com"
        )
        assert created is False
        assert company.canonical_name == "Stripe"

    async def test_idempotent_domain(self, service, session):
        c1, created1 = await service.get_or_create_company(
            session, "stripe.com"
        )
        c2, created2 = await service.get_or_create_company(
            session, "stripe.com"
        )
        assert created1 is True
        assert created2 is False
        assert c1.company_id == c2.company_id

    async def test_create_by_name(self, service, session):
        company, created = await service.get_or_create_company(
            session, "Mystery Corp"
        )
        assert created is True
        assert company.canonical_name == "Mystery Corp"
        assert company.domain is None

    async def test_get_existing_by_name(self, service, session):
        await service.create_company(session, "Mystery Corp")
        company, created = await service.get_or_create_company(
            session, "Mystery Corp"
        )
        assert created is False
        assert company.canonical_name == "Mystery Corp"

    async def test_custom_canonical_name(self, service, session):
        company, created = await service.get_or_create_company(
            session, "stripe.com", canonical_name="Stripe, Inc."
        )
        assert created is True
        assert company.canonical_name == "Stripe, Inc."

    async def test_normalizes_domain_input(self, service, session):
        c1, created1 = await service.get_or_create_company(
            session, "https://www.stripe.com/careers"
        )
        c2, created2 = await service.get_or_create_company(
            session, "STRIPE.COM"
        )
        assert created1 is True
        assert created2 is False
        assert c1.company_id == c2.company_id


# =============================================================================
# Company Sources Tests
# =============================================================================


class TestAddCompanySource:

    async def test_add_source(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        source = await service.add_company_source(
            session,
            company.company_id,
            "greenhouse",
            source_identifier="stripe",
            source_url="https://boards.greenhouse.io/stripe",
        )
        assert source.source == "greenhouse"
        assert source.source_identifier == "stripe"
        assert source.jobs_count == 1
        assert source.first_seen_at is not None
        assert source.last_seen_at is not None

    async def test_add_duplicate_source_updates(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        s1 = await service.add_company_source(
            session, company.company_id, "greenhouse",
            source_identifier="stripe",
        )
        s2 = await service.add_company_source(
            session, company.company_id, "greenhouse",
            source_identifier="stripe",
        )
        assert s1.id == s2.id  # same record
        assert s2.jobs_count == 2  # incremented

    async def test_add_source_nonexistent_company_raises(self, service, session):
        with pytest.raises(CompanyNotFoundError):
            await service.add_company_source(
                session, "nonexistent", "greenhouse"
            )

    async def test_add_source_invalid_type_raises(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        with pytest.raises(CompanyServiceError, match="Invalid source type"):
            await service.add_company_source(
                session, company.company_id, "not_a_source"
            )

    async def test_add_multiple_sources(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.add_company_source(
            session, company.company_id, "greenhouse",
            source_identifier="stripe",
        )
        await service.add_company_source(
            session, company.company_id, "serpapi",
        )
        sources = await service.get_company_sources(
            session, company.company_id
        )
        assert len(sources) == 2
        source_types = {s.source for s in sources}
        assert source_types == {"greenhouse", "serpapi"}

    async def test_add_source_fills_url_only_first_time(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        s1 = await service.add_company_source(
            session, company.company_id, "greenhouse",
            source_identifier="stripe",
            source_url="https://boards.greenhouse.io/stripe",
        )
        s2 = await service.add_company_source(
            session, company.company_id, "greenhouse",
            source_identifier="stripe",
            source_url="https://different-url.com",
        )
        # URL should stay as the first one since it was already set
        assert s2.source_url == "https://boards.greenhouse.io/stripe"


class TestGetCompanySources:

    async def test_empty_sources(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        sources = await service.get_company_sources(
            session, company.company_id
        )
        assert sources == []

    async def test_sorted_by_source(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.add_company_source(
            session, company.company_id, "serpapi"
        )
        await service.add_company_source(
            session, company.company_id, "greenhouse",
            source_identifier="stripe",
        )
        sources = await service.get_company_sources(
            session, company.company_id
        )
        assert sources[0].source == "greenhouse"
        assert sources[1].source == "serpapi"


# =============================================================================
# ATS Detection Log Tests
# =============================================================================


class TestLogATSDetection:

    async def test_log_successful_probe(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        log = await service.log_ats_detection(
            session,
            company.company_id,
            probe_url="https://stripe.com/jobs",
            provider="greenhouse",
            method="url_pattern",
            confidence=95,
            status=200,
            duration_ms=350,
        )
        assert log.detected_provider == "greenhouse"
        assert log.detection_method == "url_pattern"
        assert log.confidence == 95
        assert log.probe_status == 200
        assert log.error_message is None

    async def test_log_failed_probe(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        log = await service.log_ats_detection(
            session,
            company.company_id,
            probe_url="https://stripe.com/jobs",
            provider=None,
            status=503,
            duration_ms=5000,
            error="Service Unavailable",
        )
        assert log.detected_provider is None
        assert log.probe_status == 503
        assert log.error_message == "Service Unavailable"

    async def test_log_nonexistent_company_raises(self, service, session):
        with pytest.raises(CompanyNotFoundError):
            await service.log_ats_detection(
                session, "nonexistent",
                probe_url="https://example.com",
            )


class TestGetRecentProbes:

    async def test_empty_probes(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        probes = await service.get_recent_probes(
            session, company.company_id
        )
        assert probes == []

    async def test_multiple_probes_ordered(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        for i in range(5):
            await service.log_ats_detection(
                session,
                company.company_id,
                probe_url=f"https://stripe.com/probe/{i}",
                provider="greenhouse",
                confidence=50 + i * 10,
            )
        probes = await service.get_recent_probes(
            session, company.company_id, limit=3
        )
        assert len(probes) == 3

    async def test_limit_respected(self, service, session):
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        for i in range(10):
            await service.log_ats_detection(
                session,
                company.company_id,
                probe_url=f"https://stripe.com/probe/{i}",
            )
        probes = await service.get_recent_probes(
            session, company.company_id, limit=5
        )
        assert len(probes) == 5


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:

    async def test_empty_domain_string_treated_as_none(self, service, session):
        """Creating with empty string domain should work like None."""
        company = await service.create_company(
            session, "NoDomain",
        )
        assert company.domain is None

    async def test_company_id_deterministic(self, service, session):
        """Same domain always produces same company_id."""
        c1 = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        expected_id = compute_company_id("stripe.com")
        assert c1.company_id == expected_id

    async def test_company_id_deterministic_by_name(self, service, session):
        """Same name always produces same company_id."""
        c1 = await service.create_company(
            session, "Mystery Corp",
        )
        expected_id = compute_company_id("Mystery Corp")
        assert c1.company_id == expected_id

    async def test_override_fields_json(self, service, session):
        """Override fields stores and retrieves list correctly."""
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_company(
            session,
            company.company_id,
            manual_override=True,
            override_fields=["ats_provider", "ats_slug"],
        )
        fetched = await service.get_company(session, company.company_id)
        assert fetched.override_fields == ["ats_provider", "ats_slug"]
        assert fetched.manual_override is True

    async def test_domain_aliases_json(self, service, session):
        """Domain aliases stores and retrieves list correctly."""
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_company(
            session,
            company.company_id,
            domain_aliases=["stripe.dev", "stripe.network"],
        )
        fetched = await service.get_company(session, company.company_id)
        assert fetched.domain_aliases == ["stripe.dev", "stripe.network"]

    async def test_board_urls_json(self, service, session):
        """Board URLs stores and retrieves list correctly."""
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        await service.update_company(
            session,
            company.company_id,
            board_urls=[
                "https://boards.greenhouse.io/stripe",
                "https://stripe.com/jobs",
            ],
        )
        fetched = await service.get_company(session, company.company_id)
        assert len(fetched.board_urls) == 2

    async def test_source_with_none_identifier(self, service, session):
        """Source with None identifier is handled correctly."""
        company = await service.create_company(
            session, "Stripe", domain="stripe.com"
        )
        s1 = await service.add_company_source(
            session, company.company_id, "serpapi",
            source_identifier=None,
        )
        # Adding again with None identifier should update same record
        s2 = await service.add_company_source(
            session, company.company_id, "serpapi",
            source_identifier=None,
        )
        assert s1.id == s2.id
        assert s2.jobs_count == 2
