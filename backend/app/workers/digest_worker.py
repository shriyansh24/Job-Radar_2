"""Daily digest worker.

Generates a daily summary of new job matches, application status changes,
and stale applications for each user, then creates a digest notification.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory

logger = structlog.get_logger()


async def run_daily_digest() -> None:
    """Generate daily digest notifications for all active users."""
    from app.auth.models import User

    async with async_session_factory() as db:
        result = await db.scalars(
            select(User.id).where(User.is_active == True)  # noqa: E712
        )
        user_ids = list(result.all())

        if not user_ids:
            return

        logger.info("digest_worker.starting", user_count=len(user_ids))

        generated = 0
        for uid in user_ids:
            try:
                created = await _generate_user_digest(db, uid)
                if created:
                    generated += 1
            except Exception as exc:
                logger.error(
                    "digest_worker.user_failed",
                    user_id=str(uid),
                    error=str(exc),
                )

        await db.commit()
        logger.info("digest_worker.done", digests_created=generated)


async def _generate_user_digest(
    db: AsyncSession, user_id: object
) -> bool:
    """Build and store a digest for a single user. Returns True if created."""
    from app.jobs.models import Job
    from app.notifications.models import Notification
    from app.pipeline.models import Application, ApplicationStatusHistory

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    # 1. New jobs in the last 24h
    new_jobs_q = (
        select(func.count())
        .select_from(Job)
        .where(
            Job.user_id == user_id,
            Job.is_active == True,  # noqa: E712
            Job.created_at > cutoff,
        )
    )
    new_jobs_count: int = (await db.scalar(new_jobs_q)) or 0

    # Top 5 new jobs by match_score for the body text
    top_jobs_q = (
        select(Job.title, Job.company_name, Job.match_score)
        .where(
            Job.user_id == user_id,
            Job.is_active == True,  # noqa: E712
            Job.created_at > cutoff,
        )
        .order_by(Job.match_score.desc().nullslast())
        .limit(5)
    )
    top_jobs_result = await db.execute(top_jobs_q)
    top_jobs = list(top_jobs_result.all())

    # 2. Application status changes in the last 24h
    status_changes_q = (
        select(func.count())
        .select_from(ApplicationStatusHistory)
        .join(Application, ApplicationStatusHistory.application_id == Application.id)
        .where(
            Application.user_id == user_id,
            ApplicationStatusHistory.changed_at > cutoff,
        )
    )
    status_changes_count: int = (await db.scalar(status_changes_q)) or 0

    # 3. Stale applications (applied > 7 days ago, still in applied/screening)
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    stale_apps_q = (
        select(func.count())
        .select_from(Application)
        .where(
            Application.user_id == user_id,
            Application.status.in_(["applied", "screening"]),
            Application.applied_at < stale_cutoff,
            Application.applied_at.isnot(None),
        )
    )
    stale_apps_count: int = (await db.scalar(stale_apps_q)) or 0

    # Skip if nothing to report
    if new_jobs_count == 0 and status_changes_count == 0 and stale_apps_count == 0:
        return False

    # Build digest body
    parts: list[str] = []
    if new_jobs_count > 0:
        parts.append(f"{new_jobs_count} new job(s) discovered")
        for row in top_jobs:
            title, company, score = row
            score_str = f" ({score}%)" if score is not None else ""
            parts.append(f"  - {title} at {company or 'Unknown'}{score_str}")
    if status_changes_count > 0:
        parts.append(f"{status_changes_count} application status change(s)")
    if stale_apps_count > 0:
        parts.append(f"{stale_apps_count} application(s) may need follow-up")

    title = f"Daily Digest: {new_jobs_count} new jobs"
    body = "\n".join(parts)

    notif = Notification(
        user_id=user_id,
        title=title,
        body=body,
        notification_type="daily_digest",
        link="/jobs?sort=created_at&order=desc",
    )
    db.add(notif)

    logger.info(
        "digest_worker.created",
        user_id=str(user_id),
        new_jobs=new_jobs_count,
        status_changes=status_changes_count,
        stale_apps=stale_apps_count,
    )
    return True
