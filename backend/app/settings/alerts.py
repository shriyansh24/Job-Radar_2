from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import structlog
from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.notifications.models import Notification
from app.settings.models import SavedSearch

logger = structlog.get_logger()


@dataclass(frozen=True)
class SavedSearchAlertResult:
    search_id: uuid.UUID
    checked_at: datetime
    new_matches: int
    notification_created: bool
    notification_id: uuid.UUID | None
    link: str


def build_saved_search_query(search: SavedSearch) -> Select[tuple[Job]]:
    filters = search.filters or {}
    query = select(Job).where(Job.is_active.is_(True))

    if search.user_id is not None:
        query = query.where(Job.user_id == search.user_id)
    if query_text := _read_string(filters, "q"):
        pattern = f"%{query_text}%"
        query = query.where(
            or_(
                Job.title.ilike(pattern),
                Job.company_name.ilike(pattern),
                Job.description_clean.ilike(pattern),
            )
        )
    if source := _read_string(filters, "source"):
        query = query.where(Job.source == source)
    if remote_type := _read_string(filters, "remote_type"):
        query = query.where(Job.remote_type == remote_type)
    if experience_level := _read_string(filters, "experience_level"):
        query = query.where(Job.experience_level == experience_level)
    if job_type := _read_string(filters, "job_type"):
        query = query.where(Job.job_type == job_type)
    if status := _read_string(filters, "status"):
        query = query.where(Job.status == status)
    if company_name := _read_string(filters, "company_name"):
        query = query.where(Job.company_name.ilike(f"%{company_name}%"))
    if location := _read_string(filters, "location"):
        query = query.where(Job.location.ilike(f"%{location}%"))

    is_starred = _read_bool(filters, "is_starred")
    if is_starred is not None:
        query = query.where(Job.is_starred.is_(is_starred))

    min_match_score = _read_float(filters, "min_match_score")
    if min_match_score is not None:
        query = query.where(Job.match_score >= min_match_score)

    if search.last_checked_at is not None:
        query = query.where(Job.created_at > search.last_checked_at)

    return query.order_by(Job.created_at.desc())


async def check_saved_search_alert(
    db: AsyncSession,
    search: SavedSearch,
) -> SavedSearchAlertResult:
    checked_at = datetime.now(timezone.utc)
    jobs = list((await db.scalars(build_saved_search_query(search).limit(20))).all())
    jobs_link = build_saved_search_link(search.filters or {})

    search.last_checked_at = checked_at
    search.last_error = None
    search.last_match_count = len(jobs)

    notification: Notification | None = None
    if jobs and search.user_id is not None:
        search.last_matched_at = checked_at
        notification = Notification(
            user_id=search.user_id,
            title=f"Saved search: {search.name}",
            body=(
                f"{len(jobs)} new job(s) matched this saved search."
                if len(jobs) > 0
                else "No new jobs matched this saved search."
            ),
            notification_type="saved_search_alert",
            link=jobs_link,
        )
        db.add(notification)
        await db.flush()
        logger.info(
            "saved_search_alert.matched",
            search_id=str(search.id),
            user_id=str(search.user_id),
            new_matches=len(jobs),
            notification_id=str(notification.id),
        )
    else:
        logger.info(
            "saved_search_alert.checked",
            search_id=str(search.id),
            user_id=str(search.user_id) if search.user_id is not None else None,
            new_matches=0,
        )

    return SavedSearchAlertResult(
        search_id=search.id,
        checked_at=checked_at,
        new_matches=len(jobs),
        notification_created=notification is not None,
        notification_id=notification.id if notification is not None else None,
        link=jobs_link,
    )


def record_saved_search_alert_failure(search: SavedSearch, exc: Exception) -> None:
    search.last_error = str(exc)[:500]
    logger.error(
        "saved_search_alert.failed",
        search_id=str(search.id),
        user_id=str(search.user_id) if search.user_id is not None else None,
        error=str(exc),
    )


def build_saved_search_link(filters: dict[str, Any]) -> str:
    params: dict[str, str] = {}
    for key in (
        "q",
        "source",
        "remote_type",
        "experience_level",
        "job_type",
        "status",
        "company_name",
        "location",
    ):
        value = _read_string(filters, key)
        if value:
            params[key] = value

    is_starred = _read_bool(filters, "is_starred")
    if is_starred is not None:
        params["is_starred"] = "true" if is_starred else "false"

    min_match_score = _read_float(filters, "min_match_score")
    if min_match_score is not None:
        params["min_match_score"] = str(min_match_score)

    if not params:
        return "/jobs"
    return f"/jobs?{urlencode(params)}"


def _read_string(filters: dict[str, Any], key: str) -> str | None:
    value = filters.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return str(value)


def _read_bool(filters: dict[str, Any], key: str) -> bool | None:
    value = filters.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return None


def _read_float(filters: dict[str, Any], key: str) -> float | None:
    value = filters.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
