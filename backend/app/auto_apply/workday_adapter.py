"""Workday Shadow DOM adapter for multi-page application flows.

Workday uses shadow DOM extensively and multi-step wizards (5-15 pages).
This adapter delegates selectors, detection, and execution helpers to the
internal ``app.auto_apply.workday`` package while keeping the public API
stable for existing callers and tests.

Safety: never auto-submits. Returns needs_confirmation=True on the final
review page so the user can inspect before clicking Submit.
"""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING, Any

from app.auto_apply.workday.constants import (
    PROFILE_TO_SELECTOR,
    STEP_INDICATORS,
    WORKDAY_SELECTORS,
)
from app.auto_apply.workday.detection import WorkdayStepDetector
from app.auto_apply.workday.execution import WorkdayExecutionHelper
from app.auto_apply.workday.types import ApplicationResult, StepResult, WizardStep

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.auto_apply.models import AutoApplyProfile

__all__ = [
    "ApplicationResult",
    "PROFILE_TO_SELECTOR",
    "STEP_INDICATORS",
    "StepResult",
    "WORKDAY_SELECTORS",
    "WizardStep",
    "WorkdayBrowserAdapter",
]


class WorkdayBrowserAdapter:
    """Workday shadow DOM adapter with wizard state management."""

    MAX_PAGES: int = 15
    ACTION_DELAY: tuple[float, float] = (3.0, 5.0)
    SESSION_TIMEOUT_SEC: int = 900  # 15 minutes

    def __init__(
        self,
        page: Page,
        profile: AutoApplyProfile,
        *,
        action_delay: tuple[float, float] | None = None,
    ) -> None:
        self.page = page
        self.profile = profile
        self.action_delay = action_delay or self.ACTION_DELAY
        self._current_step: int = 0
        self._filled_total: dict[str, str] = {}
        self._missed_total: list[str] = []
        self._detector = WorkdayStepDetector(self.page)
        self._executor = WorkdayExecutionHelper(self.page, self.profile, self.action_delay)

    async def apply(self, resume_path: str | None = None) -> ApplicationResult:
        """Walk the Workday wizard, fill each page, stop before submit."""
        steps: list[StepResult] = []
        screenshots: list[bytes] = []

        for page_num in range(self.MAX_PAGES):
            await self._human_delay()

            wizard_step = await self._detect_current_step()

            if wizard_step == WizardStep.REVIEW:
                screenshot = await self._take_screenshot()
                screenshots.append(screenshot)
                steps.append(StepResult(step=wizard_step, screenshot=screenshot))
                return ApplicationResult(
                    success=True,
                    needs_confirmation=True,
                    page_reached=page_num + 1,
                    steps=steps,
                    screenshots=screenshots,
                    review_items=self._build_review_items(),
                )

            step_result = await self._fill_current_page(wizard_step, resume_path)
            steps.append(step_result)

            screenshot = await self._take_screenshot()
            screenshots.append(screenshot)
            step_result.screenshot = screenshot

            self._current_step = page_num + 1

            can_continue = await self._click_next()
            if not can_continue:
                break

        return ApplicationResult(
            success=True,
            needs_confirmation=True,
            page_reached=self._current_step,
            steps=steps,
            screenshots=screenshots,
            review_items=self._build_review_items(),
        )

    async def _query_shadow(self, selector: str) -> list[Any]:
        """Query all matching elements, piercing shadow roots."""
        from app.auto_apply.workday.shadow import query_shadow

        return await query_shadow(self.page, selector)

    async def _query_shadow_one(self, selector: str) -> Any | None:
        """Query a single element, piercing shadow roots."""
        from app.auto_apply.workday.shadow import query_shadow_one

        return await query_shadow_one(self.page, selector)

    async def _get_automation_ids(self) -> list[str]:
        """Collect all data-automation-id values on the current page."""
        from app.auto_apply.workday.shadow import get_automation_ids

        return await get_automation_ids(self.page)

    async def _detect_current_step(self) -> WizardStep:
        """Determine which wizard step we are on by checking automation IDs."""
        return await self._detector.detect_current_step()

    async def _fill_current_page(
        self, step: WizardStep, resume_path: str | None
    ) -> StepResult:
        """Fill all recognized fields on the current wizard page."""
        result = await self._executor.fill_current_page(
            step,
            resume_path,
            inter_field_delay=self._inter_field_delay,
        )
        self._filled_total.update(result.fields_filled)
        self._missed_total.extend(result.fields_missed)
        return result

    async def _fill_shadow_field(self, selector: str, value: str) -> bool:
        """Fill a single field, piercing shadow DOM if needed."""
        return await self._executor.fill_shadow_field(selector, value)

    async def _upload_resume(self, resume_path: str) -> bool:
        """Upload resume via Workday's file upload widget."""
        return await self._executor.upload_resume(resume_path)

    async def _click_next(self) -> bool:
        """Click the Next / Continue button. Returns False if not found."""
        return await self._executor.click_next()

    def _build_profile_map(self) -> dict[str, str | None]:
        """Build a flat dict from the AutoApplyProfile for field mapping."""
        return self._executor.build_profile_map()

    async def _human_delay(self) -> None:
        """Random delay between actions to avoid bot detection."""
        delay = random.uniform(*self.action_delay)
        await asyncio.sleep(delay)

    async def _inter_field_delay(self) -> None:
        """Shorter delay between filling individual fields."""
        await asyncio.sleep(random.uniform(0.5, 1.5))

    async def _take_screenshot(self) -> bytes:
        """Take a full-page screenshot for review."""
        return await self._executor.take_screenshot()

    def _build_review_items(self) -> list[str]:
        items = ["Manual confirmation required on the Workday review step."]
        for field in self._missed_total:
            message = f"Provide value for '{field}'"
            if message not in items:
                items.append(message)
        return items
