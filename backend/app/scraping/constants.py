"""Single source of truth for scraper platform configuration."""

PRIORITY_INTERVALS: dict[str, int] = {
    "watchlist": 120,  # 2 hours
    "hot": 240,        # 4 hours
    "warm": 360,       # 6 hours
    "cool": 720,       # 12 hours
}

TIER_CONCURRENCY: dict[int, int] = {
    0: 50,   # API calls
    1: 30,   # HTTP fetch
    2: 8,    # Nodriver browser
    3: 3,    # Camoufox browser
}

MAX_GLOBAL_CONCURRENCY = 100
MAX_PER_DOMAIN_CONCURRENCY = 2
BROWSER_MEMORY_BUDGET_MB = 8192  # 8GB

QUARANTINE_THRESHOLD = 10  # consecutive failures
TIER_BUMP_THRESHOLD = 5    # consecutive failures at current tier

VALID_PRIORITY_CLASSES = frozenset({"watchlist", "hot", "warm", "cool"})
VALID_ATTEMPT_STATUSES = frozenset({
    "pending", "success", "partial", "failed", "skipped", "escalated", "not_modified"
})
