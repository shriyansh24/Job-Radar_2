"""Shared enums and constants for all Phase 7A modules.

These values are used across Company Registry (M1), Search Expansion (M2),
Source Cache (M3), Canonical Jobs (M4), and Application Tracker (M5).
"""

from enum import Enum


class ATSProvider(str, Enum):
    """Applicant Tracking System providers detected by Company Registry (M1)."""
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKDAY = "workday"
    ICIMS = "icims"
    TALEO = "taleo"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    """Scraper source types used across M3 (Source Cache) and M4 (Canonical Jobs)."""
    SERPAPI = "serpapi"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    JOBSPY = "jobspy"
    THEIRSTACK = "theirstack"
    APIFY = "apify"


class ValidationState(str, Enum):
    """Company validation state machine (M1).

    Transitions:
        unverified -> probing -> verified -> stale -> (re-probe)
        unverified -> probing -> invalid -> (retry after 7d)
    """
    UNVERIFIED = "unverified"
    PROBING = "probing"
    VERIFIED = "verified"
    STALE = "stale"
    INVALID = "invalid"


class HealthState(str, Enum):
    """Source health state machine (M3).

    Transitions:
        unknown -> healthy (success) | degraded (failure)
        healthy -> degraded (3 consecutive failures)
        degraded -> failing (5 more failures)
        failing -> dead (10 more failures)
        any -> healthy (1 success)
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    DEAD = "dead"
    UNKNOWN = "unknown"


class ApplicationStatus(str, Enum):
    """Application tracker status state machine (M5).

    Transitions:
        saved -> applied -> phone_screen -> interviewing -> final_round -> offer
        offer -> accepted | declined
        applied/phone_screen/interviewing/final_round -> rejected | ghosted
        any active -> withdrawn
    """
    SAVED = "saved"
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    INTERVIEWING = "interviewing"
    FINAL_ROUND = "final_round"
    OFFER = "offer"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    WITHDRAWN = "withdrawn"


class RemoteType(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    EXEC = "exec"


class JobType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class ChangeSource(str, Enum):
    """Who initiated a status change (M5 audit trail)."""
    USER = "user"
    SYSTEM = "system"
    AUTO = "auto"


class CheckType(str, Enum):
    """Source check types (M3)."""
    SCRAPE = "scrape"
    PROBE = "probe"
    HEALTH = "health"


class CheckStatus(str, Enum):
    """Source check result statuses (M3)."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class QueryStrictness(str, Enum):
    """Search expansion strictness levels (M2)."""
    STRICT = "strict"
    BALANCED = "balanced"
    BROAD = "broad"


# --- Constants ---

# Source quality order for merge precedence (M4).
# Higher-indexed sources are lower quality.
SOURCE_QUALITY_ORDER: list[str] = [
    SourceType.GREENHOUSE.value,
    SourceType.LEVER.value,
    SourceType.ASHBY.value,
    SourceType.SERPAPI.value,
    SourceType.THEIRSTACK.value,
    SourceType.JOBSPY.value,
    SourceType.APIFY.value,
]

# Company confidence scoring signals and max points (M1).
CONFIDENCE_SIGNALS: dict[str, int] = {
    "domain_verified": 20,
    "careers_page_200": 15,
    "ats_pattern_matched": 25,
    "ats_api_responds": 30,
    "multi_source_confirm": 10,  # per source, max 30
    "jobs_scraped": 5,
}
CONFIDENCE_MAX = 100
CONFIDENCE_MULTI_SOURCE_CAP = 30

# Source health backoff schedule (M3).
# (consecutive_failures_threshold, backoff_seconds)
BACKOFF_SCHEDULE: list[tuple[int, int]] = [
    (1, 300),       # 1-2 failures: 5 minutes
    (3, 1800),      # 3-4 failures: 30 minutes
    (5, 7200),      # 5-9 failures: 2 hours
    (10, 43200),    # 10-19 failures: 12 hours
    (20, 604800),   # 20+ failures: 7 days
]

# Health state transition thresholds (M3).
HEALTH_DEGRADED_THRESHOLD = 3
HEALTH_FAILING_THRESHOLD = 8   # 3 + 5 more
HEALTH_DEAD_THRESHOLD = 18     # 3 + 5 + 10 more

# Company validation refresh intervals (M1).
VALIDATION_STALE_DAYS = 30
VALIDATION_RETRY_DAYS = 7
VALIDATION_BATCH_SIZE = 50
VALIDATION_PARALLEL_PROBES = 5

# Canonical job lifecycle thresholds (M4).
CANONICAL_STALE_SCRAPES = 2     # mark stale after missing from N scrapes
CANONICAL_CLOSED_DAYS = 14      # mark closed after N days without sighting

# Application status transitions (M5 state machine).
# Maps each status to the set of statuses it can transition to.
VALID_STATUS_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.SAVED: {
        ApplicationStatus.APPLIED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.APPLIED: {
        ApplicationStatus.PHONE_SCREEN,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.REJECTED,
        ApplicationStatus.GHOSTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.PHONE_SCREEN: {
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.REJECTED,
        ApplicationStatus.GHOSTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.INTERVIEWING: {
        ApplicationStatus.FINAL_ROUND,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.GHOSTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.FINAL_ROUND: {
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.GHOSTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.OFFER: {
        ApplicationStatus.ACCEPTED,
        ApplicationStatus.DECLINED,
        ApplicationStatus.WITHDRAWN,
    },
    # Terminal states: no transitions out
    ApplicationStatus.ACCEPTED: set(),
    ApplicationStatus.DECLINED: set(),
    ApplicationStatus.REJECTED: set(),
    ApplicationStatus.GHOSTED: set(),
    ApplicationStatus.WITHDRAWN: set(),
}

# Maps status values to auto-set timestamp fields on the Application model (M5).
STATUS_TIMESTAMP_MAP: dict[ApplicationStatus, str] = {
    ApplicationStatus.APPLIED: "applied_at",
    ApplicationStatus.PHONE_SCREEN: "response_at",
    ApplicationStatus.INTERVIEWING: "interview_at",
    ApplicationStatus.OFFER: "offer_at",
    ApplicationStatus.REJECTED: "rejected_at",
}
