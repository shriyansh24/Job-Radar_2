"""Module 4 -- Canonical Jobs Pipeline: Service layer.

Provides the ``CanonicalJobsService`` class which handles:
    - Raw job ingestion (upsert)
    - Canonical matching and merge
    - Quality scoring
    - Stale/closed detection and lifecycle management
    - Query helpers

The service operates on a SQLAlchemy ``AsyncSession`` and is stateless.
All timestamps use UTC.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.phase7a.constants import (
    CANONICAL_CLOSED_DAYS,
    SOURCE_QUALITY_ORDER,
    SourceType,
)
from backend.phase7a.id_utils import (
    compute_canonical_job_id,
    compute_raw_job_id,
    normalize_location,
    normalize_title,
)
from backend.phase7a.m4_models import CanonicalJob, RawJobSource

logger = logging.getLogger(__name__)


# ATS sources that provide higher-quality structured data.
_ATS_SOURCES = frozenset({
    SourceType.GREENHOUSE.value,
    SourceType.LEVER.value,
    SourceType.ASHBY.value,
})


def _source_quality_rank(source: str) -> int:
    """Return the quality rank for a source (lower = better).

    Sources not in SOURCE_QUALITY_ORDER get a high rank (low quality).
    """
    try:
        return SOURCE_QUALITY_ORDER.index(source)
    except ValueError:
        return len(SOURCE_QUALITY_ORDER)


class CanonicalJobsService:
    """Service for managing canonical jobs and raw source records.

    All methods require a SQLAlchemy ``AsyncSession`` passed at construction.
    The caller is responsible for committing or rolling back the session.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Raw Job Ingestion
    # ------------------------------------------------------------------

    async def ingest_raw_job(
        self,
        source: str,
        source_job_id: str,
        *,
        source_url: Optional[str] = None,
        source_id: Optional[str] = None,
        title_raw: Optional[str] = None,
        company_name_raw: Optional[str] = None,
        location_raw: Optional[str] = None,
        salary_raw: Optional[str] = None,
        description_raw: Optional[str] = None,
        raw_payload: Optional[dict] = None,
        company_id: Optional[str] = None,
    ) -> tuple[RawJobSource, Optional[CanonicalJob], bool]:
        """Ingest a raw job record from a scraper source.

        If the raw record already exists (by raw_id), it is updated:
            - last_seen_at refreshed
            - scrape_count incremented
            - is_active set to True
            - Non-None fields updated (fields provided in this call replace
              old values; None fields are left unchanged).

        If the raw record is new, it is created.

        If company_id + title_raw + location_raw are all available, the service
        attempts canonical matching and merge.

        Args:
            source: Scraper source type (e.g., "greenhouse", "serpapi").
            source_job_id: Source-specific job identifier.
            source_url: URL to the job on the source.
            source_id: Soft FK to source_registry (M3).
            title_raw: Raw job title as scraped.
            company_name_raw: Raw company name as scraped.
            location_raw: Raw location string as scraped.
            salary_raw: Raw salary string as scraped.
            description_raw: Raw job description text.
            raw_payload: Full raw JSON payload from the scraper.
            company_id: Deterministic company ID (from M1 or compute_company_id).

        Returns:
            Tuple of (raw_record, canonical_record_or_None, is_new_canonical).
        """
        now = datetime.now(timezone.utc)
        raw_id = compute_raw_job_id(source, source_job_id)

        # Try to fetch existing raw record
        existing = await self._get_raw_job_by_id(raw_id)

        if existing is not None:
            # Update existing record
            existing.last_seen_at = now
            existing.scrape_count = existing.scrape_count + 1
            existing.is_active = True

            # Update non-None fields
            if source_url is not None:
                existing.source_url = source_url
            if source_id is not None:
                existing.source_id = source_id
            if title_raw is not None:
                existing.title_raw = title_raw
            if company_name_raw is not None:
                existing.company_name_raw = company_name_raw
            if location_raw is not None:
                existing.location_raw = location_raw
            if salary_raw is not None:
                existing.salary_raw = salary_raw
            if description_raw is not None:
                existing.description_raw = description_raw
            if raw_payload is not None:
                existing.raw_payload = raw_payload

            raw_record = existing
        else:
            # Create new raw record
            raw_record = RawJobSource(
                raw_id=raw_id,
                source=source,
                source_job_id=source_job_id,
                source_url=source_url,
                source_id=source_id,
                raw_payload=raw_payload,
                title_raw=title_raw,
                company_name_raw=company_name_raw,
                location_raw=location_raw,
                salary_raw=salary_raw,
                description_raw=description_raw,
                first_seen_at=now,
                last_seen_at=now,
                is_active=True,
                scrape_count=1,
            )
            self.session.add(raw_record)

        # Attempt canonical matching if we have enough info
        canonical_record = None
        is_new_canonical = False

        if company_id and title_raw and location_raw is not None:
            # Pre-compute the canonical_job_id so we can link the raw record
            # before merge, allowing _count_sources to see this raw source.
            expected_cid = compute_canonical_job_id(
                company_id, title_raw, location_raw
            )
            raw_record.canonical_job_id = expected_cid

            canonical_record, is_new_canonical = await self._match_and_merge(
                company_id=company_id,
                company_name=company_name_raw or "",
                title=title_raw,
                location=location_raw,
                raw_source=raw_record,
            )

            # Verify the link (canonical_job_id should already match)
            if canonical_record is not None:
                raw_record.canonical_job_id = canonical_record.canonical_job_id
            else:
                # Shouldn't happen, but be defensive
                raw_record.canonical_job_id = None

        return raw_record, canonical_record, is_new_canonical

    # ------------------------------------------------------------------
    # Canonical Matching
    # ------------------------------------------------------------------

    async def _match_canonical(
        self,
        company_id: str,
        title: str,
        location: str,
    ) -> Optional[CanonicalJob]:
        """Find an existing canonical job matching the given identity.

        Uses the deterministic canonical_job_id computed from
        company_id + normalized_title + normalized_location.

        Returns:
            The matching CanonicalJob or None.
        """
        canonical_id = compute_canonical_job_id(company_id, title, location)
        result = await self.session.execute(
            select(CanonicalJob).where(
                CanonicalJob.canonical_job_id == canonical_id
            )
        )
        return result.scalars().first()

    async def _match_and_merge(
        self,
        company_id: str,
        company_name: str,
        title: str,
        location: str,
        raw_source: RawJobSource,
    ) -> tuple[Optional[CanonicalJob], bool]:
        """Match a raw source to a canonical job, creating or merging as needed.

        Returns:
            Tuple of (canonical_job, is_new_canonical).
        """
        existing = await self._match_canonical(company_id, title, location)

        if existing is not None:
            merged = await self._merge_into_canonical(existing, raw_source)
            return merged, False
        else:
            new_canonical = await self._create_canonical(
                company_id, company_name, title, location, raw_source
            )
            return new_canonical, True

    # ------------------------------------------------------------------
    # Merge Logic
    # ------------------------------------------------------------------

    async def _merge_into_canonical(
        self,
        canonical_job: CanonicalJob,
        raw_source: RawJobSource,
    ) -> CanonicalJob:
        """Merge data from a raw source into an existing canonical job.

        Merge rules based on SOURCE_QUALITY_ORDER:
            - title: longer title wins if from equal or better source
            - salary: prefer ATS source data
            - description: longest from best source
            - apply_url: ATS link preferred
            - source_count incremented
            - primary_source: best quality source
            - last_seen_at: most recent
            - quality_score: recalculated

        Args:
            canonical_job: The existing canonical job to update.
            raw_source: The raw source record being merged.

        Returns:
            The updated canonical job.
        """
        now = datetime.now(timezone.utc)
        source = raw_source.source

        current_primary_rank = _source_quality_rank(
            canonical_job.primary_source or ""
        )
        new_source_rank = _source_quality_rank(source)
        is_better_source = new_source_rank < current_primary_rank
        is_equal_source = new_source_rank == current_primary_rank

        # Title: longer wins if from equal or better source
        if raw_source.title_raw:
            if is_better_source or (
                is_equal_source
                and len(raw_source.title_raw) > len(canonical_job.title or "")
            ):
                canonical_job.title = raw_source.title_raw
                canonical_job.title_normalized = normalize_title(raw_source.title_raw)

        # Salary: prefer ATS source data
        if raw_source.salary_raw and source in _ATS_SOURCES:
            # Parse simple salary patterns (this is a best-effort pass-through;
            # full salary parsing belongs in enrichment pipeline)
            pass  # salary_raw is a string; canonical stores ints. Leave for enrichment.

        # Description: longest from best source
        if raw_source.description_raw:
            current_desc_len = len(canonical_job.description_markdown or "")
            new_desc_len = len(raw_source.description_raw)
            if is_better_source or (
                is_equal_source and new_desc_len > current_desc_len
            ):
                canonical_job.description_markdown = raw_source.description_raw

        # Apply URL: ATS link preferred
        if raw_source.source_url:
            if source in _ATS_SOURCES or not canonical_job.apply_url:
                canonical_job.apply_url = raw_source.source_url

        # Location: update if from better source and we have data
        if raw_source.location_raw and is_better_source:
            canonical_job.location_raw = raw_source.location_raw

        # Update provenance
        # Count distinct linked sources
        source_count = await self._count_sources(
            canonical_job.canonical_job_id
        )
        canonical_job.source_count = source_count

        if is_better_source:
            canonical_job.primary_source = source

        # Update lifecycle
        canonical_job.last_seen_at = now
        canonical_job.updated_at = now
        canonical_job.is_active = True
        canonical_job.closed_at = None  # Reactivate if previously closed

        # Recalculate quality score
        canonical_job.quality_score = self._calculate_quality_score(
            canonical_job
        )

        return canonical_job

    async def _create_canonical(
        self,
        company_id: str,
        company_name: str,
        title: str,
        location: str,
        raw_source: RawJobSource,
    ) -> CanonicalJob:
        """Create a new canonical job from a raw source.

        Args:
            company_id: Deterministic company ID.
            company_name: Display name for the company.
            title: Job title (raw, will be stored and normalized).
            location: Location string (raw).
            raw_source: The originating raw source record.

        Returns:
            The newly created canonical job.
        """
        now = datetime.now(timezone.utc)
        canonical_id = compute_canonical_job_id(company_id, title, location)
        normalized_title = normalize_title(title)
        normalized_loc = normalize_location(location)

        canonical = CanonicalJob(
            canonical_job_id=canonical_id,
            company_id=company_id,
            company_name=company_name,
            title=title,
            title_normalized=normalized_title,
            location_raw=location,
            location_city=normalized_loc if normalized_loc != "remote" else None,
            description_markdown=raw_source.description_raw,
            apply_url=raw_source.source_url,
            source_count=1,
            primary_source=raw_source.source,
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        # Set remote_type heuristic from location
        if normalized_loc == "remote":
            canonical.remote_type = "remote"

        # Calculate initial quality score
        canonical.quality_score = self._calculate_quality_score(canonical)

        self.session.add(canonical)
        return canonical

    # ------------------------------------------------------------------
    # Quality Scoring
    # ------------------------------------------------------------------

    def _calculate_quality_score(self, canonical_job: CanonicalJob) -> int:
        """Calculate a quality score (0-100) for a canonical job.

        Scoring breakdown:
            - title present: +10
            - company_id present: +10
            - location present: +10
            - salary data present: +15
            - description present: +15
            - apply_url present: +10
            - multi-source: +5 per extra source (max +20)
            - ATS primary source: +10

        Args:
            canonical_job: The canonical job to score.

        Returns:
            Integer score between 0 and 100.
        """
        score = 0

        if canonical_job.title:
            score += 10
        if canonical_job.company_id:
            score += 10
        if (
            canonical_job.location_city
            or canonical_job.location_raw
            or canonical_job.remote_type
        ):
            score += 10
        if canonical_job.salary_min is not None or canonical_job.salary_max is not None:
            score += 15
        if canonical_job.description_markdown:
            score += 15
        if canonical_job.apply_url:
            score += 10

        # Multi-source bonus: +5 per extra source, max +20
        extra_sources = max(0, (canonical_job.source_count or 1) - 1)
        score += min(extra_sources * 5, 20)

        # ATS primary source bonus
        if canonical_job.primary_source in _ATS_SOURCES:
            score += 10

        return min(score, 100)

    # ------------------------------------------------------------------
    # Stale / Closed Detection
    # ------------------------------------------------------------------

    async def detect_stale_jobs(self) -> list[str]:
        """Detect canonical jobs that may be stale.

        A job is considered stale if none of its raw sources have been seen
        in the last ``CANONICAL_STALE_SCRAPES`` scrape cycles (approximated
        by checking if last_seen_at is older than CANONICAL_CLOSED_DAYS/2).

        Returns:
            List of canonical_job_ids that are stale.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=CANONICAL_CLOSED_DAYS // 2
        )
        result = await self.session.execute(
            select(CanonicalJob.canonical_job_id).where(
                CanonicalJob.is_active == True,  # noqa: E712
                CanonicalJob.last_seen_at < cutoff,
            )
        )
        return [row[0] for row in result.fetchall()]

    async def detect_closed_jobs(self) -> list[str]:
        """Detect canonical jobs that should be marked closed.

        A job is considered closed if it hasn't been seen for
        ``CANONICAL_CLOSED_DAYS`` days.

        Returns:
            List of canonical_job_ids that should be closed.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=CANONICAL_CLOSED_DAYS
        )
        result = await self.session.execute(
            select(CanonicalJob.canonical_job_id).where(
                CanonicalJob.is_active == True,  # noqa: E712
                CanonicalJob.last_seen_at < cutoff,
            )
        )
        return [row[0] for row in result.fetchall()]

    async def mark_job_closed(self, canonical_job_id: str) -> Optional[CanonicalJob]:
        """Mark a canonical job as closed.

        Sets is_active=False and closed_at to now.

        Returns:
            The updated canonical job, or None if not found.
        """
        job = await self.get_canonical_job(canonical_job_id)
        if job is None:
            return None
        now = datetime.now(timezone.utc)
        job.is_active = False
        job.closed_at = now
        job.updated_at = now
        return job

    async def mark_job_stale(self, canonical_job_id: str) -> Optional[CanonicalJob]:
        """Mark a canonical job as stale (still active but flagged).

        Updates the updated_at timestamp. The job remains is_active=True
        but the caller may use this signal for UI indication.

        Returns:
            The updated canonical job, or None if not found.
        """
        job = await self.get_canonical_job(canonical_job_id)
        if job is None:
            return None
        job.updated_at = datetime.now(timezone.utc)
        return job

    async def reactivate_job(self, canonical_job_id: str) -> Optional[CanonicalJob]:
        """Reactivate a previously closed or stale canonical job.

        Sets is_active=True, clears closed_at, and refreshes timestamps.

        Returns:
            The updated canonical job, or None if not found.
        """
        job = await self.get_canonical_job(canonical_job_id)
        if job is None:
            return None
        now = datetime.now(timezone.utc)
        job.is_active = True
        job.closed_at = None
        job.last_seen_at = now
        job.updated_at = now
        return job

    # ------------------------------------------------------------------
    # Query Methods
    # ------------------------------------------------------------------

    async def get_canonical_job(
        self, canonical_job_id: str
    ) -> Optional[CanonicalJob]:
        """Get a canonical job by ID.

        Returns:
            The canonical job or None.
        """
        result = await self.session.execute(
            select(CanonicalJob).where(
                CanonicalJob.canonical_job_id == canonical_job_id
            )
        )
        return result.scalars().first()

    async def list_canonical_jobs(
        self,
        *,
        is_active: Optional[bool] = None,
        company_id: Optional[str] = None,
        primary_source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CanonicalJob]:
        """List canonical jobs with optional filters.

        Args:
            is_active: Filter by active state.
            company_id: Filter by company.
            primary_source: Filter by primary source.
            limit: Maximum results (default 50).
            offset: Pagination offset.

        Returns:
            List of canonical jobs.
        """
        stmt = select(CanonicalJob)

        if is_active is not None:
            stmt = stmt.where(CanonicalJob.is_active == is_active)
        if company_id is not None:
            stmt = stmt.where(CanonicalJob.company_id == company_id)
        if primary_source is not None:
            stmt = stmt.where(CanonicalJob.primary_source == primary_source)

        stmt = stmt.order_by(CanonicalJob.last_seen_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_raw_sources(
        self, canonical_job_id: str
    ) -> list[RawJobSource]:
        """Get all raw sources linked to a canonical job.

        Returns:
            List of raw source records.
        """
        result = await self.session.execute(
            select(RawJobSource)
            .where(RawJobSource.canonical_job_id == canonical_job_id)
            .order_by(RawJobSource.first_seen_at.asc())
        )
        return list(result.scalars().all())

    async def get_raw_job(self, raw_id: str) -> Optional[RawJobSource]:
        """Get a raw job source by raw_id.

        Returns:
            The raw job source or None.
        """
        return await self._get_raw_job_by_id(raw_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_raw_job_by_id(self, raw_id: str) -> Optional[RawJobSource]:
        """Fetch a raw job source record by its raw_id."""
        result = await self.session.execute(
            select(RawJobSource).where(RawJobSource.raw_id == raw_id)
        )
        return result.scalars().first()

    async def _count_sources(self, canonical_job_id: str) -> int:
        """Count distinct sources linked to a canonical job.

        Uses an ORM query to ensure the session auto-flushes pending
        changes before counting.
        """
        result = await self.session.execute(
            select(func.count(func.distinct(RawJobSource.source))).where(
                RawJobSource.canonical_job_id == canonical_job_id
            )
        )
        count = result.scalar()
        return count if count is not None else 0
