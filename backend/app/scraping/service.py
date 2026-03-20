from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.scraping.deduplication import DeduplicationService
from app.scraping.port import ScrapedJob, ScraperPort
from app.scraping.rate_limiter import CircuitBreaker, TokenBucketLimiter
from app.scraping.scrapers.apify import ApifyScraper
from app.scraping.scrapers.ashby import AshbyScraper
from app.scraping.scrapers.career_page import CareerPageScraper
from app.scraping.scrapers.greenhouse import GreenhouseScraper
from app.scraping.scrapers.jobspy import JobSpyScraper
from app.scraping.scrapers.lever import LeverScraper
from app.scraping.scrapers.serpapi import SerpAPIScraper
from app.scraping.scrapers.theirstack import TheirStackScraper

logger = structlog.get_logger()


@dataclass
class ScraperRunResult:
    run_id: uuid.UUID | None = None
    jobs_found: int = 0
    jobs_new: int = 0
    jobs_updated: int = 0
    errors: list[str] = field(default_factory=list)


class ScrapingService:
    """Orchestrates scraping across all sources."""

    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self._scrapers: dict[str, ScraperPort] = {}
        self._rate_limiters: dict[str, TokenBucketLimiter] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._init_scrapers()

    def _init_scrapers(self) -> None:
        """Initialize all available scrapers based on configured API keys."""
        scraper_classes: list[type[ScraperPort]] = [
            SerpAPIScraper,
            GreenhouseScraper,
            LeverScraper,
            AshbyScraper,
            JobSpyScraper,
            TheirStackScraper,
            ApifyScraper,
            CareerPageScraper,
        ]
        for cls in scraper_classes:
            scraper = cls(self.settings)  # type: ignore[call-arg]
            name = scraper.source_name
            self._scrapers[name] = scraper
            self._rate_limiters[name] = TokenBucketLimiter(rate=1.0, burst=5)
            self._circuit_breakers[name] = CircuitBreaker()

    @property
    def available_sources(self) -> list[str]:
        return list(self._scrapers.keys())

    async def run_scrape(
        self,
        sources: list[str] | None = None,
        query: str = "",
        location: str | None = None,
        user_id: uuid.UUID | None = None,
        event_callback: Callable | None = None,
    ) -> ScraperRunResult:
        """Run scrapers, dedup results, save to DB, broadcast events."""
        start = time.monotonic()
        active_sources = sources or list(self._scrapers.keys())
        result = ScraperRunResult()

        # Create scraper_run record (lazy import to avoid circular dep with Phase 3A models)
        run_id = await self._create_run_record(active_sources, user_id)
        result.run_id = run_id

        all_jobs: list[ScrapedJob] = []

        for source_name in active_sources:
            scraper = self._scrapers.get(source_name)
            if not scraper:
                continue

            cb = self._circuit_breakers[source_name]
            if not cb.can_execute():
                logger.warning("scraper_circuit_open", source=source_name)
                result.errors.append(f"{source_name}: circuit breaker open")
                continue

            rl = self._rate_limiters[source_name]
            await rl.acquire()

            try:
                source_start = time.monotonic()
                jobs = await scraper.fetch_jobs(query, location)
                elapsed = time.monotonic() - source_start
                all_jobs.extend(jobs)
                cb.record_success()
                logger.info(
                    "scraper_completed",
                    source=source_name,
                    count=len(jobs),
                    duration_s=round(elapsed, 2),
                )
                if event_callback:
                    await event_callback(
                        {
                            "type": "scraper_progress",
                            "source": source_name,
                            "count": len(jobs),
                        }
                    )
            except Exception as e:
                cb.record_failure()
                result.errors.append(f"{source_name}: {e!s}")
                logger.error("scraper_failed", source=source_name, error=str(e))

        # Dedup
        deduper = DeduplicationService()
        unique_jobs = deduper.deduplicate(all_jobs)

        # Save to DB
        new_count, updated_count = await self._persist_jobs(unique_jobs, user_id)
        result.jobs_found = len(all_jobs)
        result.jobs_new = new_count
        result.jobs_updated = updated_count

        # Update run record
        elapsed_total = time.monotonic() - start
        await self._complete_run_record(run_id, result, elapsed_total)

        logger.info(
            "scrape_completed",
            found=result.jobs_found,
            new=result.jobs_new,
            updated=result.jobs_updated,
            errors=len(result.errors),
            duration_s=round(elapsed_total, 2),
        )
        return result

    async def _create_run_record(
        self, sources: list[str], user_id: uuid.UUID | None
    ) -> uuid.UUID | None:
        """Create a scraper_runs record. Returns None if model not available."""
        try:
            from app.scraping.models import ScraperRun

            run = ScraperRun(
                user_id=user_id,
                source=",".join(sources),
                status="running",
            )
            self.db.add(run)
            await self.db.flush()
            return run.id  # type: ignore[return-value]
        except Exception:
            return None

    async def _complete_run_record(
        self,
        run_id: uuid.UUID | None,
        result: ScraperRunResult,
        elapsed: float,
    ) -> None:
        if not run_id:
            return
        try:
            from app.scraping.models import ScraperRun

            run = await self.db.get(ScraperRun, run_id)
            if run:
                run.status = "completed" if not result.errors else "completed_with_errors"
                run.jobs_found = result.jobs_found
                run.jobs_new = result.jobs_new
                run.jobs_updated = result.jobs_updated
                run.error_message = "; ".join(result.errors) if result.errors else None
                run.completed_at = datetime.now(UTC)
                run.duration_seconds = round(elapsed, 2)
            await self.db.commit()
        except Exception:
            pass

    async def _persist_jobs(
        self, jobs: list[ScrapedJob], user_id: uuid.UUID | None
    ) -> tuple[int, int]:
        """Save scraped jobs to DB. Returns (new_count, updated_count)."""
        new_count = 0
        updated_count = 0

        try:
            from app.jobs.models import Job
        except ImportError:
            logger.warning("job_model_not_available", hint="Phase 3A not complete")
            return 0, 0

        for scraped in jobs:
            job_id = self._compute_job_id(scraped)
            existing = await self.db.get(Job, job_id)
            if existing:
                updated_count += 1
            else:
                job = Job(
                    id=job_id,
                    user_id=user_id,
                    **self._scraped_to_dict(scraped),
                )
                self.db.add(job)
                new_count += 1

        try:
            await self.db.commit()
        except Exception as e:
            logger.error("persist_jobs_failed", error=str(e))
            await self.db.rollback()

        return new_count, updated_count

    @staticmethod
    def _compute_job_id(job: ScrapedJob) -> str:
        """SHA-256 of (source + title + company + location) for stable ID."""
        content = f"{job.source}|{job.title}|{job.company_name}|{job.location}"
        return hashlib.sha256(content.encode()).hexdigest()[:64]

    @staticmethod
    def _scraped_to_dict(job: ScrapedJob) -> dict:
        """Convert ScrapedJob to dict for Job ORM model."""
        return {
            "source": job.source,
            "source_url": job.source_url,
            "title": job.title,
            "company_name": job.company_name,
            "company_domain": job.company_domain,
            "company_logo_url": job.company_logo_url,
            "location": job.location,
            "remote_type": job.remote_type,
            "description_raw": job.description_raw,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_period": job.salary_period,
            "salary_currency": job.salary_currency,
            "experience_level": job.experience_level,
            "job_type": job.job_type,
            "posted_at": job.posted_at,
            "scraped_at": datetime.now(UTC),
        }

    async def run_target_batch(
        self,
        targets: list,
        run_id,
        adapter_registry,
        browser_pool,
    ) -> dict:
        """Execute scraping for a batch of targets using the tier-based pipeline.

        This is the new entry point for Mode 1 (career page) and Mode 3 (watchlist)
        scraping.  Each target is routed through the TierRouter to build an
        ExecutionPlan, then steps are tried in order (primary + fallbacks) until
        one succeeds or all are exhausted.

        For custom HTML career pages (source_kind='career_page', no ATS vendor),
        PageCrawler automatically follows pagination to collect jobs from all pages.

        The existing ``run_scrape()`` method (Mode 2, keyword search) is unaffected.
        """
        from app.scraping.control.tier_router import TierRouter
        from app.scraping.execution.escalation_engine import should_escalate
        from app.scraping.execution.page_crawler import PageCrawler
        from app.scraping.models import ScrapeAttempt
        from urllib.parse import urlparse
        import asyncio

        succeeded_target_ids: set = set()

        results: dict = {
            "jobs_found": 0,
            "targets_attempted": 0,
            "targets_succeeded": 0,
            "targets_failed": 0,
            "errors": [],
            "succeeded_target_ids": succeeded_target_ids,
        }

        async def process_target(target) -> None:
            plan = TierRouter.route(target)
            steps = [plan.primary_step] + list(plan.fallback_chain)

            for step_idx, step in enumerate(steps):
                attempt = ScrapeAttempt(
                    run_id=run_id,
                    target_id=target.id,
                    selected_tier=plan.primary_tier,
                    actual_tier_used=step.tier,
                    scraper_name=step.scraper_name,
                    parser_name=step.parser_name,
                    escalations=step_idx,
                )

                try:
                    binding = adapter_registry.get(step.scraper_name)
                    _adapter, method = adapter_registry.resolve(step.scraper_name)

                    # ── ATS / API path ──────────────────────────
                    if binding.method == "fetch_jobs":
                        token = target.ats_board_token or target.url
                        jobs = await method(token)
                        attempt.jobs_extracted = len(jobs) if isinstance(jobs, list) else 0
                        attempt.status = "success"
                        attempt.http_status = 200
                        self.db.add(attempt)
                        results["jobs_found"] += attempt.jobs_extracted
                        results["targets_succeeded"] += 1
                        succeeded_target_ids.add(target.id)
                        break

                    # ── Browser path ────────────────────────────
                    if binding.is_browser:
                        domain = urlparse(target.url).netloc
                        async with browser_pool.acquire(step.tier, domain):
                            result = await asyncio.wait_for(
                                method(target.url, timeout_s=step.timeout_s),
                                timeout=step.timeout_s + 5,
                            )
                    else:
                        # ── Fetcher path ────────────────────────
                        result = await method(target.url, timeout_s=step.timeout_s)

                    # Evaluate fetcher / browser result
                    attempt.http_status = result.status_code
                    attempt.content_hash_after = result.content_hash
                    attempt.duration_ms = result.duration_ms

                    decision = should_escalate(
                        status_code=result.status_code,
                        jobs_found=0,  # job extraction happens downstream
                        html_length=len(result.html),
                        html_snippet=result.html[:2000],
                    )
                    if decision:
                        attempt.status = "escalated"
                        attempt.error_class = decision.reason.value
                        self.db.add(attempt)
                        continue

                    # ── Pagination for custom HTML career pages ──────────
                    # Only follow pagination when:
                    #   - source_kind is 'career_page' (not an ATS API)
                    #   - ats_vendor is not set (custom HTML, not Greenhouse etc.)
                    source_kind = getattr(target, "source_kind", None)
                    ats_vendor = getattr(target, "ats_vendor", None)
                    paginated_jobs: list[dict] = []

                    if source_kind == "career_page" and not ats_vendor:
                        # Build a simple fetch callable that re-uses the same
                        # adapter method used for the first page fetch.
                        async def _fetch_page(url: str) -> str:
                            page_result = await method(url, timeout_s=step.timeout_s)
                            return page_result.html

                        # No-op parser — job extraction is owned by the
                        # downstream parser pipeline, not the crawler.
                        # The crawler returns raw dicts; callers merge them.
                        def _parse_page(html: str, url: str) -> list[dict]:
                            return []  # extraction handled separately

                        crawler = PageCrawler()
                        try:
                            pagination_result = await crawler.crawl(
                                start_url=target.url,
                                first_page_html=result.html,
                                fetch_fn=_fetch_page,
                                parse_fn=_parse_page,
                            )
                            # Record pagination metadata on the attempt
                            attempt.pages_crawled = pagination_result.pages_crawled
                            attempt.pagination_stopped_reason = (
                                pagination_result.stopped_reason
                            )
                            paginated_jobs = pagination_result.jobs
                            logger.info(
                                "pagination_complete",
                                target_url=target.url,
                                pages=pagination_result.pages_crawled,
                                stopped_reason=pagination_result.stopped_reason,
                            )
                        except Exception as exc:
                            # Pagination failure must not prevent the first-page
                            # result from being recorded as a success.
                            logger.warning(
                                "pagination_error",
                                target_url=target.url,
                                error=str(exc),
                            )

                    jobs_count = len(paginated_jobs)
                    attempt.jobs_extracted = jobs_count
                    attempt.status = "success"
                    attempt.content_changed = (result.content_hash != target.content_hash)
                    self.db.add(attempt)
                    results["jobs_found"] += jobs_count
                    results["targets_succeeded"] += 1
                    succeeded_target_ids.add(target.id)
                    break

                except asyncio.TimeoutError:
                    attempt.status = "escalated"
                    attempt.error_class = "timeout"
                    self.db.add(attempt)
                    continue

                except Exception as exc:
                    attempt.status = "failed"
                    attempt.error_class = type(exc).__name__
                    attempt.error_message = str(exc)[:500]
                    self.db.add(attempt)
                    continue

            else:
                # for/else: all steps exhausted without break
                results["targets_failed"] += 1
                company = getattr(target, "company_name", "unknown")
                results["errors"].append(f"{company}: all tiers exhausted")

            results["targets_attempted"] += 1

        tasks = [process_target(t) for t in targets]
        await asyncio.gather(*tasks, return_exceptions=True)

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()

        return results

    async def close(self) -> None:
        """Cleanup all scraper resources."""
        for scraper in self._scrapers.values():
            await scraper.close()
