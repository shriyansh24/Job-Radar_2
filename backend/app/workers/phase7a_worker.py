"""Phase 7A background workers.

Runs company validation, source health checks, staleness sweeps,
and follow-up reminder processing.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.database import async_session_factory

logger = structlog.get_logger()


async def run_staleness_sweep() -> None:
    """Mark canonical jobs not refreshed in 14 days as stale."""
    from app.auth.models import User
    from app.canonical_jobs.service import CanonicalJobService

    async with async_session_factory() as db:
        # Run for all users
        result = await db.scalars(select(User.id))
        user_ids = list(result.all())

        total_stale = 0
        for uid in user_ids:
            svc = CanonicalJobService(db)
            count = await svc.run_staleness_sweep(uid)
            total_stale += count

        if total_stale:
            logger.info("phase7a.staleness_sweep_done", total_marked=total_stale)


async def run_source_health_checks() -> None:
    """Update source health metrics based on recent scraper runs."""
    from app.scraping.models import ScraperRun
    from app.source_health.models import SourceRegistry

    async with async_session_factory() as db:
        # Get all registered sources
        sources = await db.scalars(select(SourceRegistry))

        for source in sources.all():
            # Count recent runs in last 24h
            recent_query = (
                select(ScraperRun)
                .where(
                    ScraperRun.source == source.source_name,
                    ScraperRun.started_at > datetime.now(timezone.utc).replace(hour=0),
                )
                .order_by(ScraperRun.started_at.desc())
                .limit(10)
            )
            try:
                runs_result = await db.scalars(recent_query)
                recent_runs = list(runs_result.all())

                if not recent_runs:
                    continue

                failed = sum(1 for r in recent_runs if r.status == "failed")
                total = len(recent_runs)

                if failed >= total * 0.8:
                    source.health_state = "failing"
                elif failed >= total * 0.5:
                    source.health_state = "degraded"
                else:
                    source.health_state = "healthy"

                source.last_check_at = datetime.now(timezone.utc)
            except Exception as exc:
                logger.error(
                    "phase7a.source_health_check_failed", source=source.source_name, error=str(exc)
                )

        await db.commit()
        logger.info("phase7a.source_health_checks_done")


async def run_followup_reminders() -> None:
    """Send notifications for due follow-up reminders."""
    from app.followup.models import FollowupReminder
    from app.notifications.models import Notification
    from app.pipeline.models import Application

    async with async_session_factory() as db:
        now = datetime.now(timezone.utc)

        # Find unsent reminders that are due
        query = select(FollowupReminder).where(
            FollowupReminder.is_sent == False,  # noqa: E712
            FollowupReminder.reminder_at <= now,
        )
        result = await db.scalars(query)
        reminders = list(result.all())

        for reminder in reminders:
            # Get application details for the notification
            app = await db.scalar(
                select(Application).where(Application.id == reminder.application_id)
            )
            title = "Follow-up reminder"
            body = reminder.reminder_note or "Time to follow up on your application"
            if app:
                title = (
                    f"Follow up: {app.position_title or 'Application'} at "
                    f"{app.company_name or 'company'}"
                )

            notif = Notification(
                user_id=reminder.user_id,
                title=title,
                body=body,
                notification_type="followup",
                link="/pipeline",
            )
            db.add(notif)
            reminder.is_sent = True

        if reminders:
            await db.commit()
            logger.info("phase7a.followup_reminders_sent", count=len(reminders))
