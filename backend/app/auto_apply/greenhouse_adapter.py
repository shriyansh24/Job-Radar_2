from __future__ import annotations

import asyncio
import random
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import structlog

from app.auto_apply.form_extractor import FormField
from app.auto_apply.lever_adapter import ApplicationResult

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

logger = structlog.get_logger()


@runtime_checkable
class ExtractorProtocol(Protocol):
    async def extract_fields(self, page: Any) -> list[FormField]: ...


@runtime_checkable
class FieldClassifierProtocol(Protocol):
    async def classify(self, field_label: str) -> str | None: ...


class GreenhouseBrowserAdapter:
    """Fill Greenhouse application forms via browser automation without auto-submitting."""

    FIELD_MAP: dict[str, str] = {
        "#first_name": "first_name",
        "#last_name": "last_name",
        "#email": "email",
        "#phone": "phone",
        "#job_application_location": "city",
    }

    RESUME_SELECTORS: list[str] = [
        'input[type="file"][id*="resume"]',
        'input[type="file"]#resume',
        'input[type="file"]',
    ]

    COVER_LETTER_SELECTORS: list[str] = [
        "#cover_letter",
        'textarea[id*="cover_letter"]',
        "#job_application_answers_attributes_0_text_value",
    ]

    def __init__(
        self,
        form_extractor: ExtractorProtocol | None = None,
        field_mapper: FieldClassifierProtocol | None = None,
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
        filled: dict[str, str] = {}
        missed: list[str] = []

        for selector, profile_key in self.FIELD_MAP.items():
            value = self._lookup_profile_value(profile, profile_key)
            if not value:
                missed.append(profile_key)
                continue

            locator = page.locator(selector)
            if await locator.count() == 0:
                missed.append(profile_key)
                continue

            await locator.first.fill("")
            await self._human_type(locator.first, value)
            filled[profile_key] = value
            await asyncio.sleep(random.uniform(0.2, 0.5))

        if resume_path:
            if await self._upload_resume(page, resume_path):
                filled["resume"] = resume_path
            else:
                missed.append("resume")

        if cover_letter:
            if await self._fill_cover_letter(page, cover_letter):
                filled["cover_letter"] = f"{cover_letter[:50]}..."
            else:
                missed.append("cover_letter")

        if self.form_extractor and self.field_mapper:
            custom_filled, custom_missed = await self._handle_custom_questions(page, profile)
            filled.update(custom_filled)
            missed.extend(custom_missed)

        screenshot = await page.screenshot(full_page=True)
        logger.info(
            "auto_apply_greenhouse_filled",
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
        for selector in self.RESUME_SELECTORS:
            locator = page.locator(selector)
            if await locator.count() > 0:
                await locator.first.set_input_files(resume_path)
                await asyncio.sleep(1.0)
                logger.debug("auto_apply_greenhouse_resume_uploaded", selector=selector)
                return True
        logger.warning("auto_apply_greenhouse_resume_upload_failed")
        return False

    async def _fill_cover_letter(self, page: Page, cover_letter: str) -> bool:
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
        filled: dict[str, str] = {}
        missed: list[str] = []

        assert self.form_extractor is not None  # noqa: S101
        assert self.field_mapper is not None  # noqa: S101

        try:
            fields = await self.form_extractor.extract_fields(page)
        except Exception as exc:
            logger.warning("auto_apply_greenhouse_custom_field_extraction_failed", error=str(exc))
            return filled, missed

        standard_selectors = set(self.FIELD_MAP) | set(self.RESUME_SELECTORS) | set(
            self.COVER_LETTER_SELECTORS
        )

        for field in fields:
            if field.locator_desc in standard_selectors or field.field_type == "file":
                continue

            try:
                semantic_key = await self.field_mapper.classify(field.label)
            except Exception as exc:
                logger.warning(
                    "auto_apply_greenhouse_field_classification_failed",
                    field_label=field.label,
                    error=str(exc),
                )
                continue

            if not semantic_key:
                continue

            value = self._lookup_profile_value(profile, semantic_key)
            if not value:
                missed.append(field.label)
                continue

            if await self._fill_dynamic_field(page, field, value):
                filled[field.label] = value
            else:
                missed.append(field.label)

        return filled, missed

    async def _fill_dynamic_field(self, page: Page, field: FormField, value: str) -> bool:
        locator = page.locator(field.locator_desc)
        if await locator.count() == 0:
            logger.debug("auto_apply_greenhouse_dynamic_field_missing", field=asdict(field))
            return False

        if field.field_type == "select":
            await locator.first.select_option(label=value)
            return True

        if field.field_type == "checkbox":
            normalized = value.strip().lower()
            if normalized in {"true", "yes", "1", "on"}:
                await locator.first.check()
                return True
            return False

        await locator.first.fill("")
        await self._human_type(locator.first, value)
        return True

    def _lookup_profile_value(self, profile: dict[str, Any], semantic_key: str) -> str | None:
        alias_map: dict[str, tuple[str, ...]] = {
            "city": ("city", "location", "location_city"),
            "location": ("location", "city", "location_city"),
            "portfolio": ("portfolio_url", "website_url", "portfolio"),
            "github": ("github_url", "github"),
            "linkedin": ("linkedin_url", "linkedin"),
        }
        if semantic_key in profile and profile[semantic_key]:
            return str(profile[semantic_key])
        for alias in alias_map.get(semantic_key, ()):
            value = profile.get(alias)
            if value:
                return str(value)
        return None

    async def _human_type(self, locator: Locator, text: str) -> None:
        if not self.human_typing:
            await locator.fill(text)
            return

        for char in text:
            delay = random.randint(self.min_type_delay, self.max_type_delay)
            await locator.type(char, delay=delay)
