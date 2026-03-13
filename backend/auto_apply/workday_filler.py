"""Workday multi-page form controller.

Workday uses stable `data-automation-id` attributes for all form elements,
making it more predictable to automate than generic ATS platforms.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.auto_apply.profile import ApplicationProfile

# ---------------------------------------------------------------------------
# Workday page flow (in order)
# ---------------------------------------------------------------------------

WORKDAY_PAGES: list[str] = [
    "My Information",
    "My Experience",
    "Application Questions",
    "Voluntary Disclosures",
    "Review and Submit",
]

# ---------------------------------------------------------------------------
# Stable data-automation-id selectors for common Workday fields
# ---------------------------------------------------------------------------

WORKDAY_SELECTORS: dict[str, str] = {
    # My Information page
    "legal_name_first":     '[data-automation-id="legalNameSection_firstName"]',
    "legal_name_last":      '[data-automation-id="legalNameSection_lastName"]',
    "email":                '[data-automation-id="email"]',
    "phone":                '[data-automation-id="phone"]',
    "address_line1":        '[data-automation-id="addressSection_addressLine1"]',
    "city":                 '[data-automation-id="addressSection_city"]',
    "state":                '[data-automation-id="addressSection_stateProvince"]',
    "postal_code":          '[data-automation-id="addressSection_postalCode"]',
    "country":              '[data-automation-id="addressSection_countryRegion"]',
    # My Experience page
    "resume_upload":        '[data-automation-id="file-upload-input-ref"]',
    "cover_letter_upload":  '[data-automation-id="cover-letter-input-ref"]',
    "linkedin_url":         '[data-automation-id="linkedinField"]',
    "website_url":          '[data-automation-id="websiteField"]',
    # Application Questions
    "how_did_you_hear":     '[data-automation-id="howDidYouHearAboutUs"]',
    "work_auth":            '[data-automation-id="workAuth_legallyAuthorized"]',
    "sponsorship":          '[data-automation-id="workAuth_requireSponsorship"]',
    # Navigation
    "next_button":          '[data-automation-id="bottom-navigation-next-button"]',
    "save_button":          '[data-automation-id="bottom-navigation-save-button"]',
    "submit_button":        '[data-automation-id="bottom-navigation-next-button"]',
}


# ---------------------------------------------------------------------------
# WorkdayResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class WorkdayResult:
    """Result of a Workday application attempt."""

    pages_completed: list[str]
    fields_filled: dict[str, Any]
    fields_skipped: list[str]
    custom_questions_answered: list[str]
    screenshots: list[str]
    needs_review: list[str]
    browser_session_id: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# WorkdayFiller
# ---------------------------------------------------------------------------


class WorkdayFiller:
    """Fills multi-page Workday job applications using Playwright.

    Navigates through the standard Workday page flow:
    My Information → My Experience → Application Questions →
    Voluntary Disclosures → Review and Submit.

    Pass `submit=False` (the default) to fill forms without submitting.
    """

    def __init__(self, profile: ApplicationProfile) -> None:
        self.profile = profile

    async def fill_application(
        self,
        page: Any,
        auto_advance: bool = True,
        submit: bool = False,
    ) -> WorkdayResult:
        """Fill the entire Workday application flow.

        Args:
            page: Playwright page object (already navigated to the apply URL).
            auto_advance: Whether to click "Next" after each page.
            submit: Whether to click the final "Submit" button.

        Returns:
            WorkdayResult with detailed fill report.
        """
        pages_completed: list[str] = []
        all_filled: dict[str, Any] = {}
        all_skipped: list[str] = []
        needs_review: list[str] = []
        screenshots: list[str] = []

        page_handlers = [
            ("My Information", self._fill_my_information),
            ("My Experience", self._fill_my_experience),
            ("Application Questions", self._fill_application_questions),
            ("Voluntary Disclosures", self._fill_voluntary_disclosures),
        ]

        for page_name, handler in page_handlers:
            try:
                result = await handler(page)
                all_filled.update(result.get("filled", {}))
                all_skipped.extend(result.get("skipped", []))
                needs_review.extend(result.get("needs_review", []))
                pages_completed.append(page_name)

                if auto_advance and not submit:
                    # Click "Next" to advance (no-op in tests with mocked page)
                    next_btn = await page.query_selector(WORKDAY_SELECTORS["next_button"])
                    if next_btn:
                        await next_btn.click()
            except Exception as e:
                needs_review.append(f"{page_name}: {e}")

        return WorkdayResult(
            pages_completed=pages_completed,
            fields_filled=all_filled,
            fields_skipped=all_skipped,
            custom_questions_answered=[],
            screenshots=screenshots,
            needs_review=needs_review,
            browser_session_id="",
        )

    async def _fill_my_information(self, page: Any) -> dict:
        """Fill the 'My Information' page (name, email, phone, address)."""
        filled: dict[str, Any] = {}
        skipped: list[str] = []
        needs_review: list[str] = []

        # Split name into first/last
        if self.profile.name:
            parts = self.profile.name.strip().split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

            for sel_key, value in [
                ("legal_name_first", first_name),
                ("legal_name_last", last_name),
            ]:
                el = await page.query_selector(WORKDAY_SELECTORS[sel_key])
                if el:
                    try:
                        await el.fill(value)
                        filled[sel_key] = value
                    except Exception:
                        skipped.append(sel_key)
                else:
                    skipped.append(sel_key)

        # Email
        if self.profile.email:
            el = await page.query_selector(WORKDAY_SELECTORS["email"])
            if el:
                try:
                    await el.fill(self.profile.email)
                    filled["email"] = self.profile.email
                except Exception:
                    skipped.append("email")
            else:
                skipped.append("email")

        # Phone
        if self.profile.phone:
            el = await page.query_selector(WORKDAY_SELECTORS["phone"])
            if el:
                try:
                    await el.fill(self.profile.phone)
                    filled["phone"] = self.profile.phone
                except Exception:
                    skipped.append("phone")
            else:
                skipped.append("phone")

        # Location — mark for review (state dropdowns are tricky)
        if self.profile.location:
            needs_review.append("location — verify city/state fields manually")

        return {"filled": filled, "skipped": skipped, "needs_review": needs_review}

    async def _fill_my_experience(self, page: Any) -> dict:
        """Fill the 'My Experience' page (resume upload, LinkedIn, website)."""
        filled: dict[str, Any] = {}
        skipped: list[str] = []

        if self.profile.linkedin:
            el = await page.query_selector(WORKDAY_SELECTORS["linkedin_url"])
            if el:
                try:
                    await el.fill(self.profile.linkedin)
                    filled["linkedin_url"] = self.profile.linkedin
                except Exception:
                    skipped.append("linkedin_url")
            else:
                skipped.append("linkedin_url")

        if self.profile.portfolio:
            el = await page.query_selector(WORKDAY_SELECTORS["website_url"])
            if el:
                try:
                    await el.fill(self.profile.portfolio)
                    filled["website_url"] = self.profile.portfolio
                except Exception:
                    skipped.append("website_url")
            else:
                skipped.append("website_url")

        return {"filled": filled, "skipped": skipped, "needs_review": []}

    async def _fill_application_questions(self, page: Any) -> dict:
        """Fill the 'Application Questions' page (work auth, sponsorship, etc.)."""
        filled: dict[str, Any] = {}
        skipped: list[str] = []
        needs_review: list[str] = []

        # Work authorization — attempt to click the appropriate radio
        if self.profile.work_authorization:
            el = await page.query_selector(WORKDAY_SELECTORS["work_auth"])
            if el:
                try:
                    await el.click()
                    filled["work_auth"] = self.profile.work_authorization
                except Exception:
                    needs_review.append("work_authorization")
            else:
                needs_review.append("work_authorization")

        return {"filled": filled, "skipped": skipped, "needs_review": needs_review}

    async def _fill_voluntary_disclosures(self, page: Any) -> dict:
        """Fill the 'Voluntary Disclosures' page (EEO, gender, veteran, disability)."""
        # These fields are sensitive; mark for human review rather than auto-filling
        needs_review = ["voluntary_disclosure_fields — please complete manually"]
        return {"filled": {}, "skipped": [], "needs_review": needs_review}
