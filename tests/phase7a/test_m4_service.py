"""Tests for Module 4 Canonical Jobs Pipeline: Service layer.

Verifies CanonicalJobsService behavior including:
    - Raw job ingestion (new + update)
    - Canonical matching and merge
    - Multi-source merge precedence
    - Quality scoring
    - Stale/closed detection
    - Reactivation
    - Query methods
    - Edge cases (minimal data, duplicates, conflicts)
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.database import Base
from backend.phase7a.constants import (
    CANONICAL_CLOSED_DAYS,
    SOURCE_QUALITY_ORDER,
)
from backend.phase7a.id_utils import (
    compute_canonical_job_id,
    compute_company_id,
    compute_raw_job_id,
)
from backend.phase7a.m4_models import CanonicalJob, RawJobSource
from backend.phase7a.m4_service import CanonicalJobsService


@pytest_asyncio.fixture
async def m4_engine():
    """In-memory SQLite engine with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def m4_session(m4_engine):
    """Async session bound to the M4 test engine."""
    factory = async_sessionmaker(
        m4_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def service(m4_session):
    """CanonicalJobsService instance with test session."""
    return CanonicalJobsService(m4_session)


# Helper constants
_COMPANY_ID = compute_company_id("acme.com")
_COMPANY_NAME = "Acme Corp"


class TestRawJobIngestion:
    """Tests for ingest_raw_job: new record creation."""

    @pytest.mark.asyncio
    async def test_ingest_new_raw_job(self, service, m4_session):
        """Ingest a new raw job creates a raw_job_sources record."""
        raw, canonical, is_new = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-001",
            source_url="https://boards.greenhouse.io/acme/jobs/001",
            title_raw="ML Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="San Francisco, CA",
        )
        await m4_session.flush()

        assert raw is not None
        assert raw.raw_id == compute_raw_job_id("greenhouse", "gh-001")
        assert raw.source == "greenhouse"
        assert raw.scrape_count == 1
        assert raw.is_active is True

    @pytest.mark.asyncio
    async def test_ingest_new_raw_job_without_canonical_data(
        self, service, m4_session
    ):
        """Ingest without company_id should not create canonical record."""
        raw, canonical, is_new = await service.ingest_raw_job(
            source="serpapi",
            source_job_id="serp-001",
            title_raw="Data Scientist",
        )
        await m4_session.flush()

        assert raw is not None
        assert canonical is None
        assert is_new is False

    @pytest.mark.asyncio
    async def test_ingest_creates_canonical_when_data_available(
        self, service, m4_session
    ):
        """Ingest with full data should create a canonical job."""
        raw, canonical, is_new = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-can-001",
            source_url="https://boards.greenhouse.io/acme/jobs/001",
            title_raw="ML Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="San Francisco, CA",
            description_raw="Great ML role at Acme.",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert canonical is not None
        assert is_new is True
        assert canonical.title == "ML Engineer"
        assert canonical.company_id == _COMPANY_ID
        assert canonical.company_name == _COMPANY_NAME
        assert canonical.primary_source == "greenhouse"
        assert raw.canonical_job_id == canonical.canonical_job_id

    @pytest.mark.asyncio
    async def test_ingest_with_empty_location_creates_canonical(
        self, service, m4_session
    ):
        """Ingest with empty string location should still attempt canonical match."""
        raw, canonical, is_new = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-empty-loc",
            title_raw="Backend Developer",
            company_name_raw=_COMPANY_NAME,
            location_raw="",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert canonical is not None
        assert is_new is True

    @pytest.mark.asyncio
    async def test_ingest_with_raw_payload(self, service, m4_session):
        """Ingest preserves the raw payload JSON."""
        payload = {"id": 999, "custom_field": "value"}
        raw, _, _ = await service.ingest_raw_job(
            source="ashby",
            source_job_id="ash-payload",
            raw_payload=payload,
        )
        await m4_session.flush()

        assert raw.raw_payload == payload


