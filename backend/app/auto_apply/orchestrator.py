from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from tempfile import gettempdir
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select

from app.auto_apply.ats_detector import ATSDetector
from app.auto_apply.ats_filler import GenericATSFiller
from app.auto_apply.engine import RuleEngine
from app.auto_apply.field_mapper import FieldMapper
from app.auto_apply.form_extractor import FormExtractor
from app.auto_apply.greenhouse_adapter import GreenhouseBrowserAdapter
from app.auto_apply.lever_adapter import ApplicationResult as LeverApplicationResult
from app.auto_apply.lever_adapter import LeverAPIAdapter
from app.auto_apply.models import AutoApplyProfile, AutoApplyRule, AutoApplyRun
from app.auto_apply.safety import SafetyLayer
from app.auto_apply.workday_adapter import WorkdayBrowserAdapter
from app.pipeline.models import Application

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.config import Settings
    from app.enrichment.llm_client import LLMClient
    from app.jobs.models import Job

logger = structlog.get_logger()


class AutoApplyOrchestrator:
    """Orchestrates the live auto-apply flow for manual and batch execution."""

    REVIEW_COMPLETE_STATUS = "filled"
    SUBMITTED_STATUS = "success"

    def __init__(self, db: AsyncSession, settings: Settings, llm_client: LLMClient | None):
        self.db = db
        self.settings = settings
        self.llm = llm_client

    def _build_screenshot_path(self, run_id: uuid.UUID, index: int = 0) -> str:
        suffix = "" if index == 0 else f"_{index}"
        return str(Path(gettempdir()) / f"auto_apply_{run_id}{suffix}.png")

    async def apply_to_job(
        self,
        job: Job,
        profile: AutoApplyProfile,
        resume_path: str | None = None,
        *,
        rule: AutoApplyRule | None = None,
        allow_first_time_ats: bool = False,
    ) -> AutoApplyRun:
        run = AutoApplyRun(
            user_id=profile.user_id if hasattr(profile, "user_id") else None,
            job_id=job.id,
            rule_id=rule.id if rule else None,
            status="running",
            started_at=datetime.now(UTC),
        )
        self.db.add(run)
        await self.db.flush()

        if profile.user_id is None:
            run.status = "failed"
            run.error_message = "Auto-apply profile is missing a user_id"
            run.completed_at = datetime.now(UTC)
            await self.db.commit()
            return run

        apply_url = job.source_url
        if not apply_url:
            run.status = "failed"
            run.error_message = "No application URL"
            run.completed_at = datetime.now(UTC)
            await self.db.commit()
            return run

        ats_provider = ATSDetector.detect(apply_url)
        run.ats_provider = ats_provider

        safety = await self._build_safety_layer(
            profile.user_id,
            allow_first_time_for={ats_provider} if allow_first_time_ats and ats_provider else None,
        )
        safety_result = await safety.check_safety(
            job_id=job.id,
            user_id=profile.user_id,
            db=self.db,
            ats_provider=ats_provider,
            company_name=job.company_name,
            first_seen_at=job.first_seen_at,
            blacklisted_companies=list(rule.excluded_companies or []) if rule else [],
            blacklisted_keywords=list(rule.excluded_keywords or []) if rule else [],
            job_title=job.title,
        )
        if not safety_result.passed:
            run.status = "failed"
            run.fields_missed = safety_result.failed_checks
            run.error_message = f"Blocked by: {', '.join(safety_result.failed_checks)}"
            run.completed_at = datetime.now(UTC)
            await self.db.commit()
            return run

        lever_target = (
            LeverAPIAdapter.parse_lever_url(apply_url) if ats_provider == "lever" else None
        )
        if lever_target:
            result = await self._apply_via_lever(lever_target, profile, resume_path)
            return await self._finish_run_from_adapter_result(
                run,
                job,
                result,
                submitted=True,
            )

        return await self._apply_via_browser(
            run=run,
            job=job,
            profile=profile,
            resume_path=resume_path,
        )

    async def run_batch(self, user_id: uuid.UUID) -> list[AutoApplyRun]:
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
        for job, rule in matched_jobs[:10]:
            run = await self.apply_to_job(job, profile, rule=rule)
            runs.append(run)
            await asyncio.sleep(0)

        return runs

    async def _apply_via_lever(
        self,
        lever_target: tuple[str, str],
        profile: AutoApplyProfile,
        resume_path: str | None,
    ) -> LeverApplicationResult:
        company_slug, posting_id = lever_target
        adapter = LeverAPIAdapter()
        return await adapter.apply(
            company_slug=company_slug,
            posting_id=posting_id,
            profile=self._build_profile_payload(profile),
            resume_path=resume_path,
            cover_letter=profile.cover_letter_template,
        )

    async def _apply_via_browser(
        self,
        *,
        run: AutoApplyRun,
        job: Job,
        profile: AutoApplyProfile,
        resume_path: str | None,
    ) -> AutoApplyRun:
        from playwright.async_api import async_playwright

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
                )
                page = await context.new_page()

                await page.goto(job.source_url or "", wait_until="networkidle")

                detected_provider = await ATSDetector.detect_from_page(page)
                if detected_provider:
                    run.ats_provider = detected_provider

                apply_button = await page.query_selector(
                    'a:has-text("Apply"), button:has-text("Apply")'
                )
                if apply_button and run.ats_provider != "greenhouse":
                    await apply_button.click()
                    await page.wait_for_load_state("networkidle")

                if run.ats_provider == "greenhouse":
                    greenhouse_adapter = GreenhouseBrowserAdapter(
                        form_extractor=FormExtractor(),
                        field_mapper=FieldMapper(self.db, ats_provider="greenhouse"),
                    )
                    greenhouse_result = await greenhouse_adapter.apply(
                        page,
                        self._build_profile_payload(profile),
                        resume_path=resume_path,
                        cover_letter=profile.cover_letter_template,
                    )
                    return await self._finish_run_from_adapter_result(
                        run,
                        job,
                        greenhouse_result,
                        submitted=False,
                    )

                if run.ats_provider == "workday":
                    workday_adapter = WorkdayBrowserAdapter(page, profile)
                    workday_result = await workday_adapter.apply(resume_path=resume_path)
                    run.fields_filled = workday_result.fields_filled
                    run.fields_missed = workday_result.fields_missed
                    run.review_items = self._merge_review_items(
                        workday_result.review_items,
                        run.fields_missed,
                        workday_result.needs_confirmation,
                    )
                    run.screenshots = self._persist_screenshots(
                        run.id,
                        screenshots=workday_result.screenshots,
                    )
                    run.status = (
                        self.REVIEW_COMPLETE_STATUS if workday_result.success else "failed"
                    )
                    run.error_message = workday_result.error
                    run.completed_at = datetime.now(UTC)
                    await self.db.commit()
                    return run

                filler = GenericATSFiller(page, profile, self.llm)
                filler_result = await filler.fill_form()
                run.fields_filled = filler_result["filled"]
                run.fields_missed = filler_result["missed"]
                run.review_items = self._merge_review_items(
                    filler_result.get("review_items", []),
                    run.fields_missed,
                    True,
                )
                screenshot = await page.screenshot(full_page=True)
                run.screenshots = self._persist_screenshots(run.id, screenshots=[screenshot])
                run.status = self.REVIEW_COMPLETE_STATUS
                run.completed_at = datetime.now(UTC)
                await self.db.commit()
                return run
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(UTC)
            logger.error("auto_apply_failed", job_id=job.id, error=str(exc))
            await self.db.commit()
            return run

    async def _finish_run_from_adapter_result(
        self,
        run: AutoApplyRun,
        job: Job,
        result: Any,
        *,
        submitted: bool,
    ) -> AutoApplyRun:
        run.fields_filled = getattr(result, "fields_filled", {}) or {}
        run.fields_missed = getattr(result, "fields_missed", []) or []
        run.review_items = self._merge_review_items(
            getattr(result, "review_items", []),
            run.fields_missed,
            getattr(result, "needs_confirmation", False),
        )
        run.error_message = getattr(result, "error", None)

        screenshots: list[bytes] = []
        if getattr(result, "screenshot", None):
            screenshots.append(result.screenshot)
        if getattr(result, "screenshots", None):
            screenshots.extend(result.screenshots)
        run.screenshots = self._persist_screenshots(run.id, screenshots=screenshots)

        run.status = (
            self.SUBMITTED_STATUS
            if submitted and getattr(result, "success", False)
            else self.REVIEW_COMPLETE_STATUS if getattr(result, "success", False) else "failed"
        )
        run.completed_at = datetime.now(UTC)

        if submitted and getattr(result, "success", False):
            await self._record_application(job, run.user_id, run.ats_provider)

        await self.db.commit()
        return run

    @staticmethod
    def _merge_review_items(
        review_items: list[str] | None,
        fields_missed: list[str] | None,
        needs_confirmation: bool,
    ) -> list[str]:
        merged: list[str] = []

        if needs_confirmation:
            merged.append("Manual confirmation required before final submission.")

        for item in review_items or []:
            if item not in merged:
                merged.append(item)

        for field in fields_missed or []:
            message = f"Provide value for '{field}'"
            if message not in merged:
                merged.append(message)

        return merged

    async def _record_application(
        self,
        job: Job,
        user_id: uuid.UUID | None,
        ats_provider: str | None,
    ) -> None:
        if user_id is None:
            return

        existing = await self.db.scalar(
            select(Application).where(
                Application.user_id == user_id,
                Application.job_id == job.id,
            )
        )
        if existing is not None:
            return

        application = Application(
            user_id=user_id,
            job_id=job.id,
            company_name=job.company_name,
            position_title=job.title,
            status="applied",
            source=f"auto_apply:{ats_provider or 'generic'}",
            applied_at=datetime.now(UTC),
        )
        self.db.add(application)
        await self.db.flush()

    async def _build_safety_layer(
        self,
        user_id: uuid.UUID | None,
        *,
        allow_first_time_for: set[str] | None = None,
    ) -> SafetyLayer:
        known = await self._get_known_ats_types(user_id)
        if allow_first_time_for:
            known.update(allow_first_time_for)
        return SafetyLayer(
            daily_limit=self.settings.auto_apply_max_daily,
            known_ats_types=known,
        )

    async def _get_known_ats_types(self, user_id: uuid.UUID | None) -> set[str]:
        if user_id is None:
            return set()

        rows = await self.db.scalars(
            select(AutoApplyRun.ats_provider).where(
                AutoApplyRun.user_id == user_id,
                AutoApplyRun.ats_provider.is_not(None),
                AutoApplyRun.status.in_(
                    [self.SUBMITTED_STATUS, self.REVIEW_COMPLETE_STATUS]
                ),
            )
        )
        return {provider for provider in rows.all() if provider}

    def _build_profile_payload(self, profile: AutoApplyProfile) -> dict[str, Any]:
        full_name = profile.full_name or ""
        parts = full_name.split()
        first_name = parts[0] if parts else ""
        last_name = parts[-1] if len(parts) > 1 else ""

        return {
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": profile.email or "",
            "phone": profile.phone or "",
            "linkedin_url": profile.linkedin_url or "",
            "github_url": profile.github_url or "",
            "portfolio_url": profile.portfolio_url or "",
            "website_url": profile.portfolio_url or "",
            "cover_letter": profile.cover_letter_template or "",
        }

    def _persist_screenshots(self, run_id: uuid.UUID, screenshots: list[bytes]) -> list[str]:
        paths: list[str] = []
        for index, screenshot in enumerate(screenshots):
            path = self._build_screenshot_path(run_id, index)
            with open(path, "wb") as handle:
                handle.write(screenshot)
            paths.append(path)
        return paths

    async def _get_candidate_jobs(self, user_id: uuid.UUID) -> list[Job]:
        from app.jobs.models import Job

        applied_job_ids = (
            await self.db.scalars(select(Application.job_id).where(Application.user_id == user_id))
        ).all()
        prior_run_job_ids = (
            await self.db.scalars(
                select(AutoApplyRun.job_id).where(
                    AutoApplyRun.user_id == user_id,
                    AutoApplyRun.job_id.is_not(None),
                    AutoApplyRun.status.in_(
                        [self.SUBMITTED_STATUS, self.REVIEW_COMPLETE_STATUS, "running"]
                    ),
                )
            )
        ).all()

        excluded_ids = {job_id for job_id in [*applied_job_ids, *prior_run_job_ids] if job_id}

        stmt = select(Job).where(
            Job.user_id == user_id,
            Job.is_active == True,  # noqa: E712
            Job.status == "new",
        )
        if excluded_ids:
            stmt = stmt.where(~Job.id.in_(excluded_ids))

        stmt = stmt.order_by(Job.match_score.desc().nulls_last()).limit(50)
        return list((await self.db.scalars(stmt)).all())
