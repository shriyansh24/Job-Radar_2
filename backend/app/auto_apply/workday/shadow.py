from __future__ import annotations

from typing import Any

from .constants import JS_DETECT_AUTOMATION_IDS, JS_QUERY_SHADOW, JS_QUERY_SHADOW_ONE


async def query_shadow(page: Any, selector: str) -> list[Any]:
    return await page.evaluate(JS_QUERY_SHADOW, selector)


async def query_shadow_one(page: Any, selector: str) -> Any | None:
    return await page.evaluate(JS_QUERY_SHADOW_ONE, selector)


async def get_automation_ids(page: Any) -> list[str]:
    return await page.evaluate(JS_DETECT_AUTOMATION_IDS)