class TestRawJobUpdate:
    """Tests for ingest_raw_job: updating existing records."""

    @pytest.mark.asyncio
    async def test_re_ingest_updates_existing(self, service, m4_session):
        """Re-ingesting the same raw job updates it instead of creating a new one."""
        # First ingest
        raw1, _, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-update-001",
            title_raw="ML Engineer",
            company_name_raw=_COMPANY_NAME,
        )
        await m4_session.flush()
        assert raw1.scrape_count == 1

        # Second ingest of same source+id
        raw2, _, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-update-001",
            title_raw="Senior ML Engineer",  # title changed
        )
        await m4_session.flush()

        assert raw2.raw_id == raw1.raw_id  # same record
        assert raw2.scrape_count == 2
        assert raw2.title_raw == "Senior ML Engineer"
        assert raw2.is_active is True

    @pytest.mark.asyncio
    async def test_re_ingest_preserves_none_fields(self, service, m4_session):
        """Re-ingest with None fields should not overwrite existing data."""
        # First ingest with description
        raw1, _, _ = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-preserve",
            title_raw="Engineer",
            description_raw="Original description.",
        )
        await m4_session.flush()
        assert raw1.description_raw == "Original description."

        # Second ingest without description (None)
        raw2, _, _ = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-preserve",
            title_raw="Senior Engineer",
            # description_raw not provided = None
        )
        await m4_session.flush()

        assert raw2.description_raw == "Original description."  # preserved
        assert raw2.title_raw == "Senior Engineer"  # updated

    @pytest.mark.asyncio
    async def test_re_ingest_reactivates(self, service, m4_session):
        """Re-ingesting sets is_active=True even if it was deactivated."""
        raw1, _, _ = await service.ingest_raw_job(
            source="ashby",
            source_job_id="ash-reactive",
            title_raw="Dev",
        )
        await m4_session.flush()

        # Manually deactivate
        raw1.is_active = False
        await m4_session.flush()

        # Re-ingest
        raw2, _, _ = await service.ingest_raw_job(
            source="ashby",
            source_job_id="ash-reactive",
        )
        await m4_session.flush()

        assert raw2.is_active is True
        assert raw2.scrape_count == 2


class TestCanonicalMatching:
    """Tests for canonical job matching and creation."""

    @pytest.mark.asyncio
    async def test_same_job_different_sources_matches(
        self, service, m4_session
    ):
        """Two raw sources for the same job should merge into one canonical."""
        # First source: greenhouse
        raw1, can1, is_new1 = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-match-001",
            title_raw="ML Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="San Francisco, CA",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert is_new1 is True
        canonical_id = can1.canonical_job_id

        # Second source: lever (same title, company, location)
        raw2, can2, is_new2 = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-match-001",
            title_raw="ML Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="San Francisco, CA",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert is_new2 is False  # matched existing
        assert can2.canonical_job_id == canonical_id
        assert raw1.canonical_job_id == canonical_id
        assert raw2.canonical_job_id == canonical_id

    @pytest.mark.asyncio
    async def test_different_jobs_create_different_canonicals(
        self, service, m4_session
    ):
        """Different titles at the same company create separate canonicals."""
        _, can1, new1 = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-diff-001",
            title_raw="ML Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="San Francisco, CA",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        _, can2, new2 = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-diff-002",
            title_raw="Data Scientist",
            company_name_raw=_COMPANY_NAME,
            location_raw="San Francisco, CA",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert new1 is True
        assert new2 is True
        assert can1.canonical_job_id != can2.canonical_job_id

    @pytest.mark.asyncio
    async def test_seniority_normalization_matches(self, service, m4_session):
        """'Senior ML Engineer' and 'ML Engineer' should match to same canonical
        because title normalization strips seniority prefixes."""
        _, can1, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-senior-001",
            title_raw="Senior ML Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        _, can2, is_new = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-senior-001",
            title_raw="ML Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        # These should match because normalize_title strips "Senior"
        assert can1.canonical_job_id == can2.canonical_job_id
        assert is_new is False


