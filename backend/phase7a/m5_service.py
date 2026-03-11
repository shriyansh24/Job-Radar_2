"""
Module 5 — Application Tracker: Service layer.

ApplicationService provides all business logic for creating, updating,
and querying application records. It enforces:
  - At least one job link (legacy or canonical) on creation
  - Status state machine transitions
  - Auto-setting of timestamp fields on status change
  - Audit trail recording in application_status_history
  - User-owned field protection (only explicitly allowed fields updatable)

All methods accept an AsyncSession and operate within the caller's
transaction boundary.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.phase7a.constants import (
    ApplicationStatus,
    ChangeSource,
    VALID_STATUS_TRANSITIONS,
    STATUS_TIMESTAMP_MAP,
)
from backend.phase7a.id_utils import generate_application_id
from backend.phase7a.m5_models import Application, ApplicationStatusHistory


class InvalidStatusTransitionError(Exception):
    """Raised when a status transition is not allowed by the state machine."""

    def __init__(self, current: str, requested: str, allowed: set[str]):
        self.current = current
        self.requested = requested
        self.allowed = allowed
        allowed_str = ", ".join(sorted(allowed)) if allowed else "(none — terminal state)"
        super().__init__(
            f"Cannot transition from '{current}' to '{requested}'. "
            f"Allowed transitions: {allowed_str}"
        )


class ApplicationNotFoundError(Exception):
    """Raised when an application record is not found."""

    def __init__(self, application_id: str):
        self.application_id = application_id
        super().__init__(f"Application not found: {application_id}")


class ApplicationCreateError(Exception):
    """Raised when application creation fails validation."""
    pass


class DuplicateApplicationError(Exception):
    """Raised when an application already exists for the given job."""

    def __init__(self, job_id: str, existing_app_id: str):
        self.job_id = job_id
        self.existing_app_id = existing_app_id
        super().__init__(
            f"Application already exists for job '{job_id}': {existing_app_id}"
        )


# Fields that the user is allowed to update directly via update_application()
_USER_UPDATABLE_FIELDS = frozenset({
    "notes",
    "tags",
    "custom_fields",
    "applied_at",
    "applied_via",
    "reminder_at",
    "reminder_note",
    "follow_up_at",
})


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class ApplicationService:
    """
    Service layer for the Application Tracker (Module 5).

    All public methods are async and accept an AsyncSession.
    The caller is responsible for committing/rolling back the session.
    """

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_application(
        self,
        session: AsyncSession,
        *,
        legacy_job_id: Optional[str] = None,
        canonical_job_id: Optional[str] = None,
        status: str = "saved",
        notes: Optional[str] = None,
        tags: Optional[list] = None,
        custom_fields: Optional[dict] = None,
        applied_at: Optional[datetime] = None,
        applied_via: Optional[str] = None,
    ) -> Application:
        """
        Create a new application record.

        Must provide at least one of legacy_job_id or canonical_job_id.
        Validates status is a valid ApplicationStatus value.
        Records initial status in the history table.

        Returns the created Application instance (flushed, not yet committed).
        """
        # Validate: at least one job link
        if not legacy_job_id and not canonical_job_id:
            raise ApplicationCreateError(
                "Must provide at least one of legacy_job_id or canonical_job_id"
            )

        # Validate status
        try:
            status_enum = ApplicationStatus(status)
        except ValueError:
            valid = ", ".join(s.value for s in ApplicationStatus)
            raise ApplicationCreateError(
                f"Invalid status '{status}'. Valid values: {valid}"
            )

        # Check for duplicate: same legacy_job_id or canonical_job_id
        if legacy_job_id:
            existing = await self._find_by_legacy_job_id(session, legacy_job_id)
            if existing:
                raise DuplicateApplicationError(legacy_job_id, existing.application_id)

        if canonical_job_id:
            existing = await self._find_by_canonical_job_id(session, canonical_job_id)
            if existing:
                raise DuplicateApplicationError(canonical_job_id, existing.application_id)

        now = _utcnow()
        app_id = generate_application_id()

        app = Application(
            application_id=app_id,
            canonical_job_id=canonical_job_id,
            legacy_job_id=legacy_job_id,
            status=status_enum.value,
            status_changed_at=now,
            notes=notes,
            tags=tags,
            custom_fields=custom_fields,
            applied_at=applied_at,
            applied_via=applied_via,
            is_archived=False,
            created_at=now,
        )

        session.add(app)

        # Record initial status in history
        history = ApplicationStatusHistory(
            application_id=app_id,
            old_status=None,
            new_status=status_enum.value,
            changed_at=now,
            change_source=ChangeSource.USER.value,
            note=f"Application created with status '{status_enum.value}'",
        )
        session.add(history)

        await session.flush()
        return app

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_application(
        self,
        session: AsyncSession,
        application_id: str,
    ) -> Optional[Application]:
        """Get a single application by ID. Returns None if not found."""
        stmt = select(Application).where(
            Application.application_id == application_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_applications(
        self,
        session: AsyncSession,
        *,
        status: Optional[str] = None,
        is_archived: bool = False,
        tags: Optional[list[str]] = None,
        page: int = 1,
        limit: int = 50,
    ) -> list[Application]:
        """
        List applications with filtering and pagination.

        Args:
            status: Filter by status value (optional)
            is_archived: Filter by archive state (default: False = active only)
            tags: Filter by tags (any match) — Note: JSON containment is limited
                  in SQLite, so this does a basic string match for now.
            page: Page number (1-indexed)
            limit: Page size (default 50, max 200)
        """
        limit = min(limit, 200)
        offset = (max(page, 1) - 1) * limit

        conditions = [Application.is_archived == is_archived]

        if status is not None:
            conditions.append(Application.status == status)

        stmt = (
            select(Application)
            .where(and_(*conditions))
            .order_by(Application.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await session.execute(stmt)
        applications = list(result.scalars().all())

        # Post-filter by tags if needed (SQLite JSON support is limited)
        if tags:
            applications = [
                app for app in applications
                if app.tags and any(t in app.tags for t in tags)
            ]

        return applications

    # ------------------------------------------------------------------
    # Update (user-owned fields)
    # ------------------------------------------------------------------

    async def update_application(
        self,
        session: AsyncSession,
        application_id: str,
        **fields,
    ) -> Application:
        """
        Update user-owned fields on an application.

        Only the following fields are allowed:
          notes, tags, custom_fields, applied_at, applied_via,
          reminder_at, reminder_note, follow_up_at

        Raises ApplicationNotFoundError if the application does not exist.
        Raises ValueError if any disallowed field is provided.
        """
        # Validate fields
        disallowed = set(fields.keys()) - _USER_UPDATABLE_FIELDS
        if disallowed:
            raise ValueError(
                f"Cannot update these fields via update_application: "
                f"{', '.join(sorted(disallowed))}. "
                f"Use update_status() for status changes."
            )

        app = await self.get_application(session, application_id)
        if app is None:
            raise ApplicationNotFoundError(application_id)

        for key, value in fields.items():
            setattr(app, key, value)

        app.updated_at = _utcnow()
        await session.flush()
        return app

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    async def update_status(
        self,
        session: AsyncSession,
        application_id: str,
        new_status: str,
        change_source: str = "user",
        note: Optional[str] = None,
    ) -> Application:
        """
        Transition an application to a new status.

        Validates the transition against the state machine.
        Records the change in application_status_history.
        Auto-sets relevant timestamp fields (applied_at, offer_at, etc.)
        based on the new status.

        Args:
            application_id: The application to update
            new_status: Target status (must be a valid ApplicationStatus value)
            change_source: Who triggered this (user|system|auto)
            note: Optional note about the change

        Raises:
            ApplicationNotFoundError: if application_id not found
            InvalidStatusTransitionError: if transition is not allowed
        """
        # Validate new_status
        try:
            new_status_enum = ApplicationStatus(new_status)
        except ValueError:
            valid = ", ".join(s.value for s in ApplicationStatus)
            raise ValueError(f"Invalid status '{new_status}'. Valid values: {valid}")

        # Validate change_source
        try:
            source_enum = ChangeSource(change_source)
        except ValueError:
            valid = ", ".join(s.value for s in ChangeSource)
            raise ValueError(
                f"Invalid change_source '{change_source}'. Valid values: {valid}"
            )

        app = await self.get_application(session, application_id)
        if app is None:
            raise ApplicationNotFoundError(application_id)

        current_status = ApplicationStatus(app.status)

        # Validate transition
        allowed = VALID_STATUS_TRANSITIONS.get(current_status, set())
        if new_status_enum not in allowed:
            raise InvalidStatusTransitionError(
                current=current_status.value,
                requested=new_status_enum.value,
                allowed={s.value for s in allowed},
            )

        now = _utcnow()
        old_status = app.status

        # Update status
        app.status = new_status_enum.value
        app.status_changed_at = now
        app.updated_at = now

        # Auto-set timestamp fields based on new status
        ts_field = STATUS_TIMESTAMP_MAP.get(new_status_enum)
        if ts_field and getattr(app, ts_field) is None:
            setattr(app, ts_field, now)

        # Record in history
        history = ApplicationStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status_enum.value,
            changed_at=now,
            change_source=source_enum.value,
            note=note,
        )
        session.add(history)

        await session.flush()
        return app

    # ------------------------------------------------------------------
    # Status history
    # ------------------------------------------------------------------

    async def get_status_history(
        self,
        session: AsyncSession,
        application_id: str,
    ) -> list[ApplicationStatusHistory]:
        """
        Get the full status history for an application, ordered by changed_at DESC.
        """
        stmt = (
            select(ApplicationStatusHistory)
            .where(ApplicationStatusHistory.application_id == application_id)
            .order_by(ApplicationStatusHistory.changed_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Archive / Unarchive
    # ------------------------------------------------------------------

    async def archive_application(
        self,
        session: AsyncSession,
        application_id: str,
    ) -> Application:
        """Archive an application (hide from active views)."""
        app = await self.get_application(session, application_id)
        if app is None:
            raise ApplicationNotFoundError(application_id)

        app.is_archived = True
        app.updated_at = _utcnow()
        await session.flush()
        return app

    async def unarchive_application(
        self,
        session: AsyncSession,
        application_id: str,
    ) -> Application:
        """Unarchive an application (restore to active views)."""
        app = await self.get_application(session, application_id)
        if app is None:
            raise ApplicationNotFoundError(application_id)

        app.is_archived = False
        app.updated_at = _utcnow()
        await session.flush()
        return app

    # ------------------------------------------------------------------
    # Reminders and follow-ups
    # ------------------------------------------------------------------

    async def get_due_reminders(
        self,
        session: AsyncSession,
        before: datetime,
    ) -> list[Application]:
        """Get applications with reminders due before the given time."""
        stmt = (
            select(Application)
            .where(
                and_(
                    Application.reminder_at.isnot(None),
                    Application.reminder_at <= before,
                    Application.is_archived == False,  # noqa: E712
                )
            )
            .order_by(Application.reminder_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_due_followups(
        self,
        session: AsyncSession,
        before: datetime,
    ) -> list[Application]:
        """Get applications with follow-ups due before the given time."""
        stmt = (
            select(Application)
            .where(
                and_(
                    Application.follow_up_at.isnot(None),
                    Application.follow_up_at <= before,
                    Application.is_archived == False,  # noqa: E712
                )
            )
            .order_by(Application.follow_up_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Canonical job linking (future M4 integration)
    # ------------------------------------------------------------------

    async def link_canonical_job(
        self,
        session: AsyncSession,
        application_id: str,
        canonical_job_id: str,
    ) -> Application:
        """
        Link an application to a canonical job ID.

        For future M4 integration — updates canonical_job_id on an
        existing application record.
        """
        app = await self.get_application(session, application_id)
        if app is None:
            raise ApplicationNotFoundError(application_id)

        app.canonical_job_id = canonical_job_id
        app.updated_at = _utcnow()
        await session.flush()
        return app

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _find_by_legacy_job_id(
        self,
        session: AsyncSession,
        legacy_job_id: str,
    ) -> Optional[Application]:
        """Find an existing (non-archived) application by legacy_job_id."""
        stmt = select(Application).where(
            and_(
                Application.legacy_job_id == legacy_job_id,
                Application.is_archived == False,  # noqa: E712
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_by_canonical_job_id(
        self,
        session: AsyncSession,
        canonical_job_id: str,
    ) -> Optional[Application]:
        """Find an existing (non-archived) application by canonical_job_id."""
        stmt = select(Application).where(
            and_(
                Application.canonical_job_id == canonical_job_id,
                Application.is_archived == False,  # noqa: E712
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
