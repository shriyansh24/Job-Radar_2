from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EscalationReason(Enum):
    HTTP_FORBIDDEN = "http_403"
    RATE_LIMITED = "http_429"
    SERVER_ERROR = "http_5xx"
    TIMEOUT = "timeout"
    EMPTY_RESPONSE = "empty_response"
    ZERO_EXTRACTION = "zero_extraction"
    CLOUDFLARE_CHALLENGE = "cloudflare_challenge"


@dataclass(frozen=True)
class EscalationDecision:
    reason: EscalationReason
    skip_to_tier: int | None = None  # if set, skip directly to this tier
    retry_same: bool = False          # retry same tier before escalating
    backoff_seconds: float = 0        # wait before retry


CF_SIGNATURES = ["checking your browser", "cloudflare", "cf-browser-verification",
                  "ray id", "enable javascript and cookies"]


def should_escalate(
    status_code: int | None,
    jobs_found: int,
    html_length: int,
    html_snippet: str = "",
    timed_out: bool = False,
) -> EscalationDecision | None:
    """Determine if the current attempt should escalate to a higher tier."""

    if timed_out:
        return EscalationDecision(reason=EscalationReason.TIMEOUT)

    if status_code == 429:
        return EscalationDecision(reason=EscalationReason.RATE_LIMITED,
                                  retry_same=True, backoff_seconds=30)

    if status_code == 403:
        if _is_cloudflare(html_snippet):
            return EscalationDecision(reason=EscalationReason.CLOUDFLARE_CHALLENGE,
                                      skip_to_tier=2)
        return EscalationDecision(reason=EscalationReason.HTTP_FORBIDDEN)

    if status_code and status_code >= 500:
        return EscalationDecision(reason=EscalationReason.SERVER_ERROR,
                                  retry_same=True)

    if status_code == 200 and html_length == 0:
        return EscalationDecision(reason=EscalationReason.EMPTY_RESPONSE)

    if status_code == 200 and jobs_found == 0 and html_length > 0:
        return EscalationDecision(reason=EscalationReason.ZERO_EXTRACTION)

    if jobs_found > 0:
        return None  # success, no escalation

    return None


def _is_cloudflare(html: str) -> bool:
    lower = html.lower()
    return any(sig in lower for sig in CF_SIGNATURES)
