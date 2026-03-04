import logging
from datetime import timedelta

from rapidfuzz import fuzz
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Job

logger = logging.getLogger(__name__)


async def check_duplicate(
    job_data: dict, session: AsyncSession
) -> str | None:
    """Check if a job is a duplicate. Returns the job_id of the original if duplicate, else None."""
    job_id = job_data.get("job_id", "")

    # Primary check: exact job_id match
    result = await session.execute(select(Job).where(Job.job_id == job_id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing.job_id

    # Cross-source check: same company + similar title + posted within 7 days
    company_domain = job_data.get("company_domain", "")
    company_name = job_data.get("company_name", "")
    title = job_data.get("title", "")

    if not title or (not company_domain and not company_name):
        return None

    # Find candidates: same company
    if company_domain:
        result = await session.execute(
            select(Job).where(
                Job.company_domain == company_domain,
                Job.is_active == True,
            )
        )
    else:
        result = await session.execute(
            select(Job).where(
                Job.company_name == company_name,
                Job.is_active == True,
            )
        )

    candidates = result.scalars().all()

    posted_at = job_data.get("posted_at")

    for candidate in candidates:
        # Title similarity check
        similarity = fuzz.ratio(
            title.lower().strip(), candidate.title.lower().strip()
        )
        if similarity < 92:
            continue

        # Date proximity check (within 7 days)
        if posted_at and candidate.posted_at:
            delta = abs((posted_at - candidate.posted_at).total_seconds())
            if delta > timedelta(days=7).total_seconds():
                continue

        logger.info(
            f"Duplicate found: '{title}' at {company_name} "
            f"matches '{candidate.title}' (similarity: {similarity}%)"
        )
        return candidate.job_id

    return None


async def deduplicate_and_insert(
    job_data: dict, session: AsyncSession
) -> tuple[bool, str]:
    """Insert a job, handling deduplication. Returns (is_new, job_id)."""
    job_id = job_data["job_id"]

    # Check for exact ID match first
    result = await session.execute(select(Job).where(Job.job_id == job_id))
    existing = result.scalar_one_or_none()
    if existing:
        # Update scraped_at to mark it as still active
        await session.execute(
            update(Job)
            .where(Job.job_id == job_id)
            .values(is_active=True)
        )
        return False, job_id

    # Check for cross-source duplicate
    original_id = await check_duplicate(job_data, session)
    if original_id and original_id != job_id:
        job_data["duplicate_of"] = original_id

    job = Job(**job_data)
    session.add(job)

    try:
        await session.commit()
        return True, job_id
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to insert job {job_id}: {e}")
        return False, job_id
