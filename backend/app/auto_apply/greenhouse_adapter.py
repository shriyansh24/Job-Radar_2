"""Greenhouse browser adapter for job applications.

Greenhouse has predictable DOM with semantic IDs (#first_name, #last_name, #email),
making browser-based form filling reliable. No public submit API exists.
"""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import structlog

from app.auto_apply.lever_adapter import ApplicationResult

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

logger = structlog.get_logger()


@runtime_checkable
class FormExtractor(Protocol):
    """Protocol for C1 FormExtractor (built in parallel)."""

    async def extract_fields(self, page: Any) -> list[dict[str, Any]]: ...


@runtime_checkable
class FieldMapper(Protocol):
    """Protocol for C2 FieldMapper (built in parallel)."""

    async def map_fields(
        self, fields: list[dict[str, Any]], profile: dict[str, Any]
    ) -> list[dict[str, Any]]: ...


class GreenhouseBrowserAdapter:
    """Fill Greenhouse application forms via browser automation.

    Greenhouse uses predictable selectors, making this adapter
    more reliable than generic browser filling.
    """

    # Standard Greenhouse field selectors -> profile key mapping
    FIELD_MAP: dict[str, str] = {
        "#first_name": "first_name",
        "#last_name": "last_name",
        "#email": "email",
        "#phone": "phone",
        "#job_application_location": "city",
    }

    # Selectors for resume upload
    RESUME_SELECTORS: list[str] = [
        'input[type="file"][id*="resume"]',
        'input[type="file"]#resume',
        'input[type="file"]',
    ]

    # Selectors for cover letter textarea
    COVER_LETTER_SELECTORS: list[str] = [
        "#cover_letter",
        'textarea[id*="cover_letter"]',
        "#job_application_answers_attributes_0_text_value",
    ]

    def __init__(
        self,
        form_extractor: FormExtractor | None = None,
        field_mapper: FieldMapper | None = None,
        human_typing: bool = True,
        min_type_delay: int = 40,
        max_type_delay: int = 120,
    ) -> None:
        self.form_extractor = form_extractor
        self.field_mapper = field_mapper
        self.human_typing = human_typing
        self.min_type_delay = min_type_delay
        self.max_type_delay = max_type_delay

    async def apply(
        self,
        page: Page,
        profile: dict[str, Any],
        resume_path: str | None = None,
        cover_letter: str | None = None,
    ) -> ApplicationResult:
        """Fill a Greenhouse application form.

        Does NOT auto-submit. Returns a result with needs_confirmation=True
        so the user can review before submission.

        Args:
            page: Playwright page navigated to the Greenhouse application.
            profile: Applicant profile dict.
            resume_path: Local path to resume file.
            cover_letter: Optional cover letter text.

        Returns:
            ApplicationResult with filled fields and screenshot.
        """
        filled: dict[str, str] = {}
        missed: list[str] = []

        # 1. Fill standard fields via known selectors
        for selector, profile_key in self.FIELD_MAP.items():
            value = profile.get(profile_key)
            if not value:
                missed.append(profile_key)
                continue

            locator = page.locator(selector)
            if await locator.count() > 0:
                await locator.first.fill("")
                await self._human_type(locator.first, str(value))
                filled[profile_key] = str(value)
                await asyncio.sleep(random.uniform(0.2, 0.5))
            else:
                missed.append(profile_key)

        # 2. Upload resume
        if resume_path:
            uploaded = await self._upload_resume(page, resume_path)
            if uploaded:
                filled["resume"] = resume_path
            else:
                missed.append("resume")

        # 3. Fill cover letter
        if cover_letter:
            cl_filled = await self._fill_cover_letter(page, cover_letter)
            if cl_filled:
                filled["cover_letter"] = cover_letter[:50] + "..."
            else:
                missed.append("cover_letter")

        # 4. Handle custom questions via C1+C2 if available
        if self.form_extractor and self.field_mapper:
            custom_filled, custom_missed = await self._handle_custom_questions(
                page, profile
            )
            filled.update(custom_filled)
            missed.extend(custom_missed)

        # 5. Screenshot before submit (never auto-submit)
        screenshot = await page.screenshot(full_page=True)

        logger.info(
            "greenhouse.apply.filled",
            filled_count=len(filled),
            missed_count=len(missed),
        )

        return ApplicationResult(
            success=True,
            ats="greenhouse",
            method="browser",
            screenshot=screenshot,
            needs_confirmation=True,
            fields_filled=filled,
            fields_missed=missed,
        )

    async def _upload_resume(self, page: Page, resume_path: str) -> bool:
        """Try to upload a resume using known Greenhouse selectors."""
        for selector in self.RESUME_SELECTORS:
            locator = page.locator(selector)
            if await locator.count() > 0:
                await locator.first.set_input_files(resume_path)
                await asyncio.sleep(1.0)
                logger.debug("greenhouse.resume_uploaded", selector=selector)
                return True
        logger.warning("greenhouse.resume_upload_failed", selectors=self.RESUME_SELECTORS)
        return False

    async def _fill_cover_letter(self, page: Page, cover_letter: str) -> bool:
        """Fill the cover letter textarea if present."""
        for selector in self.COVER_LETTER_SELECTORS:
            locator = page.locator(selector)
            if await locator.count() > 0:
                await locator.first.fill("")
                await locator.first.fill(cover_letter)
                return True
        return False

    async def _handle_custom_questions(
        self, page: Page, profile: dict[str, Any]
    ) -> tuple[dict[str, str], list[str]]:
        """Delegate unknown fields to FormExtractor + FieldMapper."""
        filled: dict[str, str] = {}
        missed: list[str] = []

        assert self.form_extractor is not None  # noqa: S101
        assert self.field_mapper is not None  # noqa: S101

        try:
            fields = await self.form_extractor.extract_fields(page)
            mapped = await self.field_mapper.map_fields(fields, profile)

            for item in mapped:
                selector = item.get("selector", "")
                value = item.get("value")
                label = item.get("label", selector)

                if not value:
                    missed.append(label)
                    continue

                locator = page.locator(selector)
                if await locator.count() > 0:
                    await locator.first.fill(str(value))
                    filled[label] = str(value)
                else:
                    missed.append(label)

        except Exception:
            logger.warning("greenhouse.custom_questions_failed", exc_info=True)

        return filled, missed

    async def _human_type(
        self,
        locator: Locator,
        text: str,
    ) -> None:
        """Type with human-like delays to avoid bot detection."""
        if not self.human_typing:
            await locator.fill(text)
            return

        for char in text:
            delay = random.randint(self.min_type_delay, self.max_type_delay)
            await locator.type(char, delay=delay)
