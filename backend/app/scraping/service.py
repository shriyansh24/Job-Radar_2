from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urlparse

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.scraping.deduplication import DeduplicationService
from app.scraping.execution.request_cache import (
    build_conditional_headers,
    extract_response_cache_headers,
)
from app.scraping.execution.robots_policy import evaluate_robots
from app.scraping.port import ScrapedJob, ScraperPort
from app.scraping.rate_limiter import CircuitBreaker, TokenBucketLimiter
from app.scraping.scrapers.adaptive_parser import AdaptiveCareerParser
from app.scraping.scrapers.apify import ApifyScraper
from app.scraping.scrapers.ashby import AshbyScraper
from app.scraping.scrapers.career_page import CareerPageScraper
from app.scraping.scrapers.greenhouse import GreenhouseScraper
from app.scraping.scrapers.jobspy import JobSpyScraper
from app.scraping.scrapers.lever import LeverScraper
from app.scraping.scrapers.serpapi import SerpAPIScraper
from app.scraping.scrapers.theirstack import TheirStackScraper
from app.scraping.service_parts import (
    complete_run_record,
    compute_job_id,
    create_run_record,
    persist_jobs,
    scraped_job_to_dict,
)

logger = structlog.get_logger()
EventCallback = Callable[[dict[str, object]], Any]


@dataclass
class ScraperRunResult:
    run_id: uuid.UUID | None = None
    jobs_found: int = 0
    jobs_new: int = 0
    jobs_updated: int = 0
    errors: list[str] = field(default_factory=list)


def _safe_failure_message(source_name: str, reason: str) -> str:
    return f"{source_name}: {reason}"


