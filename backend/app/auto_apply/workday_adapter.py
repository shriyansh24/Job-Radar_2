"""Workday Shadow DOM adapter for multi-page application flows.

Workday uses shadow DOM extensively and multi-step wizards (5-15 pages).
This adapter pierces shadow roots via Playwright evaluate(), navigates
between wizard steps, and maps user profile fields to Workday's
data-automation-id attributes.

Safety: never auto-submits. Returns needs_confirmation=True on the final
review page so the user can inspect before clicking Submit.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.auto_apply.models import AutoApplyProfile

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class WizardStep(str, Enum):
    PERSONAL_INFO = "personal_info"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    VOLUNTARY_DISCLOSURES = "voluntary_disclosures"
    REVIEW = "review"
    UNKNOWN = "unknown"


@dataclass
class StepResult:
    step: WizardStep
    fields_filled: dict[str, str] = field(default_factory=dict)
    fields_missed: list[str] = field(default_factory=list)
    screenshot: bytes | None = None


@dataclass
class ApplicationResult:
    success: bool
    ats: str = "workday"
    method: str = "browser"
    needs_confirmation: bool = True
    page_reached: int = 0
    steps: list[StepResult] = field(default_factory=list)
    screenshots: list[bytes] = field(default_factory=list)
    error: str | None = None

    @property
    def fields_filled(self) -> dict[str, str]:
        merged: dict[str, str] = {}
        for s in self.steps:
            merged.update(s.fields_filled)
        return merged

    @property
    def fields_missed(self) -> list[str]:
        missed: list[str] = []
        for s in self.steps:
            missed.extend(s.fields_missed)
        return missed


# ---------------------------------------------------------------------------
# Selector and mapping constants
# ---------------------------------------------------------------------------

WORKDAY_SELECTORS: dict[str, str] = {
    # Personal info
    "first_name": '[data-automation-id="legalNameSection_firstName"]',
    "last_name": '[data-automation-id="legalNameSection_lastName"]',
    "email": '[data-automation-id="email"]',
    "phone": '[data-automation-id="phone"]',
    "address_line1": '[data-automation-id="addressSection_addressLine1"]',
    "city": '[data-automation-id="addressSection_city"]',
    "state": '[data-automation-id="addressSection_countryRegion"]',
    "postal_code": '[data-automation-id="addressSection_postalCode"]',
    # Resume upload
    "resume_upload": '[data-automation-id="file-upload-input-ref"]',
    # Navigation
    "next_button": '[data-automation-id="bottom-navigation-next-button"]',
    "previous_button": '[data-automation-id="bottom-navigation-previous-button"]',
    # Experience
    "job_title": '[data-automation-id="jobTitle"]',
    "company_name": '[data-automation-id="company"]',
    "currently_work_here": '[data-automation-id="currentlyWorkHere"]',
    # Education
    "school_name": '[data-automation-id="school"]',
    "degree": '[data-automation-id="degree"]',
    # LinkedIn
    "linkedin": '[data-automation-id="linkedinQuestion"]',
    # Generic text input/textarea (fallback)
    "text_input": "input[type='text']:visible, textarea:visible",
}

# Maps profile field names to their Workday data-automation-id selectors
_PROFILE_TO_SELECTOR: dict[str, str] = {
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "phone": "phone",
    "linkedin_url": "linkedin",
}

# Step detection: data-automation-id patterns that indicate which wizard step we are on
_STEP_INDICATORS: dict[WizardStep, list[str]] = {
    WizardStep.PERSONAL_INFO: [
        "legalNameSection_firstName",
        "legalNameSection_lastName",
        "email",
        "phone",
    ],
    WizardStep.EXPERIENCE: [
        "jobTitle",
        "company",
        "currentlyWorkHere",
    ],
    WizardStep.EDUCATION: [
        "school",
        "degree",
    ],
    WizardStep.VOLUNTARY_DISCLOSURES: [
        "voluntaryDisclosures",
        "gender",
        "ethnicity",
        "veteranStatus",
        "disabilityStatus",
    ],
    WizardStep.REVIEW: [
        "review",
    ],
}


# ---------------------------------------------------------------------------
# JS helpers for shadow DOM piercing
# ---------------------------------------------------------------------------

_JS_QUERY_SHADOW = """
(selector) => {
    function queryShadowAll(root, sel) {
        let results = [...root.querySelectorAll(sel)];
        root.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
                results = results.concat(queryShadowAll(el.shadowRoot, sel));
            }
        });
        return results;
    }
    return queryShadowAll(document, selector);
}
"""

_JS_QUERY_SHADOW_ONE = """
(selector) => {
    function queryShadow(root, sel) {
        let found = root.querySelector(sel);
        if (found) return found;
        for (const el of root.querySelectorAll('*')) {
            if (el.shadowRoot) {
                found = queryShadow(el.shadowRoot, sel);
                if (found) return found;
            }
        }
        return null;
    }
    return queryShadow(document, selector);
}
"""

_JS_DETECT_AUTOMATION_IDS = """
() => {
    function collectIds(root) {
        let ids = [];
        root.querySelectorAll('[data-automation-id]').forEach(el => {
            ids.push(el.getAttribute('data-automation-id'));
        });
        root.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
                ids = ids.concat(collectIds(el.shadowRoot));
            }
        });
        return ids;
    }
    return collectIds(document);
}
"""


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class WorkdayBrowserAdapter:
    """Workday shadow DOM adapter with wizard state management.

    Pierces shadow roots via Playwright ``evaluate()``, navigates the
    multi-page wizard, and maps user profile fields to Workday's
    ``data-automation-id`` attributes.
    """

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def apply(self, resume_path: str | None = None) -> ApplicationResult:
        """Walk the Workday wizard, fill each page, stop before submit."""
        steps: list[StepResult] = []
        screenshots: list[bytes] = []

        for page_num in range(self.MAX_PAGES):
            await self._human_delay()

            # Detect which step we are on
            wizard_step = await self._detect_current_step()

            # If we detect the review page, stop and ask for confirmation
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
                )

            # Extract and fill fields on the current page
            step_result = await self._fill_current_page(wizard_step, resume_path)
            steps.append(step_result)

            screenshot = await self._take_screenshot()
            screenshots.append(screenshot)
            step_result.screenshot = screenshot

            self._current_step = page_num + 1

            # Try to navigate to next page
            can_continue = await self._click_next()
            if not can_continue:
                break

        return ApplicationResult(
            success=True,
            needs_confirmation=True,
            page_reached=self._current_step,
            steps=steps,
            screenshots=screenshots,
        )

    # ------------------------------------------------------------------
    # Shadow DOM helpers
    # ------------------------------------------------------------------

    async def _query_shadow(self, selector: str) -> list[Any]:
        """Query all matching elements, piercing shadow roots."""
        return await self.page.evaluate(_JS_QUERY_SHADOW, selector)

    async def _query_shadow_one(self, selector: str) -> Any | None:
        """Query a single element, piercing shadow roots."""
        return await self.page.evaluate(_JS_QUERY_SHADOW_ONE, selector)

    async def _get_automation_ids(self) -> list[str]:
        """Collect all data-automation-id values on the current page."""
        return await self.page.evaluate(_JS_DETECT_AUTOMATION_IDS)

    # ------------------------------------------------------------------
    # Step detection
    # ------------------------------------------------------------------

    async def _detect_current_step(self) -> WizardStep:
        """Determine which wizard step we are on by checking automation IDs."""
        try:
            page_ids = await self._get_automation_ids()
        except Exception:
            logger.warning("workday.step_detection_failed")
            return WizardStep.UNKNOWN

        page_ids_set = set(page_ids)

        # Check for "submit" on the next button which signals review page
        try:
            next_btn = await self._query_shadow_one(
                WORKDAY_SELECTORS["next_button"]
            )
            if next_btn:
                btn_text = await self.page.evaluate(
                    "(el) => el?.innerText || ''", next_btn
                )
                if btn_text and "submit" in btn_text.lower():
                    return WizardStep.REVIEW
        except Exception as exc:
            logger.debug("workday.review_step_probe_failed", error=str(exc))

        # Match against known step indicators
        best_step = WizardStep.UNKNOWN
        best_score = 0
        for step, indicators in _STEP_INDICATORS.items():
            score = sum(1 for ind in indicators if ind in page_ids_set)
            if score > best_score:
                best_score = score
                best_step = step

        return best_step

    # ------------------------------------------------------------------
    # Field filling
    # ------------------------------------------------------------------

    async def _fill_current_page(
        self, step: WizardStep, resume_path: str | None
    ) -> StepResult:
        """Fill all recognized fields on the current wizard page."""
        result = StepResult(step=step)

        # Build the profile value map
        profile_values = self._build_profile_map()

        # Fill each mapped field
        for profile_key, selector_key in _PROFILE_TO_SELECTOR.items():
            selector = WORKDAY_SELECTORS.get(selector_key)
            if not selector:
                continue

            value = profile_values.get(profile_key)
            if not value:
                result.fields_missed.append(profile_key)
                continue

            filled = await self._fill_shadow_field(selector, value)
            if filled:
                result.fields_filled[profile_key] = value
                await self._inter_field_delay()
            else:
                result.fields_missed.append(profile_key)

        # Handle resume upload on the first page if selector is present
        if resume_path:
            uploaded = await self._upload_resume(resume_path)
            if uploaded:
                result.fields_filled["resume_upload"] = resume_path

        self._filled_total.update(result.fields_filled)
        self._missed_total.extend(result.fields_missed)

        logger.info(
            "workday.page_filled",
            step=step.value,
            filled=len(result.fields_filled),
            missed=len(result.fields_missed),
        )

        return result

    async def _fill_shadow_field(self, selector: str, value: str) -> bool:
        """Fill a single field, piercing shadow DOM if needed.

        Tries Playwright locator first (handles light DOM and
        Playwright's built-in shadow piercing), then falls back to
        JS-based shadow DOM traversal.
        """
        # Attempt 1: Playwright locator (handles css >> shadow piercing)
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

        # Attempt 2: JS shadow DOM traversal
        try:
            element = await self._query_shadow_one(selector)
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

    async def _upload_resume(self, resume_path: str) -> bool:
        """Upload resume via Workday's file upload widget."""
        selector = WORKDAY_SELECTORS["resume_upload"]

        # Attempt 1: standard file input
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

        # Attempt 2: click the upload button and use file chooser
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

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    async def _click_next(self) -> bool:
        """Click the Next / Continue button. Returns False if not found
        or if the button text indicates Submit (safety stop)."""
        selector = WORKDAY_SELECTORS["next_button"]

        try:
            locator = self.page.locator(selector)
            if await locator.count() == 0:
                # Fallback selectors
                locator = self.page.locator(
                    'button:has-text("Next"), '
                    'button:has-text("Continue"), '
                    'button:has-text("Save and Continue")'
                )
                if await locator.count() == 0:
                    return False

            btn_text = await locator.first.inner_text()

            # SAFETY: never click submit
            if "submit" in btn_text.lower():
                logger.info("workday.submit_detected_stopping")
                return False

            await locator.first.click()
            await self.page.wait_for_load_state("networkidle")
            return True
        except Exception as exc:
            logger.warning("workday.next_click_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Profile mapping
    # ------------------------------------------------------------------

    def _build_profile_map(self) -> dict[str, str | None]:
        """Build a flat dict from the AutoApplyProfile for field mapping."""
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

    # ------------------------------------------------------------------
    # Timing / anti-detection
    # ------------------------------------------------------------------

    async def _human_delay(self) -> None:
        """Random delay between actions to avoid bot detection."""
        delay = random.uniform(*self.action_delay)
        await asyncio.sleep(delay)

    async def _inter_field_delay(self) -> None:
        """Shorter delay between filling individual fields."""
        await asyncio.sleep(random.uniform(0.5, 1.5))

    async def _take_screenshot(self) -> bytes:
        """Take a full-page screenshot for review."""
        return await self.page.screenshot(full_page=True)
