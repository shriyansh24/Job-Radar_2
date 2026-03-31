from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from protego import Protego


@dataclass(frozen=True)
class RobotsDecision:
    allowed: bool
    reason: str
    robots_url: str
    from_cache: bool = False


@dataclass(frozen=True)
class RobotsCacheEntry:
    parser: Protego | None
    unavailable_reason: str | None = None


async def evaluate_robots(
    url: str,
    user_agent: str,
    cache: dict[str, RobotsCacheEntry],
    *,
    timeout_s: float = 10.0,
) -> RobotsDecision:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return RobotsDecision(
            allowed=True,
            reason="unsupported_scheme",
            robots_url=url,
        )

    origin = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{origin}/robots.txt"
    cache_key = origin.lower()
    cached = cache.get(cache_key)
    if cache_key in cache:
        if cached is None or cached.parser is None:
            reason = (
                cached.unavailable_reason
                if cached is not None and cached.unavailable_reason
                else "robots_unavailable"
            )
            return RobotsDecision(
                allowed=True,
                reason=reason,
                robots_url=robots_url,
                from_cache=True,
            )
        allowed = cached.parser.can_fetch(url, user_agent)
        return RobotsDecision(
            allowed=allowed,
            reason="robots_allowed" if allowed else "robots_disallowed",
            robots_url=robots_url,
            from_cache=True,
        )

    try:
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            response = await client.get(robots_url, headers={"User-Agent": user_agent})
    except Exception:
        cache[cache_key] = RobotsCacheEntry(parser=None, unavailable_reason="robots_unavailable")
        return RobotsDecision(
            allowed=True,
            reason="robots_unavailable",
            robots_url=robots_url,
        )

    if response.status_code == 404:
        cache[cache_key] = RobotsCacheEntry(parser=None, unavailable_reason="robots_missing")
        return RobotsDecision(
            allowed=True,
            reason="robots_missing",
            robots_url=robots_url,
        )

    if response.status_code != 200:
        cache[cache_key] = RobotsCacheEntry(
            parser=None,
            unavailable_reason=f"robots_http_{response.status_code}",
        )
        return RobotsDecision(
            allowed=True,
            reason=f"robots_http_{response.status_code}",
            robots_url=robots_url,
        )

    try:
        parser = Protego.parse(response.text)
    except Exception:
        cache[cache_key] = RobotsCacheEntry(parser=None, unavailable_reason="robots_invalid")
        return RobotsDecision(
            allowed=True,
            reason="robots_invalid",
            robots_url=robots_url,
        )

    cache[cache_key] = RobotsCacheEntry(parser=parser)
    allowed = parser.can_fetch(url, user_agent)
    return RobotsDecision(
        allowed=allowed,
        reason="robots_allowed" if allowed else "robots_disallowed",
        robots_url=robots_url,
    )
