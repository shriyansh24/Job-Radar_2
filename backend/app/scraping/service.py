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

    async def close(self) -> None:
        """Cleanup all scraper resources."""
        for scraper in self._scrapers.values():
            await scraper.close()
