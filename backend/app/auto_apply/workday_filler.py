from __future__ import annotations

from typing import Any

from app.auto_apply.ats_filler import GenericATSFiller


class WorkdayFiller(GenericATSFiller):
    """Workday-specific form filling logic."""

    async def fill_form(self) -> dict[str, Any]:
        """Workday has multi-page forms — handle navigation."""
        results: dict[str, Any] = {"filled": {}, "missed": []}

        # Workday typically has: My Information -> My Experience -> Application Questions -> Review
        pages_filled = 0
        max_pages = 5

        while pages_filled < max_pages:
            page_result = await super().fill_form()
            results["filled"].update(page_result["filled"])
            results["missed"].extend(page_result["missed"])

            # Try to click Next/Continue
            next_btn = await self.page.query_selector(
                'button:has-text("Next"), '
                'button:has-text("Continue"), '
                'button:has-text("Save and Continue")'
            )
            if next_btn:
                await next_btn.click()
                await self.page.wait_for_load_state("networkidle")
                pages_filled += 1
            else:
                break

        return results

    async def upload_resume(self, resume_path: str) -> None:
        """Upload resume in Workday's specific upload flow."""
        upload_btn = await self.page.query_selector(
            'button:has-text("Select Files"), input[type="file"]'
        )
        if upload_btn:
            tag: str = await upload_btn.evaluate("el => el.tagName.toLowerCase()")
            if tag == "input":
                await upload_btn.set_input_files(resume_path)
            else:
                async with self.page.expect_file_chooser() as fc_info:
                    await upload_btn.click()
                fc = await fc_info.value
                await fc.set_files(resume_path)
