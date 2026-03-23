from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from tempfile import gettempdir
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from app.auto_apply.ats_detector import ATSDetector
from app.auto_apply.ats_filler import GenericATSFiller
from app.auto_apply.engine import RuleEngine
from app.auto_apply.models import AutoApplyProfile, AutoApplyRule, AutoApplyRun
from app.auto_apply.workday_filler import WorkdayFiller
from app.pipeline.models import Application

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.config import Settings
    from app.enrichment.llm_client import LLMClient
    from app.jobs.models import Job

logger = structlog.get_logger()


class AutoApplyOrchestrator:
    """Orchestrates the full auto-apply flow with Playwright."""

    def __init__(self, db: AsyncSession, settings: Settings, llm_client: LLMClient):
        self.db = db
        self.settings = settings
        self.llm = llm_client

    def _build_screenshot_path(self, run_id: uuid.UUID) -> str:
        """Build a cross-platform temp path for review screenshots."""
        return str(Path(gettempdir()) / f"auto_apply_{run_id}.png")

    async def apply_to_job(
        self,
        job: Job,
        profile: AutoApplyProfile,
        resume_path: str | None = None,
    ) -> AutoApplyRun:
        """Full auto-apply flow for a single job."""
        run = AutoApplyRun(
            user_id=profile.user_id if hasattr(profile, "user_id") else None,
            job_id=job.id,
            status="running",
            started_at=datetime.now(UTC),
        )
        self.db.add(run)
        await self.db.flush()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
                )
                page = await context.new_page()

                apply_url = job.source_url
                if not apply_url:
                    run.status = "failed"
                    run.error_message = "No application URL"
                    await self.db.commit()
                    return run

                await page.goto(apply_url, wait_until="networkidle")

                # Detect ATS
                ats_provider = await ATSDetector.detect_from_page(page)
                run.ats_provider = ats_provider

                # Click Apply button if on job page (not direct application)
                apply_btn = await page.query_selector(
                    'a:has-text("Apply"), button:has-text("Apply")'
                )
                if apply_btn:
                    await apply_btn.click()
                    await page.wait_for_load_state("networkidle")

                # Choose filler based on ATS
                filler: GenericATSFiller
                if ats_provider == "workday":
                    filler = WorkdayFiller(page, profile, self.llm)
                else:
                    filler = GenericATSFiller(page, profile, self.llm)

                # Upload resume if available
                if resume_path and hasattr(filler, "upload_resume"):
                    await filler.upload_resume(resume_path)  # type: ignore[attr-defined]

                # Fill the form
                result = await filler.fill_form()
                run.fields_filled = result["filled"]
                run.fields_missed = result["missed"]

                # Take screenshot
                screenshot = await page.screenshot(full_page=True)
                ss_path = self._build_screenshot_path(run.id)
                with open(ss_path, "wb") as f:
                    f.write(screenshot)
                run.screenshots = [ss_path]

                # NOTE: Do NOT auto-submit. Leave form filled for user review.
                run.status = "filled"
                run.completed_at = datetime.now(UTC)

                await browser.close()

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            logger.error("auto_apply_failed", job_id=job.id, error=str(e))

        await self.db.commit()
        return run

    async def run_batch(self, user_id: uuid.UUID) -> list[AutoApplyRun]:
        """Run auto-apply for all matching jobs based on rules."""
        rules = (
            await self.db.scalars(
                select(AutoApplyRule)
                .where(AutoApplyRule.user_id == user_id, AutoApplyRule.is_active == True)  # noqa: E712
                .order_by(AutoApplyRule.priority.desc())
            )
        ).all()

        if not rules:
            return []

        profile = await self.db.scalar(
            select(AutoApplyProfile).where(
                AutoApplyProfile.user_id == user_id,
                AutoApplyProfile.is_active == True,  # noqa: E712
            )
        )
        if not profile:
            return []

        engine = RuleEngine()
        candidate_jobs = await self._get_candidate_jobs(user_id)
        matched_jobs = engine.match_jobs(candidate_jobs, list(rules))

        runs: list[AutoApplyRun] = []
        for job, rule in matched_jobs[:10]:  # Max 10 per batch
            run = await self.apply_to_job(job, profile)
            run.rule_id = rule.id
            runs.append(run)
            await asyncio.sleep(5)  # Rate limit between applications

        return runs

    async def _get_candidate_jobs(self, user_id: uuid.UUID) -> list[Job]:
        """Get jobs that haven't been applied to yet."""
        from app.jobs.models import Job

        applied_job_ids_result = (
            await self.db.scalars(select(Application.job_id).where(Application.user_id == user_id))
        ).all()

        stmt = select(Job).where(
            Job.user_id == user_id,
            Job.is_active == True,  # noqa: E712
            Job.status == "new",
        )
        if applied_job_ids_result:
            stmt = stmt.where(~Job.id.in_(applied_job_ids_result))

        stmt = stmt.order_by(Job.match_score.desc().nulls_last()).limit(50)
        return list((await self.db.scalars(stmt)).all())
