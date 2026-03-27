"""Daily digest worker for queued ops notifications."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory

logger = structlog.get_logger()


async def run_daily_digest(ctx: dict[str, Any] | None = None) -> None:
    """Create daily digest notifications for active users with fresh activity."""
    del ctx

    from app.auth.models import User

    async with async_session_factory() as db:
        result = await db.scalars(select(User.id).where(User.is_active == True))  # noqa: E712
        user_ids = list(result.all())

        if not user_ids:
            logger.info("digest_worker_skipped", reason="no_active_users")
            return

        logger.info("digest_worker_starting", user_count=len(user_ids))

        generated = 0
        for user_id in user_ids:
            try:
                created = await _generate_user_digest(db, user_id)
                if created:
                    generated += 1
            except Exception:
                logger.exception("digest_worker_user_failed", user_id=str(user_id))

        await db.commit()
        logger.info("digest_worker_completed", digests_created=generated)


async def _generate_user_digest(db: AsyncSession, user_id: object) -> bool:
    """Build a digest for one user and stage a notification when there is new activity."""
    from app.jobs.models import Job
    from app.notifications.models import Notification
    from app.pipeline.models import Application, ApplicationStatusHistory

    cutoff = datetime.now(UTC) - timedelta(hours=24)
    stale_cutoff = datetime.now(UTC) - timedelta(days=7)

    new_jobs_count = (
        await db.scalar(
            select(func.count())
            .select_from(Job)
            .where(
                Job.user_id == user_id,
                Job.is_active == True,  # noqa: E712
                Job.created_at > cutoff,
            )
        )
    ) or 0

    top_jobs = list(
        (
            await db.execute(
                select(Job.title, Job.company_name, Job.match_score)
                .where(
                    Job.user_id == user_id,
                    Job.is_active == True,  # noqa: E712
                    Job.created_at > cutoff,
                )
                .order_by(Job.match_score.is_(None), Job.match_score.desc())
                .limit(5)
            )
        ).all()
    )

    status_changes_count = (
        await db.scalar(
            select(func.count())
            .select_from(ApplicationStatusHistory)
            .join(Application, ApplicationStatusHistory.application_id == Application.id)
            .where(
                Application.user_id == user_id,
                ApplicationStatusHistory.changed_at > cutoff,
            )
        )
    ) or 0

    stale_apps_count = (
        await db.scalar(
            select(func.count())
            .select_from(Application)
            .where(
                Application.user_id == user_id,
                Application.status.in_(["applied", "screening"]),
                Application.applied_at.is_not(None),
                Application.applied_at < stale_cutoff,
            )
        )
    ) or 0

    if new_jobs_count == 0 and status_changes_count == 0 and stale_apps_count == 0:
        logger.info("digest_worker_no_changes", user_id=str(user_id))
        return False

    body_lines: list[str] = []
    if new_jobs_count > 0:
        body_lines.append(f"{new_jobs_count} new jobs")
        for title, company_name, match_score in top_jobs:
            score_suffix = f" ({match_score}%)" if match_score is not None else ""
            body_lines.append(f"- {title} at {company_name or 'Unknown'}{score_suffix}")
    if status_changes_count > 0:
        body_lines.append(f"{status_changes_count} status changes")
    if stale_apps_count > 0:
        body_lines.append(f"{stale_apps_count} follow-ups due")

    notification = Notification(
        user_id=user_id,
        title=f"Daily digest: {new_jobs_count} new jobs",
        body="\n".join(body_lines),
        notification_type="daily_digest",
        link="/jobs?sort=created_at&order=desc",
    )
    db.add(notification)

    logger.info(
        "digest_worker_created",
        user_id=str(user_id),
        new_jobs=new_jobs_count,
        status_changes=status_changes_count,
        stale_apps=stale_apps_count,
    )
    return True