class ScrapingService:
    """Orchestrates scraping across all sources."""

    SOURCE_FETCH_TIMEOUT_S = 300.0
    PAGINATION_TIMEOUT_S = 30.0
    ROBOTS_TIMEOUT_S = 10.0

    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self._scrapers: dict[str, ScraperPort] = {}
        self._rate_limiters: dict[str, TokenBucketLimiter] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._init_scrapers()

    def _init_scrapers(self) -> None:
        """Initialize all available scrapers based on configured API keys."""
        scraper_classes: list[type[Any]] = [
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
            scraper = cast(ScraperPort, cls(self.settings))
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
        event_callback: EventCallback | None = None,
    ) -> ScraperRunResult:
        """Run scrapers, dedup results, save to DB, broadcast events."""
        start = time.monotonic()
        active_sources = sources or list(self._scrapers.keys())
        result = ScraperRunResult()

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
                jobs = await asyncio.wait_for(
                    scraper.fetch_jobs(query, location),
                    timeout=self.SOURCE_FETCH_TIMEOUT_S,
                )
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
                    try:
                        await event_callback(
                            {
                                "type": "scraper_progress",
                                "source": source_name,
                                "count": len(jobs),
                            }
                        )
                    except Exception as exc:
                        logger.warning(
                            "scraper_progress_event_failed",
                            source=source_name,
                            error=str(exc),
                        )
            except Exception as exc:
                cb.record_failure()
                result.errors.append(_safe_failure_message(source_name, "scrape failed"))
                logger.error("scraper_failed", source=source_name, error=str(exc))

        deduper = DeduplicationService()
        unique_jobs = deduper.deduplicate(all_jobs)

        new_count, updated_count = await self._persist_jobs(unique_jobs, user_id)
        result.jobs_found = len(all_jobs)
        result.jobs_new = new_count
        result.jobs_updated = updated_count

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
        return await create_run_record(self.db, sources=sources, user_id=user_id)

    async def _complete_run_record(
        self,
        run_id: uuid.UUID | None,
        result: ScraperRunResult,
        elapsed: float,
    ) -> None:
        await complete_run_record(
            self.db,
            run_id=run_id,
            jobs_found=result.jobs_found,
            jobs_new=result.jobs_new,
            jobs_updated=result.jobs_updated,
            errors=result.errors,
            elapsed=elapsed,
        )

    async def _persist_jobs(
        self, jobs: list[ScrapedJob], user_id: uuid.UUID | None
    ) -> tuple[int, int]:
        return await persist_jobs(self.db, jobs, user_id)

    @staticmethod
    def _compute_job_id(job: ScrapedJob) -> str:
        return compute_job_id(job)

    @staticmethod
    def _scraped_to_dict(job: ScrapedJob) -> dict[str, Any]:
        return scraped_job_to_dict(job)

    async def run_target_batch(
        self,
        targets: list[Any],
        run_id: uuid.UUID,
        adapter_registry: Any,
        browser_pool: Any,
    ) -> dict[str, Any]:
        """Execute scraping for a batch of targets using the tier-based pipeline."""
        from app.scraping.control.tier_router import TierRouter
        from app.scraping.execution.escalation_engine import should_escalate
        from app.scraping.models import ScrapeAttempt

        succeeded_target_ids: set[uuid.UUID] = set()
        robots_cache: dict[str, Any] = {}

        results: dict[str, Any] = {
            "jobs_found": 0,
            "targets_attempted": 0,
            "targets_succeeded": 0,
            "targets_failed": 0,
            "errors": [],
            "succeeded_target_ids": succeeded_target_ids,
        }

        async def process_target(target: Any) -> None:
            plan = TierRouter.route(target)
            steps = [plan.primary_step] + list(plan.fallback_chain)
            user_agent = self._scraping_user_agent()

            if plan.primary_tier > 0:
                robots = await evaluate_robots(
                    target.url,
                    user_agent,
                    robots_cache,
                    timeout_s=self.ROBOTS_TIMEOUT_S,
                )
                if robots.reason not in {"robots_allowed", "unsupported_scheme"}:
                    log_method = logger.warning if robots.allowed else logger.info
                    log_method(
                        "robots_policy_evaluated",
                        target_url=target.url,
                        allowed=robots.allowed,
                        reason=robots.reason,
                        robots_url=robots.robots_url,
                        from_cache=robots.from_cache,
                    )
                if not robots.allowed:
                    attempt = ScrapeAttempt(
                        run_id=run_id,
                        target_id=target.id,
                        selected_tier=plan.primary_tier,
                        actual_tier_used=plan.primary_step.tier,
                        scraper_name=plan.primary_step.scraper_name,
                        parser_name=plan.primary_step.parser_name,
                        status="blocked",
                        error_class="robots_disallowed",
                        error_message="Fetch blocked by robots.txt policy",
                        content_hash_before=target.content_hash,
                    )
                    self.db.add(attempt)
                    self._mark_target_failure(target, http_status=None)
                    results["targets_failed"] += 1
                    results["targets_attempted"] += 1
                    results["errors"].append(
                        f"{getattr(target, 'company_name', 'unknown')}: blocked by robots.txt"
                    )
                    return

            for step_idx, step in enumerate(steps):
                attempt = ScrapeAttempt(
                    run_id=run_id,
                    target_id=target.id,
                    selected_tier=plan.primary_tier,
                    actual_tier_used=step.tier,
                    scraper_name=step.scraper_name,
                    parser_name=step.parser_name,
                    escalations=step_idx,
                    content_hash_before=target.content_hash,
                )

                try:
                    binding = adapter_registry.get(step.scraper_name)
                    _adapter, method = adapter_registry.resolve(step.scraper_name)

                    if binding.method == "fetch_jobs":
                        token = target.ats_board_token or target.url
                        jobs = self._normalize_target_jobs(
                            await method(token),
                            target=target,
                            default_source=getattr(target, "ats_vendor", None)
                            or step.scraper_name,
                        )
                        await self._persist_jobs(jobs, getattr(target, "user_id", None))
                        attempt.jobs_extracted = len(jobs)
                        attempt.status = "success"
                        attempt.http_status = 200
                        self._mark_target_success(
                            target,
                            tier=step.tier,
                            status_code=200,
                        )
                        self.db.add(attempt)
                        results["jobs_found"] += len(jobs)
                        results["targets_succeeded"] += 1
                        succeeded_target_ids.add(target.id)
                        break

                    if binding.is_browser:
                        domain = urlparse(target.url).netloc
                        async with browser_pool.acquire(step.tier, domain):
                            result = await asyncio.wait_for(
                                method(target.url, timeout_s=step.timeout_s),
                                timeout=step.timeout_s + 5,
                            )
                    else:
                        request_headers = build_conditional_headers(
                            getattr(target, "etag", None),
                            getattr(target, "last_modified", None),
                        )
                        if request_headers:
                            logger.info(
                                "conditional_request_headers_applied",
                                target_url=target.url,
                                headers=sorted(request_headers.keys()),
                            )
                        result = await method(
                            target.url,
                            timeout_s=step.timeout_s,
                            user_agent=user_agent,
                            headers=request_headers or None,
                        )

                    attempt.http_status = result.status_code
                    attempt.content_hash_after = result.content_hash
                    attempt.duration_ms = result.duration_ms
                    attempt.content_changed = self._content_changed(
                        target.content_hash,
                        result.content_hash,
                    )

                    if result.status_code == 304:
                        attempt.status = "success"
                        attempt.jobs_extracted = 0
                        self._mark_target_success(
                            target,
                            tier=step.tier,
                            status_code=304,
                        )
                        self.db.add(attempt)
                        logger.info(
                            "target_not_modified",
                            target_url=target.url,
                            scraper=step.scraper_name,
                        )
                        results["targets_succeeded"] += 1
                        succeeded_target_ids.add(target.id)
                        break

                    if result.status_code != 200:
                        decision = should_escalate(
                            status_code=result.status_code,
                            jobs_found=0,
                            html_length=len(result.html),
                            html_snippet=result.html[:2000],
                        )
                        if decision:
                            attempt.status = "escalated"
                            attempt.error_class = decision.reason.value
                            self.db.add(attempt)
                            continue
                        attempt.status = "failed"
                        attempt.error_class = f"http_{result.status_code}"
                        self.db.add(attempt)
                        continue

                    jobs = await self._extract_target_jobs(
                        target=target,
                        step=step,
                        binding=binding,
                        method=method,
                        browser_pool=browser_pool,
                        first_page_html=result.html,
                        user_agent=user_agent,
                    )

                    decision = should_escalate(
                        status_code=result.status_code,
                        jobs_found=len(jobs),
                        html_length=len(result.html),
                        html_snippet=result.html[:2000],
                    )
                    if decision:
                        attempt.status = "escalated"
                        attempt.error_class = decision.reason.value
                        self.db.add(attempt)
                        continue

                    response_etag, response_last_modified = extract_response_cache_headers(
                        getattr(result, "headers", None)
                    )
                    if build_conditional_headers(
                        getattr(target, "etag", None),
                        getattr(target, "last_modified", None),
                    ) and not (response_etag or response_last_modified):
                        logger.info(
                            "conditional_request_cache_headers_missing",
                            target_url=target.url,
                            scraper=step.scraper_name,
                        )

                    await self._persist_jobs(jobs, getattr(target, "user_id", None))

                    attempt.jobs_extracted = len(jobs)
                    attempt.status = "success"
                    self._mark_target_success(
                        target,
                        tier=step.tier,
                        status_code=result.status_code,
                        content_hash=result.content_hash,
                        etag=response_etag,
                        last_modified=response_last_modified,
                    )
                    self.db.add(attempt)
                    results["jobs_found"] += len(jobs)
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
                    attempt.error_message = "Scrape attempt failed"
                    self.db.add(attempt)
                    continue

            else:
                self._mark_target_failure(target, http_status=attempt.http_status)
                results["targets_failed"] += 1
                company = getattr(target, "company_name", "unknown")
                results["errors"].append(f"{company}: all tiers exhausted")

            results["targets_attempted"] += 1

        for target in targets:
            try:
                await process_target(target)
            except Exception as error:
                results["targets_failed"] += 1
                results["errors"].append("target task failed")
                logger.error(
                    "target_batch_aborted",
                    errors=[str(error)],
                )
                await self.db.rollback()
                return results

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()

        return results

    def _scraping_user_agent(self) -> str:
        normalized = self.settings.app_name.replace(" ", "")
        return f"{normalized}/1.0"

    def _normalize_target_jobs(
        self,
        jobs: list[Any],
        *,
        target: Any,
        default_source: str,
    ) -> list[ScrapedJob]:
        normalized: list[ScrapedJob] = []
        seen_keys: set[tuple[str, str]] = set()
        company_name = getattr(target, "company_name", "") or ""

        for entry in jobs:
            if isinstance(entry, ScrapedJob):
                raw = entry
                job = ScrapedJob(
                    title=raw.title.strip(),
                    company_name=raw.company_name or company_name,
                    source=raw.source or default_source,
                    source_url=raw.source_url or getattr(target, "url", None),
                    location=raw.location,
                    remote_type=raw.remote_type,
                    description_raw=raw.description_raw,
                    salary_min=raw.salary_min,
                    salary_max=raw.salary_max,
                    salary_period=raw.salary_period,
                    salary_currency=raw.salary_currency,
                    experience_level=raw.experience_level,
                    job_type=raw.job_type,
                    posted_at=raw.posted_at,
                    company_domain=raw.company_domain,
                    company_logo_url=raw.company_logo_url,
                    ats_job_id=raw.ats_job_id,
                    ats_provider=raw.ats_provider,
                    extra_data={
                        **raw.extra_data,
                        "source_target_id": getattr(target, "id", None),
                    },
                )
            else:
                title = str(entry.get("title", "")).strip()
                if not title:
                    continue
                job = ScrapedJob(
                    title=title,
                    company_name=str(entry.get("company_name") or company_name),
                    source=default_source,
                    source_url=str(entry.get("url") or entry.get("source_url") or target.url),
                    location=self._optional_string(entry.get("location")),
                    remote_type=self._optional_string(entry.get("remote_type")),
                    description_raw=self._optional_string(entry.get("description_raw")),
                    salary_min=cast(float | None, entry.get("salary_min")),
                    salary_max=cast(float | None, entry.get("salary_max")),
                    salary_period=self._optional_string(entry.get("salary_period")),
                    experience_level=self._optional_string(entry.get("experience_level")),
                    job_type=self._optional_string(entry.get("job_type")),
                    company_domain=self._optional_string(entry.get("company_domain")),
                    company_logo_url=self._optional_string(entry.get("company_logo_url")),
                    ats_job_id=self._optional_string(entry.get("ats_job_id")),
                    ats_provider=self._optional_string(entry.get("ats_provider")),
                    extra_data={"source_target_id": getattr(target, "id", None)},
                )

            key = ((job.source_url or "").strip().lower(), job.title.strip().lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)
            normalized.append(job)

        return normalized

    async def _extract_target_jobs(
        self,
        *,
        target: Any,
        step: Any,
        binding: Any,
        method: Any,
        browser_pool: Any,
        first_page_html: str,
        user_agent: str,
    ) -> list[ScrapedJob]:
        from app.scraping.execution.page_crawler import PageCrawler

        source_kind = getattr(target, "source_kind", None)
        ats_vendor = getattr(target, "ats_vendor", None)
        default_source = ats_vendor or source_kind or "career_page"

        if source_kind == "career_page" and not ats_vendor:
            crawler = PageCrawler()

            async def _fetch_page(url: str) -> str:
                if binding.is_browser:
                    domain = urlparse(url).netloc
                    async with browser_pool.acquire(step.tier, domain):
                        page_result = await asyncio.wait_for(
                            method(url, timeout_s=step.timeout_s),
                            timeout=step.timeout_s + 5,
                        )
                else:
                    page_result = await method(
                        url,
                        timeout_s=step.timeout_s,
                        user_agent=user_agent,
                    )
                return cast(str, page_result.html)

            def _parse_page(html: str, url: str) -> list[dict[str, Any]]:
                parser = AdaptiveCareerParser(
                    html=html,
                    company_name=getattr(target, "company_name", "") or "",
                    base_url=url,
                )
                return cast(list[dict[str, Any]], parser.extract())

            try:
                pagination_result = await asyncio.wait_for(
                    crawler.crawl(
                        start_url=target.url,
                        first_page_html=first_page_html,
                        fetch_fn=_fetch_page,
                        parse_fn=_parse_page,
                    ),
                    timeout=self.PAGINATION_TIMEOUT_S,
                )
            except Exception as exc:
                logger.warning(
                    "pagination_error",
                    target_url=target.url,
                    error=str(exc),
                )
            else:
                logger.info(
                    "pagination_complete",
                    target_url=target.url,
                    pages=pagination_result.pages_crawled,
                    stopped_reason=pagination_result.stopped_reason,
                    jobs_found=len(pagination_result.jobs),
                )
                return self._normalize_target_jobs(
                    pagination_result.jobs,
                    target=target,
                    default_source=default_source,
                )

        parser = AdaptiveCareerParser(
            html=first_page_html,
            company_name=getattr(target, "company_name", "") or "",
            base_url=target.url,
        )
        return self._normalize_target_jobs(
            cast(list[dict[str, Any]], parser.extract()),
            target=target,
            default_source=default_source,
        )

    def _mark_target_success(
        self,
        target: Any,
        *,
        tier: int,
        status_code: int,
        content_hash: str | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> None:
        target.last_success_at = datetime.now(UTC)
        target.last_success_tier = tier
        target.last_http_status = status_code
        target.consecutive_failures = 0
        if content_hash is not None:
            target.content_hash = content_hash
        if etag is not None or last_modified is not None:
            target.etag = etag
            target.last_modified = last_modified

    def _mark_target_failure(
        self,
        target: Any,
        *,
        http_status: int | None,
    ) -> None:
        target.last_failure_at = datetime.now(UTC)
        target.last_http_status = http_status
        target.consecutive_failures = (getattr(target, "consecutive_failures", 0) or 0) + 1
        target.failure_count = (getattr(target, "failure_count", 0) or 0) + 1

    @staticmethod
    def _content_changed(before: str | None, after: str | None) -> bool | None:
        if before is None or after is None:
            return None
        return before != after

    @staticmethod
    def _optional_string(value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    async def close(self) -> None:
        """Cleanup all scraper resources."""
        for scraper in self._scrapers.values():
            await scraper.close()
