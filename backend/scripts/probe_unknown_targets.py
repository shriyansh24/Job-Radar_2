"""Probe HTTP endpoints of scrape_targets with ats_vendor IS NULL to detect ATS vendor.

Usage (from D:/jobradar-v2/backend):
    python -m scripts.probe_unknown_targets
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Register FK-referenced tables before using ScrapeTarget
import app.auth.models  # noqa: F401
from app.database import async_session_factory
from app.scraping.control.ats_registry import (
    ATS_RULES,
    classify_headers,
    classify_html,
    classify_url,
)
from app.scraping.models import ScrapeTarget

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONCURRENCY = 20  # max simultaneous HTTP connections
BATCH_DELAY = 1.0  # seconds to sleep between batches
REQUEST_TIMEOUT = 5.0  # seconds per request
HTML_CHUNK = 10_240  # bytes of HTML body to fetch

# Additional URL-redirect patterns (checked against final response URL)
_REDIRECT_URL_RULES: list[tuple[str, str]] = [
    ("myworkdayjobs.com", "workday"),
    ("greenhouse.io", "greenhouse"),
    ("jobs.lever.co", "lever"),
    ("ashbyhq.com", "ashby"),
    ("icims.com", "icims"),
    ("smartrecruiters.com", "smartrecruiters"),
    ("jobvite.com", "jobvite"),
    ("breezy.hr", "breezy"),
]

# ATS vendor -> start_tier mapping (mirrors ats_registry)
_VENDOR_START_TIER: dict[str, int] = {rule["vendor"]: rule["start_tier"] for rule in ATS_RULES}


# ---------------------------------------------------------------------------
# HTTP probe logic
# ---------------------------------------------------------------------------


def _vendor_from_redirect_url(url: str) -> str | None:
    """Check the final (post-redirect) URL for known ATS patterns."""
    url_lower = url.lower()
    # Try classify_url first (covers all registry patterns)
    result = classify_url(url_lower)
    if result.vendor:
        return result.vendor
    # Fallback to manual redirect rules
    for pattern, vendor in _REDIRECT_URL_RULES:
        if pattern in url_lower:
            return vendor
    return None


def _vendor_from_html(html: str) -> str | None:
    """Check HTML snippet for ATS-identifying signatures."""
    result = classify_html(html)
    if result:
        return result.vendor

    # Extended checks for ATS vendors with link/iframe patterns
    snippet = html[:HTML_CHUNK].lower()
    extra_checks = [
        ("jobs.ashbyhq.com", "ashby"),
        ("ashby-job-posting", "ashby"),
        ("icims.com", "icims"),
        ("smartrecruiters.com", "smartrecruiters"),
        ("jobvite.com", "jobvite"),
        ("breezy.hr", "breezy"),
        ("lever-jobs-container", "lever"),
        ("jobs.lever.co", "lever"),
    ]
    for signature, vendor in extra_checks:
        if signature in snippet:
            return vendor

    return None


def _check_json_ld(html: str) -> bool:
    """Return True if page has JSON-LD JobPosting structured data."""
    snippet = html[:HTML_CHUNK].lower()
    return '"jobposting"' in snippet or "jobposting" in snippet


async def probe_target(
    client: httpx.AsyncClient,
    target: ScrapeTarget,
) -> tuple[str | None, bool]:
    """
    Probe a single target URL.

    Returns:
        (vendor, json_ld_capable) where vendor is None if not detected.
    """
    url = target.url
    vendor: str | None = None
    json_ld = False

    # ---- Step 1: HEAD request ----
    try:
        head_resp = await client.head(url, follow_redirects=True)
        final_url = str(head_resp.url)

        # Check if redirect landed on a known ATS domain
        if final_url.lower() != url.lower():
            vendor = _vendor_from_redirect_url(final_url)
            if vendor:
                return vendor, False

        # Check response headers
        header_result = classify_headers(dict(head_resp.headers))
        if header_result and header_result.vendor:
            return header_result.vendor, False
    except httpx.HTTPError:
        pass  # HEAD failed; fall through to GET

    if vendor:
        return vendor, False

    # ---- Step 2: Partial GET for HTML body ----
    try:
        async with client.stream("GET", url, follow_redirects=True) as get_resp:
            final_url = str(get_resp.url)

            # Check redirect URL first
            if final_url.lower() != url.lower():
                vendor = _vendor_from_redirect_url(final_url)
                if vendor:
                    return vendor, False

            # Check response headers from GET
            header_result = classify_headers(dict(get_resp.headers))
            if header_result and header_result.vendor:
                return header_result.vendor, False

            # Read first HTML_CHUNK bytes
            raw = b""
            async for chunk in get_resp.aiter_bytes(chunk_size=4096):
                raw += chunk
                if len(raw) >= HTML_CHUNK:
                    break

            html = raw.decode("utf-8", errors="replace")

            vendor = _vendor_from_html(html)
            json_ld = _check_json_ld(html)
    except httpx.HTTPError:
        pass  # GET also failed; leave vendor as None

    return vendor, json_ld


# ---------------------------------------------------------------------------
# Database update helpers
# ---------------------------------------------------------------------------


async def update_target(
    target: ScrapeTarget,
    db: AsyncSession,
    vendor: str | None,
    json_ld: bool,
) -> bool:
    """
    Update target record. Returns True if a change was made.
    """
    changed = False

    if vendor and vendor != "json_ld_capable":
        target.ats_vendor = vendor
        target.source_kind = "ats_board"
        target.start_tier = _VENDOR_START_TIER.get(vendor, 0)
        changed = True
    elif json_ld and not vendor:
        # Mark source_kind without setting an ATS vendor
        # (keeps ats_vendor NULL but hints parser at structured data)
        target.source_kind = "json_ld_career_page"
        changed = True

    if changed:
        await db.flush()

    return changed


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


async def run_probe() -> None:
    # ---- Load unknown targets ----
    async with async_session_factory() as db:
        result = await db.execute(
            select(ScrapeTarget).where(
                ScrapeTarget.ats_vendor.is_(None),
                ScrapeTarget.enabled.is_(True),
            )
        )
        targets: list[ScrapeTarget] = list(result.scalars().all())

    total = len(targets)
    print(f"Found {total} targets with ats_vendor IS NULL and enabled = TRUE")
    if total == 0:
        print("Nothing to probe. Exiting.")
        return

    # ---- Probe in batches of CONCURRENCY ----
    stats: dict[str, int] = defaultdict(int)
    stats["total"] = total
    reclassified = 0
    json_ld_count = 0
    vendor_breakdown: dict[str, int] = defaultdict(int)
    processed = 0
    errors = 0

    limits = httpx.Limits(
        max_connections=CONCURRENCY,
        max_keepalive_connections=CONCURRENCY,
    )
    headers = {
        "User-Agent": ("Mozilla/5.0 (compatible; JobRadarBot/2.0; +https://jobradar.app/bot)"),
    }

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        limits=limits,
        headers=headers,
    ) as client:
        for batch_start in range(0, total, CONCURRENCY):
            batch = targets[batch_start : batch_start + CONCURRENCY]

            tasks = [probe_target(client, target) for target in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # ---- Persist updates inside a single session per batch ----
            async with async_session_factory() as db:
                for target, outcome in zip(batch, results):
                    processed += 1

                    if isinstance(outcome, BaseException):
                        errors += 1
                        print(f"  [GATHER ERROR] {target.url[:80]} -> {type(outcome).__name__}")
                        continue

                    vendor, json_ld = outcome

                    # Re-attach target to this session
                    db_target = await db.merge(target)
                    changed = await update_target(db_target, db, vendor, json_ld)

                    if changed:
                        if vendor and vendor != "json_ld_capable":
                            reclassified += 1
                            vendor_breakdown[vendor] += 1
                        elif json_ld:
                            json_ld_count += 1

                await db.commit()

            if processed % 50 == 0 or processed == total:
                pct = processed / total * 100
                print(
                    f"  Progress: {processed}/{total} ({pct:.1f}%) -> "
                    f"reclassified={reclassified}, json_ld={json_ld_count}, "
                    f"errors={errors}"
                )

            # Polite delay between batches
            if batch_start + CONCURRENCY < total:
                await asyncio.sleep(BATCH_DELAY)

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("PROBE SUMMARY")
    print("=" * 60)
    print(f"  Targets probed       : {processed}")
    print(f"  ATS vendor detected  : {reclassified}")
    print(f"  JSON-LD capable      : {json_ld_count}")
    print(f"  Still unknown        : {processed - reclassified - json_ld_count}")
    print(f"  Errors               : {errors}")
    if vendor_breakdown:
        print("\n  Vendor Breakdown:")
        for vendor, count in sorted(vendor_breakdown.items(), key=lambda item: -item[1]):
            print(f"    {vendor:<25} {count}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(run_probe())
