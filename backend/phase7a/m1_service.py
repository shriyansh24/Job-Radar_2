"""Module 1 — Company Intelligence Registry: Service layer.

CompanyService provides CRUD, validation orchestration, confidence scoring,
and idempotent get-or-create operations for the Company Registry.

All methods accept an async SQLAlchemy session and return model instances
or raise appropriate exceptions. No HTTP/router coupling here.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func as sa_func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.phase7a.constants import (
    ATSProvider,
    ValidationState,
    SourceType,
    CONFIDENCE_SIGNALS,
    CONFIDENCE_MAX,
    CONFIDENCE_MULTI_SOURCE_CAP,
)
from backend.phase7a.id_utils import (
    compute_company_id,
    normalize_domain,
    normalize_company_name,
)
from backend.phase7a.m1_models import Company, CompanySource, ATSDetectionLog

logger = logging.getLogger(__name__)


class CompanyServiceError(Exception):
    """Base exception for CompanyService operations."""
    pass


class CompanyNotFoundError(CompanyServiceError):
    """Raised when a company_id does not exist."""
    pass


class DuplicateDomainError(CompanyServiceError):
    """Raised when trying to create a company with an already-registered domain."""
    pass


class DuplicateNameError(CompanyServiceError):
    """Raised when trying to create a company with an already-registered canonical name."""
    pass


class InvalidStateTransitionError(CompanyServiceError):
    """Raised when a validation state transition is not allowed."""
    pass


# --- Valid state transitions ---
# Maps (current_state) -> set of allowed next states
_VALID_TRANSITIONS: dict[str, set[str]] = {
    ValidationState.UNVERIFIED.value: {
        ValidationState.PROBING.value,
    },
    ValidationState.PROBING.value: {
        ValidationState.VERIFIED.value,
        ValidationState.INVALID.value,
    },
    ValidationState.VERIFIED.value: {
        ValidationState.STALE.value,
        ValidationState.PROBING.value,
    },
    ValidationState.STALE.value: {
        ValidationState.PROBING.value,
        ValidationState.INVALID.value,
    },
    ValidationState.INVALID.value: {
        ValidationState.PROBING.value,
    },
}


class CompanyService:
    """Service layer for the Company Intelligence Registry (M1).

    All public methods accept an AsyncSession and operate within it.
    Callers are responsible for committing/rolling back the session.
    """

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    async def create_company(
        self,
        session: AsyncSession,
        canonical_name: str,
        domain: Optional[str] = None,
        ats_provider: Optional[str] = None,
        ats_slug: Optional[str] = None,
        careers_url: Optional[str] = None,
        logo_url: Optional[str] = None,
    ) -> Company:
        """Create a new company record.

        Args:
            session: Async database session.
            canonical_name: Display name (e.g., "Stripe").
            domain: Primary domain (e.g., "stripe.com"). Optional.
            ats_provider: ATS provider enum value. Optional.
            ats_slug: ATS board slug. Optional.
            careers_url: Careers page URL. Optional.
            logo_url: Company logo URL. Optional.

        Returns:
            The newly created Company instance.

        Raises:
            DuplicateDomainError: If domain already registered.
            DuplicateNameError: If canonical_name already registered.
        """
        # Validate ATS provider if provided
        if ats_provider is not None:
            try:
                ATSProvider(ats_provider)
            except ValueError:
                raise CompanyServiceError(
                    f"Invalid ATS provider: '{ats_provider}'. "
                    f"Valid values: {[p.value for p in ATSProvider]}"
                )

        # Normalize domain
        normalized_domain = normalize_domain(domain) if domain else None

        # Compute deterministic ID
        if normalized_domain:
            company_id = compute_company_id(normalized_domain)
        else:
            company_id = compute_company_id(canonical_name)

        # Check for existing company with same ID (domain or name collision)
        existing = await self.get_company(session, company_id)
        if existing is not None:
            if normalized_domain and existing.domain == normalized_domain:
                raise DuplicateDomainError(
                    f"Domain '{normalized_domain}' is already registered "
                    f"to company '{existing.canonical_name}'"
                )
            raise DuplicateNameError(
                f"Company ID collision: name '{canonical_name}' produces "
                f"same ID as existing company '{existing.canonical_name}'"
            )

        # Check for existing domain (in case different ID but same domain)
        if normalized_domain:
            existing_by_domain = await self.get_company_by_domain(
                session, normalized_domain
            )
            if existing_by_domain is not None:
                raise DuplicateDomainError(
                    f"Domain '{normalized_domain}' is already registered "
                    f"to company '{existing_by_domain.canonical_name}'"
                )

        # Check for existing canonical name
        existing_by_name = await self.get_company_by_name(session, canonical_name)
        if existing_by_name is not None:
            raise DuplicateNameError(
                f"Canonical name '{canonical_name}' is already registered "
                f"(company_id: {existing_by_name.company_id[:12]}...)"
            )

        now = datetime.now(timezone.utc)
        company = Company(
            company_id=company_id,
            canonical_name=canonical_name,
            domain=normalized_domain,
            ats_provider=ats_provider,
            ats_slug=ats_slug,
            careers_url=careers_url,
            logo_url=logo_url,
            validation_state=ValidationState.UNVERIFIED.value,
            confidence_score=0,
            manual_override=False,
            created_at=now,
        )
        session.add(company)
        await session.flush()
        logger.info(
            "Created company: %s (id=%s, domain=%s)",
            canonical_name,
            company_id[:12],
            normalized_domain,
        )
        return company

    async def get_company(
        self,
        session: AsyncSession,
        company_id: str,
    ) -> Optional[Company]:
        """Get a company by its ID.

        Returns None if not found.
        """
        result = await session.execute(
            select(Company).where(Company.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_company_by_domain(
        self,
        session: AsyncSession,
        domain: str,
    ) -> Optional[Company]:
        """Get a company by its primary domain.

        Domain is normalized before lookup. Returns None if not found.
        """
        normalized = normalize_domain(domain)
        result = await session.execute(
            select(Company).where(Company.domain == normalized)
        )
        return result.scalar_one_or_none()

    async def get_company_by_name(
        self,
        session: AsyncSession,
        canonical_name: str,
    ) -> Optional[Company]:
        """Get a company by its canonical name (exact match).

        Returns None if not found.
        """
        result = await session.execute(
            select(Company).where(Company.canonical_name == canonical_name)
        )
        return result.scalar_one_or_none()

    async def list_companies(
        self,
        session: AsyncSession,
        ats_provider: Optional[str] = None,
        validation_state: Optional[str] = None,
        query: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Company], int]:
        """List companies with optional filters and pagination.

        Args:
            session: Async database session.
            ats_provider: Filter by ATS provider.
            validation_state: Filter by validation state.
            query: Search canonical_name or domain (LIKE match).
            page: Page number (1-indexed).
            limit: Results per page.

        Returns:
            Tuple of (companies_list, total_count).
        """
        conditions = []

        if ats_provider is not None:
            conditions.append(Company.ats_provider == ats_provider)

        if validation_state is not None:
            conditions.append(Company.validation_state == validation_state)

        if query:
            like_pattern = f"%{query}%"
            conditions.append(
                or_(
                    Company.canonical_name.ilike(like_pattern),
                    Company.domain.ilike(like_pattern),
                )
            )

        base_query = select(Company)
        count_query = select(sa_func.count()).select_from(Company)

        if conditions:
            base_query = base_query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * limit
        base_query = (
            base_query
            .order_by(Company.canonical_name.asc())
            .offset(offset)
            .limit(limit)
        )

        result = await session.execute(base_query)
        companies = list(result.scalars().all())

        return companies, total

    async def update_company(
        self,
        session: AsyncSession,
        company_id: str,
        **fields,
    ) -> Company:
        """Update specified fields on a company record.

        Only provided fields are updated. The updated_at timestamp is
        set automatically by SQLAlchemy's onupdate.

        Args:
            session: Async database session.
            company_id: Company to update.
            **fields: Field name/value pairs to update.

        Returns:
            The updated Company instance.

        Raises:
            CompanyNotFoundError: If company_id does not exist.
            CompanyServiceError: If an invalid field is provided.
        """
        company = await self.get_company(session, company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Company with ID '{company_id[:12]}...' does not exist"
            )

        # Validate ATS provider if being updated
        if "ats_provider" in fields and fields["ats_provider"] is not None:
            try:
                ATSProvider(fields["ats_provider"])
            except ValueError:
                raise CompanyServiceError(
                    f"Invalid ATS provider: '{fields['ats_provider']}'"
                )

        # Normalize domain if being updated
        if "domain" in fields and fields["domain"] is not None:
            fields["domain"] = normalize_domain(fields["domain"])

        # Validate validation_state if being set directly
        if "validation_state" in fields and fields["validation_state"] is not None:
            try:
                ValidationState(fields["validation_state"])
            except ValueError:
                raise CompanyServiceError(
                    f"Invalid validation state: '{fields['validation_state']}'"
                )

        # Track which columns are valid on Company
        valid_columns = {c.key for c in Company.__table__.columns}

        now = datetime.now(timezone.utc)
        for field_name, value in fields.items():
            if field_name not in valid_columns:
                raise CompanyServiceError(
                    f"Unknown field: '{field_name}'"
                )
            setattr(company, field_name, value)

        company.updated_at = now
        await session.flush()

        logger.info("Updated company %s: fields=%s", company_id[:12], list(fields.keys()))
        return company

    # -------------------------------------------------------------------------
    # Validation State Machine
    # -------------------------------------------------------------------------

    async def update_validation_state(
        self,
        session: AsyncSession,
        company_id: str,
        new_state: str,
        error: Optional[str] = None,
    ) -> Company:
        """Transition a company's validation state.

        Enforces the state machine transitions. If manual_override is True
        on the company, the transition is rejected unless the caller
        explicitly sets the override to False first.

        Args:
            session: Async database session.
            company_id: Company to update.
            new_state: Target validation state.
            error: Error message if transitioning to invalid.

        Returns:
            The updated Company instance.

        Raises:
            CompanyNotFoundError: If company_id does not exist.
            InvalidStateTransitionError: If transition is not allowed.
        """
        company = await self.get_company(session, company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Company with ID '{company_id[:12]}...' does not exist"
            )

        # Validate the new state is a real enum value
        try:
            ValidationState(new_state)
        except ValueError:
            raise InvalidStateTransitionError(
                f"Invalid validation state: '{new_state}'"
            )

        # Manual override blocks automated transitions
        if company.manual_override:
            raise InvalidStateTransitionError(
                f"Company '{company.canonical_name}' has manual_override=True. "
                f"Clear the override before changing validation state."
            )

        # Check if transition is allowed
        current_state = company.validation_state
        allowed = _VALID_TRANSITIONS.get(current_state, set())
        if new_state not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition from '{current_state}' to '{new_state}'. "
                f"Allowed transitions: {allowed}"
            )

        now = datetime.now(timezone.utc)
        company.validation_state = new_state
        company.updated_at = now

        # Update probe timestamps based on state
        if new_state == ValidationState.PROBING.value:
            company.last_probe_at = now
            company.probe_error = None
        elif new_state == ValidationState.VERIFIED.value:
            company.last_validated_at = now
            company.probe_error = None
        elif new_state == ValidationState.INVALID.value:
            company.probe_error = error

        await session.flush()

        logger.info(
            "Company %s state: %s -> %s",
            company_id[:12], current_state, new_state,
        )
        return company

    # -------------------------------------------------------------------------
    # Confidence Scoring
    # -------------------------------------------------------------------------

    async def calculate_confidence(
        self,
        session: AsyncSession,
        company_id: str,
        signals: Optional[dict[str, bool | int]] = None,
    ) -> int:
        """Calculate and update confidence score for a company.

        Scoring model (from architecture):
            - Domain verified (DNS resolves): +20
            - Careers page returns 200: +15
            - ATS pattern matched in URL: +25
            - ATS API responds with jobs: +30
            - Multiple sources confirm same ATS: +10 per source (max 30)
            - Jobs scraped successfully: +5

        Args:
            session: Async database session.
            company_id: Company to score.
            signals: Dict of signal_name -> True/False or int.
                If None, calculates from stored data.

        Returns:
            The calculated confidence score (0-100).

        Raises:
            CompanyNotFoundError: If company_id does not exist.
        """
        company = await self.get_company(session, company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Company with ID '{company_id[:12]}...' does not exist"
            )

        score = 0

        if signals is not None:
            # Use explicitly provided signals
            for signal_name, value in signals.items():
                if signal_name not in CONFIDENCE_SIGNALS:
                    continue

                if signal_name == "multi_source_confirm":
                    # Value is the count of confirming sources
                    count = int(value) if isinstance(value, (int, float)) else 0
                    points = min(
                        count * CONFIDENCE_SIGNALS["multi_source_confirm"],
                        CONFIDENCE_MULTI_SOURCE_CAP,
                    )
                    score += points
                elif value:
                    score += CONFIDENCE_SIGNALS[signal_name]
        else:
            # Auto-calculate from stored data
            # Domain exists
            if company.domain:
                score += CONFIDENCE_SIGNALS["domain_verified"]

            # ATS provider detected
            if company.ats_provider and company.ats_provider != ATSProvider.UNKNOWN.value:
                score += CONFIDENCE_SIGNALS["ats_pattern_matched"]

            # Count confirming sources
            source_count_result = await session.execute(
                select(sa_func.count())
                .select_from(CompanySource)
                .where(CompanySource.company_id == company_id)
            )
            source_count = source_count_result.scalar() or 0
            if source_count > 0:
                score += CONFIDENCE_SIGNALS["jobs_scraped"]
                multi_points = min(
                    source_count * CONFIDENCE_SIGNALS["multi_source_confirm"],
                    CONFIDENCE_MULTI_SOURCE_CAP,
                )
                score += multi_points

        # Clamp to max
        score = min(score, CONFIDENCE_MAX)

        company.confidence_score = score
        company.updated_at = datetime.now(timezone.utc)
        await session.flush()

        logger.debug(
            "Company %s confidence: %d",
            company_id[:12], score,
        )
        return score

    # -------------------------------------------------------------------------
    # Idempotent Get-or-Create
    # -------------------------------------------------------------------------

    async def get_or_create_company(
        self,
        session: AsyncSession,
        domain_or_name: str,
        canonical_name: Optional[str] = None,
    ) -> tuple[Company, bool]:
        """Idempotent lookup: return existing company or create a new one.

        If domain_or_name looks like a domain (contains '.', no spaces),
        looks up by domain first. Otherwise, looks up by name.

        Args:
            session: Async database session.
            domain_or_name: Domain (e.g., "stripe.com") or name (e.g., "Stripe").
            canonical_name: Display name if creating. Defaults to domain_or_name.

        Returns:
            Tuple of (company, created) where created is True if new.
        """
        value = domain_or_name.strip()
        is_domain = "." in value and " " not in value

        if is_domain:
            normalized = normalize_domain(value)
            existing = await self.get_company_by_domain(session, normalized)
            if existing is not None:
                return existing, False

            # Also check by computed ID in case the domain was used for ID
            computed_id = compute_company_id(normalized)
            existing = await self.get_company(session, computed_id)
            if existing is not None:
                return existing, False

            # Create with domain
            display_name = canonical_name or value.split(".")[0].capitalize()
            company = await self.create_company(
                session,
                canonical_name=display_name,
                domain=normalized,
            )
            return company, True
        else:
            # Name-based lookup
            normalized_name = normalize_company_name(value)
            computed_id = compute_company_id(value)
            existing = await self.get_company(session, computed_id)
            if existing is not None:
                return existing, False

            # Also check by canonical name (case-sensitive)
            display_name = canonical_name or value
            existing = await self.get_company_by_name(session, display_name)
            if existing is not None:
                return existing, False

            company = await self.create_company(
                session,
                canonical_name=display_name,
            )
            return company, True

    # -------------------------------------------------------------------------
    # Company Sources
    # -------------------------------------------------------------------------

    async def add_company_source(
        self,
        session: AsyncSession,
        company_id: str,
        source: str,
        source_identifier: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> CompanySource:
        """Add or update a source record for a company.

        If a source with the same (company_id, source, source_identifier)
        already exists, updates last_seen_at and increments jobs_count.

        Args:
            session: Async database session.
            company_id: Parent company.
            source: Source type value (e.g., "greenhouse").
            source_identifier: Source-specific identifier.
            source_url: Direct URL for this source.

        Returns:
            The created or updated CompanySource instance.

        Raises:
            CompanyNotFoundError: If company_id does not exist.
        """
        # Validate company exists
        company = await self.get_company(session, company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Company with ID '{company_id[:12]}...' does not exist"
            )

        # Validate source type
        try:
            SourceType(source)
        except ValueError:
            raise CompanyServiceError(
                f"Invalid source type: '{source}'. "
                f"Valid values: {[s.value for s in SourceType]}"
            )

        now = datetime.now(timezone.utc)

        # Check for existing source record
        conditions = [
            CompanySource.company_id == company_id,
            CompanySource.source == source,
        ]
        if source_identifier is not None:
            conditions.append(
                CompanySource.source_identifier == source_identifier
            )
        else:
            conditions.append(CompanySource.source_identifier.is_(None))

        result = await session.execute(
            select(CompanySource).where(and_(*conditions))
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.last_seen_at = now
            existing.jobs_count = (existing.jobs_count or 0) + 1
            if source_url and not existing.source_url:
                existing.source_url = source_url
            await session.flush()
            return existing

        # Create new source record
        company_source = CompanySource(
            company_id=company_id,
            source=source,
            source_identifier=source_identifier,
            source_url=source_url,
            jobs_count=1,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(company_source)
        await session.flush()

        logger.info(
            "Added source for company %s: %s/%s",
            company_id[:12], source, source_identifier,
        )
        return company_source

    async def get_company_sources(
        self,
        session: AsyncSession,
        company_id: str,
    ) -> list[CompanySource]:
        """Get all source records for a company.

        Returns an empty list if no sources found.
        """
        result = await session.execute(
            select(CompanySource)
            .where(CompanySource.company_id == company_id)
            .order_by(CompanySource.source.asc())
        )
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # ATS Detection Log
    # -------------------------------------------------------------------------

    async def log_ats_detection(
        self,
        session: AsyncSession,
        company_id: str,
        probe_url: str,
        provider: Optional[str] = None,
        method: Optional[str] = None,
        confidence: Optional[int] = None,
        status: Optional[int] = None,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> ATSDetectionLog:
        """Log an ATS detection probe attempt.

        Args:
            session: Async database session.
            company_id: Company being probed.
            probe_url: URL that was probed.
            provider: Detected ATS provider (or None).
            method: Detection method (url_pattern|meta_tag|api_probe|redirect).
            confidence: Detection confidence (0-100).
            status: HTTP status code.
            duration_ms: Probe duration in milliseconds.
            error: Error message if probe failed.

        Returns:
            The created ATSDetectionLog instance.

        Raises:
            CompanyNotFoundError: If company_id does not exist.
        """
        company = await self.get_company(session, company_id)
        if company is None:
            raise CompanyNotFoundError(
                f"Company with ID '{company_id[:12]}...' does not exist"
            )

        now = datetime.now(timezone.utc)
        log_entry = ATSDetectionLog(
            company_id=company_id,
            probe_url=probe_url,
            detected_provider=provider,
            detection_method=method,
            confidence=confidence,
            probe_status=status,
            probe_duration_ms=duration_ms,
            probed_at=now,
            error_message=error,
        )
        session.add(log_entry)
        await session.flush()

        logger.info(
            "ATS probe for %s: provider=%s, method=%s, confidence=%s, status=%s",
            company_id[:12], provider, method, confidence, status,
        )
        return log_entry

    async def get_recent_probes(
        self,
        session: AsyncSession,
        company_id: str,
        limit: int = 10,
    ) -> list[ATSDetectionLog]:
        """Get the most recent ATS detection probes for a company.

        Returns probes ordered by probed_at descending.
        """
        result = await session.execute(
            select(ATSDetectionLog)
            .where(ATSDetectionLog.company_id == company_id)
            .order_by(ATSDetectionLog.probed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
