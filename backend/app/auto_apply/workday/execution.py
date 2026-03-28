from __future__ import annotations

import asyncio
import random
from typing import Any, Awaitable, Callable

import structlog

from .constants import PROFILE_TO_SELECTOR, WORKDAY_SELECTORS
from .shadow import query_shadow_one
from .types import StepResult, WizardStep

logger = structlog.get_logger()
DelayCallback = Callable[[], Awaitable[None]]


class WorkdayExecutionHelper:
    def __init__(self, page: Any, profile: Any, action_delay: tuple[float, float]) -> None:
        self.page = page
        self.profile = profile
        self.action_delay = action_delay

    async def fill_current_page(
        self,
        step: WizardStep,
        resume_path: str | None,
        *,
        inter_field_delay: DelayCallback | None = None,
    ) -> StepResult:
        result = StepResult(step=step)
        profile_values = self.build_profile_map()

        for profile_key, selector_key in PROFILE_TO_SELECTOR.items():
            selector = WORKDAY_SELECTORS.get(selector_key)
            if not selector:
                continue

            value = profile_values.get(profile_key)
            if not value:
                result.fields_missed.append(profile_key)
                continue

            filled = await self.fill_shadow_field(selector, value)
            if filled:
                result.fields_filled[profile_key] = value
                if inter_field_delay:
                    await inter_field_delay()
            else:
                result.fields_missed.append(profile_key)

        if resume_path:
            uploaded = await self.upload_resume(resume_path)
            if uploaded:
                result.fields_filled["resume_upload"] = resume_path

        logger.info(
            "workday.page_filled",
            step=step.value,
            filled=len(result.fields_filled),
            missed=len(result.fields_missed),
        )

        return result

    async def fill_shadow_field(self, selector: str, value: str) -> bool:
        try:
            locator = self.page.locator(selector)
            if await locator.count() > 0:
                tag = await locator.first.evaluate("el => el.tagName.toLowerCase()")
                if tag == "select":
                    await locator.first.select_option(label=value)
                elif tag in ("input", "textarea"):
                    await locator.first.fill(value)
                else:
                    await locator.first.fill(value)
                return True
        except Exception as exc:
            logger.debug(
                "workday.locator_fill_failed",
                selector=selector,
                error=str(exc),
            )

        try:
            element = await query_shadow_one(self.page, selector)
            if element:
                await self.page.evaluate(
                    """
                    (args) => {
                        const [el, val] = args;
                        if (!el) return;
                        el.focus();
                        el.value = val;
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    """,
                    [element, value],
                )
                return True
        except Exception as exc:
            logger.debug("workday.shadow_fill_failed", selector=selector, error=str(exc))

        return False

    async def upload_resume(self, resume_path: str) -> bool:
        selector = WORKDAY_SELECTORS["resume_upload"]

        try:
            locator = self.page.locator(selector)
            if await locator.count() > 0:
                await locator.first.set_input_files(resume_path)
                logger.info("workday.resume_uploaded", method="set_input_files")
                return True
        except Exception as exc:
            logger.debug(
                "workday.resume_input_upload_failed",
                selector=selector,
                error=str(exc),
            )

        try:
            upload_btn = self.page.locator(
                'button:has-text("Select Files"), '
                'button:has-text("Upload"), '
                '[data-automation-id="file-upload-drop-zone"]'
            )
            if await upload_btn.count() > 0:
                async with self.page.expect_file_chooser() as fc_info:
                    await upload_btn.first.click()
                fc = await fc_info.value
                await fc.set_files(resume_path)
                logger.info("workday.resume_uploaded", method="file_chooser")
                return True
        except Exception as exc:
            logger.warning("workday.resume_upload_failed", error=str(exc))

        return False

    async def click_next(self) -> bool:
        selector = WORKDAY_SELECTORS["next_button"]

        try:
            locator = self.page.locator(selector)
            if await locator.count() == 0:
                locator = self.page.locator(
                    'button:has-text("Next"), '
                    'button:has-text("Continue"), '
                    'button:has-text("Save and Continue")'
                )
                if await locator.count() == 0:
                    return False

            btn_text = await locator.first.inner_text()
            if "submit" in btn_text.lower():
                logger.info("workday.submit_detected_stopping")
                return False

            await locator.first.click()
            await self.page.wait_for_load_state("networkidle")
            return True
        except Exception as exc:
            logger.warning("workday.next_click_failed", error=str(exc))
            return False

    def build_profile_map(self) -> dict[str, str | None]:
        full_name = self.profile.full_name or ""
        parts = full_name.split()
        first_name = parts[0] if parts else None
        last_name = parts[-1] if len(parts) > 1 else None

        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": self.profile.email,
            "phone": self.profile.phone,
            "linkedin_url": self.profile.linkedin_url,
        }

    async def take_screenshot(self) -> bytes:
        return await self.page.screenshot(full_page=True)

    async def human_delay(self) -> None:
        delay = random.uniform(*self.action_delay)
        await asyncio.sleep(delay)

    async def inter_field_delay(self) -> None:
        await asyncio.sleep(random.uniform(0.5, 1.5))
