from __future__ import annotations

from typing import Any

import structlog

from .constants import STEP_INDICATORS, WORKDAY_SELECTORS
from .shadow import get_automation_ids, query_shadow_one
from .types import WizardStep

logger = structlog.get_logger()


class WorkdayStepDetector:
    def __init__(self, page: Any) -> None:
        self.page = page

    async def detect_current_step(self) -> WizardStep:
        try:
            page_ids = await get_automation_ids(self.page)
        except Exception:
            logger.warning("workday.step_detection_failed")
            return WizardStep.UNKNOWN

        page_ids_set = set(page_ids)

        try:
            next_btn = await query_shadow_one(self.page, WORKDAY_SELECTORS["next_button"])
            if next_btn:
                btn_text = await self.page.evaluate(
                    "(el) => el?.innerText || ''",
                    next_btn,
                )
                if btn_text and "submit" in btn_text.lower():
                    return WizardStep.REVIEW
        except Exception as exc:
            logger.debug("workday.review_step_probe_failed", error=str(exc))

        best_step = WizardStep.UNKNOWN
        best_score = 0
        for step, indicators in STEP_INDICATORS.items():
            score = sum(1 for ind in indicators if ind in page_ids_set)
            if score > best_score:
                best_score = score
                best_step = step

        return best_step
