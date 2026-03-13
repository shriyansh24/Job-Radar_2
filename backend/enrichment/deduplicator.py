import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from rapidfuzz import fuzz
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Job

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 3-Layer deduplication — pure functions (no DB, no async)
# ---------------------------------------------------------------------------

_SIMHASH_BITS = 64


def compute_simhash(text: str) -> int:
    """Return a 64-bit SimHash integer for *text*.

    Algorithm:
      - Split text into whitespace-delimited tokens.
      - For each token compute a 64-bit hash via MD5 (first 8 bytes).
      - Maintain a vote vector of length 64: +1 if the bit is set, -1 otherwise.
      - Final hash: bit i = 1 if vote[i] > 0 else 0.
    """
    if not text:
        return 0

    votes = [0] * _SIMHASH_BITS
    for word in text.lower().split():
        digest = hashlib.md5(word.encode(), usedforsecurity=False).digest()
        # Take first 8 bytes → 64-bit integer (big-endian)
        word_hash = int.from_bytes(digest[:8], "big")
        for bit in range(_SIMHASH_BITS):
            if word_hash & (1 << bit):
                votes[bit] += 1
            else:
                votes[bit] -= 1

    result = 0
    for bit in range(_SIMHASH_BITS):
        if votes[bit] > 0:
            result |= 1 << bit
    return result


def hamming_distance(a: int, b: int) -> int:
    """Return the number of differing bits between two integers."""
    return bin(a ^ b).count("1")


@dataclass
class DedupResult:
    """Return value of :func:`deduplicate_batch`."""

    kept: list[dict[str, Any]] = field(default_factory=list)
    duplicates: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=lambda: {
        "l1_deduped": 0,
        "l2_deduped": 0,
        "l3_deduped": 0,
    })


# Thresholds — tuned for job-posting text
_SIMHASH_NEAR_DUP_THRESHOLD = 3   # bits; <= this → near-duplicate (catches near-identical strings)
_FUZZY_TITLE_THRESHOLD = 90        # token_sort_ratio on *normalized* titles; >= this → duplicate

# Common title abbreviations to expand before fuzzy comparison so that
# e.g. "Sr. Software Engineer" and "Senior Software Engineer" match correctly.
_TITLE_ABBREV = [
    (r"\bsr\b", "senior"),
    (r"\bjr\b", "junior"),
    (r"\bdir\b", "director"),
    (r"\bmgr\b", "manager"),
    (r"\beng\b", "engineer"),
    (r"\bvp\b", "vice president"),
]


def _normalize_title(title: str) -> str:
    """Lower-case, strip punctuation, and expand common abbreviations."""
    t = title.lower().strip()
    # Remove non-alphanumeric characters (preserves spaces)
    t = re.sub(r"[^\w\s]", " ", t)
    for pat, repl in _TITLE_ABBREV:
        t = re.sub(pat, repl, t)
    return " ".join(t.split())


def deduplicate_batch(
    jobs: list[dict[str, Any]],
    existing_hashes: set[str],
) -> DedupResult:
    """Deduplicate a list of job dicts using a three-layer pipeline.

    Layer 1 — Exact ``dedup_hash`` match (against ``existing_hashes`` and
              within the incoming batch itself).
    Layer 2 — SimHash of ``"{title} {company_name} {location}"``; Hamming
              distance ≤ :data:`_SIMHASH_NEAR_DUP_THRESHOLD` → duplicate.
    Layer 3 — Same company + rapidfuzz ``token_sort_ratio(title_a, title_b)``
              ≥ :data:`_FUZZY_TITLE_THRESHOLD` → duplicate.

    The first job in arrival order is always kept; later collisions are marked
    as duplicates.

    Args:
        jobs: List of raw job dicts.  Each dict must have a ``"dedup_hash"``
              key plus ``"title"``, ``"company_name"``, and ``"location"``
              (or ``"location_city"``) for L2/L3.
        existing_hashes: Set of ``dedup_hash`` values already stored in the DB.

    Returns:
        A :class:`DedupResult` with ``kept``, ``duplicates``, and ``stats``.
    """
    result = DedupResult(
        kept=[],
        duplicates=[],
        stats={"l1_deduped": 0, "l2_deduped": 0, "l3_deduped": 0},
    )

    # Accumulated state while iterating
    seen_hashes: set[str] = set()             # exact hashes already kept
    kept_simhashes: list[int] = []            # simhashes of kept jobs
    # company_key → list of (kept_title_lower,) for L3
    company_titles: dict[str, list[str]] = {}

    def _location(job: dict) -> str:
        return job.get("location") or job.get("location_city") or ""

    def _company_key(job: dict) -> str:
        return (job.get("company_domain") or job.get("company_name") or "").lower().strip()

    for job in jobs:
        h = job.get("dedup_hash", "")

        # ── Layer 1: exact hash ──────────────────────────────────────────
        if h in existing_hashes or h in seen_hashes:
            result.duplicates.append(job)
            result.stats["l1_deduped"] += 1
            continue

        title = (job.get("title") or "").strip()
        company_key = _company_key(job)
        location = _location(job)

        # ── Layer 2: SimHash near-duplicate ──────────────────────────────
        fingerprint_text = f"{title} {company_key} {location}"
        sh = compute_simhash(fingerprint_text)

        l2_dup = False
        for kept_sh in kept_simhashes:
            if hamming_distance(sh, kept_sh) <= _SIMHASH_NEAR_DUP_THRESHOLD:
                l2_dup = True
                break

        if l2_dup:
            result.duplicates.append(job)
            result.stats["l2_deduped"] += 1
            continue

        # ── Layer 3: same company + fuzzy title (with abbreviation expansion) ──
        norm_title = _normalize_title(title)
        l3_dup = False
        if company_key and norm_title:
            existing_titles = company_titles.get(company_key, [])
            for kept_norm_title in existing_titles:
                ratio = fuzz.token_sort_ratio(
                    norm_title, kept_norm_title, processor=None
                )
                if ratio >= _FUZZY_TITLE_THRESHOLD:
                    l3_dup = True
                    break

        if l3_dup:
            result.duplicates.append(job)
            result.stats["l3_deduped"] += 1
            continue

        # ── Keep this job ────────────────────────────────────────────────
        result.kept.append(job)
        seen_hashes.add(h)
        kept_simhashes.append(sh)
        if company_key:
            # Store normalized title for subsequent L3 comparisons
            company_titles.setdefault(company_key, []).append(norm_title)

    return result


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