class TestMergePrecedence:
    """Tests for merge logic and source quality precedence."""

    @pytest.mark.asyncio
    async def test_better_source_updates_title(self, service, m4_session):
        """A higher-quality source should update the canonical title."""
        # Start with serpapi (lower quality)
        _, can1, _ = await service.ingest_raw_job(
            source="serpapi",
            source_job_id="serp-merge-001",
            title_raw="ML Eng",
            company_name_raw=_COMPANY_NAME,
            location_raw="SF, CA",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()
        assert can1.title == "ML Eng"
        assert can1.primary_source == "serpapi"

        # Merge with greenhouse (higher quality)
        _, can2, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-merge-001",
            title_raw="Machine Learning Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="SF, CA",
            source_url="https://boards.greenhouse.io/acme/jobs/001",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert can2.title == "Machine Learning Engineer"
        assert can2.primary_source == "greenhouse"

    @pytest.mark.asyncio
    async def test_worse_source_does_not_overwrite_title(
        self, service, m4_session
    ):
        """A lower-quality source should not overwrite an existing better title."""
        # Start with greenhouse (high quality)
        _, can1, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-noover-001",
            title_raw="Machine Learning Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="NYC",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        # Merge with jobspy (lower quality) — same normalized title
        _, can2, _ = await service.ingest_raw_job(
            source="jobspy",
            source_job_id="js-noover-001",
            title_raw="Machine Learning Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="NYC",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        # Title should remain from greenhouse (better source), primary_source unchanged
        assert can2.title == "Machine Learning Engineer"
        assert can2.primary_source == "greenhouse"

    @pytest.mark.asyncio
    async def test_ats_source_preferred_for_apply_url(
        self, service, m4_session
    ):
        """ATS source URLs are preferred for apply_url."""
        # Start with serpapi
        _, can1, _ = await service.ingest_raw_job(
            source="serpapi",
            source_job_id="serp-url-001",
            source_url="https://google.com/jobs/redirect",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()
        assert can1.apply_url == "https://google.com/jobs/redirect"

        # Merge with ATS source
        _, can2, _ = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-url-001",
            source_url="https://jobs.lever.co/acme/engineer",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        # ATS URL should replace the serpapi redirect
        assert can2.apply_url == "https://jobs.lever.co/acme/engineer"

    @pytest.mark.asyncio
    async def test_better_source_updates_description(
        self, service, m4_session
    ):
        """A better source with a longer description should update it."""
        _, can1, _ = await service.ingest_raw_job(
            source="jobspy",
            source_job_id="js-desc-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            description_raw="Short desc.",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()
        assert can1.description_markdown == "Short desc."

        _, can2, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-desc-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            description_raw="A much longer and more detailed job description with benefits and requirements.",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert "much longer" in can2.description_markdown

    @pytest.mark.asyncio
    async def test_source_count_increments(self, service, m4_session):
        """Each new source should increment source_count on the canonical job."""
        _, can1, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-count-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()
        assert can1.source_count == 1

        _, can2, _ = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-count-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()
        assert can2.source_count == 2

        _, can3, _ = await service.ingest_raw_job(
            source="serpapi",
            source_job_id="serp-count-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()
        assert can3.source_count == 3


class TestQualityScoring:
    """Tests for _calculate_quality_score."""

    @pytest.mark.asyncio
    async def test_minimal_job_score(self, service, m4_session):
        """A minimal job with only title + company should have a low score."""
        _, canonical, _ = await service.ingest_raw_job(
            source="jobspy",
            source_job_id="js-min-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        # title: +10, company_id: +10, source_count=1 (no bonus)
        # No salary, no description, no apply_url
        # jobspy is not ATS
        assert canonical.quality_score is not None
        assert canonical.quality_score >= 20

    @pytest.mark.asyncio
    async def test_full_job_score(self, service, m4_session):
        """A fully populated job from ATS should score high."""
        _, canonical, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-full-001",
            source_url="https://boards.greenhouse.io/acme/jobs/full",
            title_raw="ML Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="San Francisco, CA",
            description_raw="Full detailed description of the ML Engineer role.",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        # Manually set salary to test scoring
        canonical.salary_min = 150000
        canonical.salary_max = 200000
        canonical.quality_score = service._calculate_quality_score(canonical)
        await m4_session.flush()

        # title:10 + company_id:10 + location:10 + salary:15 +
        # description:15 + apply_url:10 + ATS:10 = 80
        assert canonical.quality_score >= 70

    @pytest.mark.asyncio
    async def test_multi_source_bonus(self, service, m4_session):
        """Multi-source jobs should get a quality bonus."""
        _, can, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-multi-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()
        score1 = can.quality_score

        _, can, _ = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-multi-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()
        score2 = can.quality_score

        assert score2 > score1  # Multi-source bonus applied

    def test_quality_score_capped_at_100(self, service):
        """Quality score should never exceed 100."""
        # Create a mock canonical job with everything
        from backend.phase7a.m4_models import CanonicalJob

        job = CanonicalJob(
            canonical_job_id="test",
            company_name="TestCo",
            company_id="a" * 64,
            title="Engineer",
            location_city="SF",
            location_raw="SF",
            remote_type="hybrid",
            salary_min=100000,
            salary_max=200000,
            description_markdown="Long description.",
            apply_url="https://example.com",
            source_count=10,  # big multi-source bonus
            primary_source="greenhouse",
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        score = service._calculate_quality_score(job)
        assert score <= 100


class TestStaleClosedDetection:
    """Tests for stale and closed job detection."""

    @pytest.mark.asyncio
    async def test_detect_stale_jobs(self, service, m4_session):
        """Jobs not seen for CLOSED_DAYS/2 should be detected as stale."""
        now = datetime.now(timezone.utc)
        stale_time = now - timedelta(days=CANONICAL_CLOSED_DAYS // 2 + 1)

        # Create a stale canonical job
        stale_id = compute_canonical_job_id(_COMPANY_ID, "Old Role", "Remote")
        stale_job = CanonicalJob(
            canonical_job_id=stale_id,
            company_id=_COMPANY_ID,
            company_name=_COMPANY_NAME,
            title="Old Role",
            title_normalized="old role",
            source_count=1,
            primary_source="greenhouse",
            first_seen_at=stale_time,
            last_seen_at=stale_time,
            is_active=True,
            created_at=stale_time,
        )
        m4_session.add(stale_job)
        await m4_session.flush()

        stale_ids = await service.detect_stale_jobs()
        assert stale_id in stale_ids

    @pytest.mark.asyncio
    async def test_recent_jobs_not_stale(self, service, m4_session):
        """Recently seen jobs should not be detected as stale."""
        now = datetime.now(timezone.utc)
        recent_id = compute_canonical_job_id(
            _COMPANY_ID, "Fresh Role", "Remote"
        )
        fresh_job = CanonicalJob(
            canonical_job_id=recent_id,
            company_id=_COMPANY_ID,
            company_name=_COMPANY_NAME,
            title="Fresh Role",
            title_normalized="fresh role",
            source_count=1,
            primary_source="greenhouse",
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            created_at=now,
        )
        m4_session.add(fresh_job)
        await m4_session.flush()

        stale_ids = await service.detect_stale_jobs()
        assert recent_id not in stale_ids

    @pytest.mark.asyncio
    async def test_detect_closed_jobs(self, service, m4_session):
        """Jobs not seen for CANONICAL_CLOSED_DAYS should be detected as closeable."""
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(days=CANONICAL_CLOSED_DAYS + 1)

        closed_id = compute_canonical_job_id(
            _COMPANY_ID, "Ancient Role", "NYC"
        )
        old_job = CanonicalJob(
            canonical_job_id=closed_id,
            company_id=_COMPANY_ID,
            company_name=_COMPANY_NAME,
            title="Ancient Role",
            source_count=1,
            first_seen_at=old_time,
            last_seen_at=old_time,
            is_active=True,
            created_at=old_time,
        )
        m4_session.add(old_job)
        await m4_session.flush()

        closed_ids = await service.detect_closed_jobs()
        assert closed_id in closed_ids

    @pytest.mark.asyncio
    async def test_mark_job_closed(self, service, m4_session):
        """mark_job_closed should set is_active=False and closed_at."""
        now = datetime.now(timezone.utc)
        cid = compute_canonical_job_id(_COMPANY_ID, "Close Me", "Remote")
        job = CanonicalJob(
            canonical_job_id=cid,
            company_id=_COMPANY_ID,
            company_name=_COMPANY_NAME,
            title="Close Me",
            source_count=1,
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            created_at=now,
        )
        m4_session.add(job)
        await m4_session.flush()

        result = await service.mark_job_closed(cid)
        await m4_session.flush()

        assert result is not None
        assert result.is_active is False
        assert result.closed_at is not None

    @pytest.mark.asyncio
    async def test_mark_job_closed_not_found(self, service):
        """mark_job_closed with nonexistent ID returns None."""
        result = await service.mark_job_closed("nonexistent_id")
        assert result is None


class TestReactivation:
    """Tests for job reactivation."""

    @pytest.mark.asyncio
    async def test_reactivate_closed_job(self, service, m4_session):
        """Reactivating a closed job should set is_active=True and clear closed_at."""
        now = datetime.now(timezone.utc)
        cid = compute_canonical_job_id(_COMPANY_ID, "Reactivate Me", "Remote")
        job = CanonicalJob(
            canonical_job_id=cid,
            company_id=_COMPANY_ID,
            company_name=_COMPANY_NAME,
            title="Reactivate Me",
            source_count=1,
            first_seen_at=now,
            last_seen_at=now,
            is_active=False,
            closed_at=now,
            created_at=now,
        )
        m4_session.add(job)
        await m4_session.flush()

        result = await service.reactivate_job(cid)
        await m4_session.flush()

        assert result is not None
        assert result.is_active is True
        assert result.closed_at is None

    @pytest.mark.asyncio
    async def test_reactivate_not_found(self, service):
        """reactivate_job with nonexistent ID returns None."""
        result = await service.reactivate_job("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_merge_reactivates_closed_job(self, service, m4_session):
        """Merging a new raw source into a closed canonical should reactivate it."""
        now = datetime.now(timezone.utc)

        # Create and close a canonical job
        _, can1, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-react-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        can1.is_active = False
        can1.closed_at = now
        await m4_session.flush()
        assert can1.is_active is False

        # Re-ingest from a different source
        _, can2, _ = await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-react-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert can2.is_active is True
        assert can2.closed_at is None


class TestQueryMethods:
    """Tests for query methods."""

    @pytest.mark.asyncio
    async def test_get_canonical_job(self, service, m4_session):
        """get_canonical_job returns the correct record."""
        _, canonical, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-query-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        result = await service.get_canonical_job(canonical.canonical_job_id)
        assert result is not None
        assert result.title == "Engineer"

    @pytest.mark.asyncio
    async def test_get_canonical_job_not_found(self, service):
        """get_canonical_job returns None for nonexistent ID."""
        result = await service.get_canonical_job("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_canonical_jobs(self, service, m4_session):
        """list_canonical_jobs returns jobs with correct filtering."""
        # Create two jobs
        for i in range(3):
            await service.ingest_raw_job(
                source="greenhouse",
                source_job_id=f"gh-list-{i}",
                title_raw=f"Role {i}",
                company_name_raw=_COMPANY_NAME,
                location_raw="Remote",
                company_id=_COMPANY_ID,
            )
        await m4_session.flush()

        # List all
        jobs = await service.list_canonical_jobs()
        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_list_canonical_jobs_filter_active(
        self, service, m4_session
    ):
        """list_canonical_jobs with is_active filter."""
        _, can1, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-active-001",
            title_raw="Active Role",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        _, can2, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-inactive-001",
            title_raw="Inactive Role",
            company_name_raw=_COMPANY_NAME,
            location_raw="NYC",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        can2.is_active = False
        await m4_session.flush()

        active = await service.list_canonical_jobs(is_active=True)
        inactive = await service.list_canonical_jobs(is_active=False)

        assert len(active) == 1
        assert active[0].title == "Active Role"
        assert len(inactive) == 1
        assert inactive[0].title == "Inactive Role"

    @pytest.mark.asyncio
    async def test_list_canonical_jobs_pagination(self, service, m4_session):
        """list_canonical_jobs respects limit and offset."""
        for i in range(5):
            await service.ingest_raw_job(
                source="greenhouse",
                source_job_id=f"gh-page-{i}",
                title_raw=f"Page Role {i}",
                company_name_raw=_COMPANY_NAME,
                location_raw=f"City {i}",
                company_id=_COMPANY_ID,
            )
        await m4_session.flush()

        page1 = await service.list_canonical_jobs(limit=2, offset=0)
        page2 = await service.list_canonical_jobs(limit=2, offset=2)
        page3 = await service.list_canonical_jobs(limit=2, offset=4)

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1

    @pytest.mark.asyncio
    async def test_get_raw_sources(self, service, m4_session):
        """get_raw_sources returns all linked raw records."""
        # Create canonical with two sources
        _, can, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-raw-src-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        await service.ingest_raw_job(
            source="lever",
            source_job_id="lev-raw-src-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        sources = await service.get_raw_sources(can.canonical_job_id)
        assert len(sources) == 2
        source_types = {s.source for s in sources}
        assert "greenhouse" in source_types
        assert "lever" in source_types

    @pytest.mark.asyncio
    async def test_get_raw_job(self, service, m4_session):
        """get_raw_job returns the correct raw record."""
        raw, _, _ = await service.ingest_raw_job(
            source="ashby",
            source_job_id="ash-get-001",
            title_raw="Developer",
        )
        await m4_session.flush()

        result = await service.get_raw_job(raw.raw_id)
        assert result is not None
        assert result.title_raw == "Developer"

    @pytest.mark.asyncio
    async def test_get_raw_job_not_found(self, service):
        """get_raw_job returns None for nonexistent ID."""
        result = await service.get_raw_job("nonexistent")
        assert result is None


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    @pytest.mark.asyncio
    async def test_duplicate_raw_ingest_idempotent(self, service, m4_session):
        """Ingesting the exact same raw job multiple times is safe."""
        for _ in range(5):
            raw, _, _ = await service.ingest_raw_job(
                source="greenhouse",
                source_job_id="gh-idempotent",
                title_raw="Engineer",
                company_name_raw=_COMPANY_NAME,
            )
            await m4_session.flush()

        assert raw.scrape_count == 5

        # Verify only one raw record exists
        result = await m4_session.execute(
            text(
                "SELECT COUNT(*) FROM raw_job_sources "
                "WHERE source = 'greenhouse' AND source_job_id = 'gh-idempotent'"
            )
        )
        count = result.fetchone()[0]
        assert count == 1

    @pytest.mark.asyncio
    async def test_minimal_data_ingest(self, service, m4_session):
        """Ingest with only required fields should succeed."""
        raw, canonical, is_new = await service.ingest_raw_job(
            source="jobspy",
            source_job_id="js-minimal",
        )
        await m4_session.flush()

        assert raw is not None
        assert raw.source == "jobspy"
        assert canonical is None  # No company_id => no canonical

    @pytest.mark.asyncio
    async def test_source_quality_order_respected(self, service):
        """SOURCE_QUALITY_ORDER should match the expected ranking."""
        assert SOURCE_QUALITY_ORDER[0] == "greenhouse"
        assert SOURCE_QUALITY_ORDER[-1] == "apify"

        from backend.phase7a.m4_service import _source_quality_rank

        assert _source_quality_rank("greenhouse") < _source_quality_rank("serpapi")
        assert _source_quality_rank("lever") < _source_quality_rank("jobspy")
        assert _source_quality_rank("unknown_source") == len(SOURCE_QUALITY_ORDER)

    @pytest.mark.asyncio
    async def test_remote_type_set_from_location(self, service, m4_session):
        """Location containing 'remote' should set remote_type."""
        _, canonical, _ = await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-remote-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        assert canonical.remote_type == "remote"

    @pytest.mark.asyncio
    async def test_list_filter_by_company_id(self, service, m4_session):
        """list_canonical_jobs can filter by company_id."""
        company2_id = compute_company_id("other.com")

        await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-co1-001",
            title_raw="Engineer",
            company_name_raw=_COMPANY_NAME,
            location_raw="Remote",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-co2-001",
            title_raw="Designer",
            company_name_raw="Other Inc",
            location_raw="Remote",
            company_id=company2_id,
        )
        await m4_session.flush()

        acme_jobs = await service.list_canonical_jobs(company_id=_COMPANY_ID)
        other_jobs = await service.list_canonical_jobs(company_id=company2_id)

        assert len(acme_jobs) == 1
        assert acme_jobs[0].company_name == _COMPANY_NAME
        assert len(other_jobs) == 1
        assert other_jobs[0].company_name == "Other Inc"

    @pytest.mark.asyncio
    async def test_list_filter_by_primary_source(self, service, m4_session):
        """list_canonical_jobs can filter by primary_source."""
        await service.ingest_raw_job(
            source="greenhouse",
            source_job_id="gh-src-filter-001",
            title_raw="GH Role",
            company_name_raw=_COMPANY_NAME,
            location_raw="NYC",
            company_id=_COMPANY_ID,
        )
        await m4_session.flush()

        await service.ingest_raw_job(
            source="serpapi",
            source_job_id="serp-src-filter-001",
            title_raw="Serp Role",
            company_name_raw="Beta Corp",
            location_raw="LA",
            company_id=compute_company_id("beta.com"),
        )
        await m4_session.flush()

        gh_jobs = await service.list_canonical_jobs(primary_source="greenhouse")
        serp_jobs = await service.list_canonical_jobs(primary_source="serpapi")

        assert len(gh_jobs) == 1
        assert len(serp_jobs) == 1

    @pytest.mark.asyncio
    async def test_mark_stale_returns_job(self, service, m4_session):
        """mark_job_stale should return the updated job."""
        now = datetime.now(timezone.utc)
        cid = compute_canonical_job_id(_COMPANY_ID, "Stale Target", "Remote")
        job = CanonicalJob(
            canonical_job_id=cid,
            company_id=_COMPANY_ID,
            company_name=_COMPANY_NAME,
            title="Stale Target",
            source_count=1,
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            created_at=now,
        )
        m4_session.add(job)
        await m4_session.flush()

        result = await service.mark_job_stale(cid)
        assert result is not None
        assert result.is_active is True  # stale but still active
        assert result.updated_at is not None

    @pytest.mark.asyncio
    async def test_mark_stale_not_found(self, service):
        """mark_job_stale with nonexistent ID returns None."""
        result = await service.mark_job_stale("nonexistent")
        assert result is None
