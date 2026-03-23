from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.models import Application, ApplicationStatusHistory
from app.pipeline.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    PipelineView,
    StatusTransition,
)
from app.pipeline.state_machine import (
    validate_transition,
)
from app.shared.errors import NotFoundError
from app.shared.pagination import PaginatedResponse

logger = structlog.get_logger()


class PipelineService:
    def __init__(
        self,
        db: AsyncSession,
        task_factory: Callable[[Awaitable[None]], asyncio.Task[None]] | None = None,
    ):
        self.db = db
        bind = db.bind
        if bind is None:
            raise RuntimeError("PipelineService requires a bound database session")
        self._session_factory = async_sessionmaker(
            bind,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._task_factory = task_factory or asyncio.create_task

    async def list_applications(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> PaginatedResponse:
        from sqlalchemy import func

        query = select(Application).where(Application.user_id == user_id)
        total = await self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        offset = (page - 1) * page_size
        result = await self.db.scalars(
            query.order_by(Application.updated_at.desc()).offset(offset).limit(page_size)
        )
        return PaginatedResponse(
            items=list(result.all()),
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_application(self, data: ApplicationCreate, user_id: uuid.UUID) -> Application:
        app = Application(
            user_id=user_id,
            job_id=data.job_id,
            company_name=data.company_name,
            position_title=data.position_title,
            source=data.source,
            notes=data.notes,
            resume_version_id=data.resume_version_id,
            status="saved",
        )
        self.db.add(app)
        await self.db.flush()  # Ensure app.id is populated

        # Initial history entry
        history = ApplicationStatusHistory(
            application_id=app.id,
            old_status=None,
            new_status="saved",
            change_source="system",
            note="Application created",
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def get_application(self, app_id: uuid.UUID, user_id: uuid.UUID) -> Application:
        result = await self.db.execute(
            select(Application).where(
                Application.id == app_id,
                Application.user_id == user_id,
            )
        )
        app = result.scalar_one_or_none()
        if app is None:
            raise NotFoundError(f"Application {app_id} not found")
        return app

    async def update_application(
        self, app_id: uuid.UUID, data: ApplicationUpdate, user_id: uuid.UUID
    ) -> Application:
        app = await self.get_application(app_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(app, key, value)
        app.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def transition_status(
        self, app_id: uuid.UUID, transition: StatusTransition, user_id: uuid.UUID
    ) -> Application:
        app = await self.get_application(app_id, user_id)
        old_status = app.status
        new_status = transition.new_status

        validate_transition(old_status, new_status)

        app.status = new_status
        now = datetime.now(timezone.utc)
        app.updated_at = now
        if new_status == "applied":
            app.applied_at = now
        elif new_status == "offer":
            app.offer_at = now
        elif new_status == "rejected":
            app.rejected_at = now

        history = ApplicationStatusHistory(
            application_id=app.id,
            old_status=old_status,
            new_status=new_status,
            change_source=transition.change_source,
            note=transition.note,
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(app)

        # Auto-trigger interview prep when entering "interviewing" stage
        if new_status == "interviewing" and app.user_id is not None:
            try:
                self._schedule_interview_prep(app.id, app.user_id)
            except Exception:
                logger.warning(
                    "pipeline.interview_prep_schedule_failed",
                    application_id=str(app.id),
                    exc_info=True,
                )

        return app

    async def get_pipeline_view(self, user_id: uuid.UUID) -> PipelineView:
        result = await self.db.scalars(
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.updated_at.desc())
        )
        apps = result.all()
        view = PipelineView()
        for app in apps:
            bucket = getattr(view, app.status, None)
            if bucket is not None:
                bucket.append(ApplicationResponse.model_validate(app))
        return view

    def _schedule_interview_prep(
        self, application_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        self._task_factory(
            self._run_interview_prep_in_background(application_id, user_id)
        )

    async def _run_interview_prep_in_background(
        self, application_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        try:
            from app.interview.prep_engine import InterviewPrepEngine

            async with self._session_factory() as db:
                engine = InterviewPrepEngine(db)
                await engine.generate_prep(
                    application_id=application_id,
                    user_id=user_id,
                    stage="general",
                )
                logger.info(
                    "pipeline.interview_prep_auto_triggered",
                    application_id=str(application_id),
                )
        except Exception:
            # Best-effort: don't fail the status transition if prep fails
            logger.warning(
                "pipeline.interview_prep_auto_trigger_failed",
                application_id=str(application_id),
                exc_info=True,
            )

    async def get_history(
        self, app_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[ApplicationStatusHistory]:
        # Verify ownership
        await self.get_application(app_id, user_id)
        result = await self.db.scalars(
            select(ApplicationStatusHistory)
            .where(ApplicationStatusHistory.application_id == app_id)
            .order_by(ApplicationStatusHistory.changed_at.asc())
        )
        return list(result.all())
