# Chunk 2: Tier Router + Execution Ports + Escalation Engine
> **Depends on:** Chunk 1 (database tables, constants, ATS registry, classifier)
> **Produces:** FetcherPort, BrowserPort, ExtractorPort ABCs, TierRouter with ExecutionPlan, EscalationEngine, PriorityScorer
> **Spec sections:** 3.1, 3.4-3.6, 4.1-4.3, 5.1

---

### Task 11: Create Execution Port Interfaces

**Files:**
- Create: `backend/app/scraping/execution/__init__.py`
- Create: `backend/app/scraping/execution/fetcher_port.py`
- Create: `backend/app/scraping/execution/browser_port.py`
- Create: `backend/app/scraping/execution/extractor_port.py`

- [ ] **Step 1: Write test for port interfaces**

```python
# tests/unit/scraping/test_execution_ports.py
from app.scraping.execution.fetcher_port import FetcherPort, FetchResult
from app.scraping.execution.browser_port import BrowserPort, BrowserResult
from app.scraping.execution.extractor_port import ExtractorPort

def test_fetch_result_dataclass():
    r = FetchResult(html="<html>", status_code=200, headers={},
                    url_final="https://example.com", duration_ms=100,
                    content_hash="abc123")
    assert r.html == "<html>"
    assert r.status_code == 200

def test_browser_result_dataclass():
    r = BrowserResult(html="<html>", status_code=200,
                      url_final="https://example.com", duration_ms=500,
                      content_hash="def456")
    assert r.screenshot is None  # optional

def test_fetcher_port_is_abstract():
    """Cannot instantiate FetcherPort directly."""
    import pytest
    with pytest.raises(TypeError):
        FetcherPort()

def test_browser_port_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        BrowserPort()
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Create fetcher_port.py**

```python
# app/scraping/execution/fetcher_port.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True)
class FetchResult:
    html: str
    status_code: int
    headers: dict[str, str]
    url_final: str
    duration_ms: int
    content_hash: str

class FetcherPort(ABC):
    @property
    @abstractmethod
    def fetcher_name(self) -> str: ...

    @abstractmethod
    async def fetch(self, url: str, timeout_s: int = 30,
                    user_agent: str | None = None) -> FetchResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None:
        pass
```

- [ ] **Step 4: Create browser_port.py**

```python
# app/scraping/execution/browser_port.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass(frozen=True)
class BrowserResult:
    html: str
    status_code: int
    url_final: str
    duration_ms: int
    content_hash: str
    screenshot: bytes | None = None

class BrowserPort(ABC):
    @property
    @abstractmethod
    def browser_name(self) -> str: ...

    @abstractmethod
    async def render(self, url: str, timeout_s: int = 60,
                     fingerprint: dict | None = None,
                     wait_for_selector: str | None = None) -> BrowserResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None:
        pass
```

- [ ] **Step 5: Create extractor_port.py**

```python
# app/scraping/execution/extractor_port.py
from __future__ import annotations
from abc import ABC, abstractmethod
from app.scraping.port import ScrapedJob

class ExtractorPort(ABC):
    @abstractmethod
    async def extract_jobs(self, html: str, url: str) -> list[ScrapedJob]: ...

    @abstractmethod
    async def to_markdown(self, html: str) -> str: ...
```

- [ ] **Step 6: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_execution_ports.py -v
git add app/scraping/execution/ tests/unit/scraping/test_execution_ports.py
git commit -m "feat: add FetcherPort, BrowserPort, ExtractorPort interfaces"
```

---

### Task 12: Build Tier Router

**Files:**
- Create: `backend/app/scraping/control/tier_router.py`
- Test: `backend/tests/unit/scraping/test_tier_router.py`

> **IMPORTANT:** `ExecutionPlan.fallback_chain` uses `tuple[Step, ...]` (not `list[Step]`) to ensure true immutability of frozen dataclasses. The `TierRouter.route()` method must convert the pruned list to a tuple via `tuple(pruned[1:])`.

- [ ] **Step 1: Write tests**

```python
# tests/unit/scraping/test_tier_router.py
import pytest
from app.scraping.control.tier_router import TierRouter, ExecutionPlan, Step

def _make_target(**kwargs):
    """Create a minimal target-like object for testing."""
    from types import SimpleNamespace
    defaults = dict(ats_vendor=None, start_tier=1, max_tier=3,
                    last_success_tier=None, consecutive_failures=0)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)

def test_tier0_greenhouse():
    plan = TierRouter.route(_make_target(ats_vendor="greenhouse"))
    assert plan.primary_tier == 0
    assert plan.primary_step.scraper_name == "greenhouse"
    assert plan.fallback_chain == ()

def test_tier0_lever():
    plan = TierRouter.route(_make_target(ats_vendor="lever"))
    assert plan.primary_tier == 0
    assert plan.primary_step.scraper_name == "lever"

def test_tier0_workday():
    plan = TierRouter.route(_make_target(ats_vendor="workday"))
    assert plan.primary_tier == 0

def test_unknown_starts_tier1():
    plan = TierRouter.route(_make_target())
    assert plan.primary_tier == 1
    assert plan.primary_step.tier == 1
    assert len(plan.fallback_chain) > 0

def test_history_skips_lower_tiers():
    plan = TierRouter.route(_make_target(last_success_tier=2))
    assert plan.primary_tier == 2
    assert plan.primary_step.tier == 2
    assert all(s.tier >= 2 for s in plan.fallback_chain)

def test_max_tier_caps_fallback():
    plan = TierRouter.route(_make_target(max_tier=1))
    assert all(s.tier <= 1 for s in plan.fallback_chain)
    assert plan.max_tier == 1

def test_fallback_chain_has_browser_flag():
    plan = TierRouter.route(_make_target())
    tier2_steps = [s for s in plan.fallback_chain if s.tier >= 2]
    assert all(s.browser_required for s in tier2_steps)

def test_fallback_chain_is_tuple():
    """ExecutionPlan.fallback_chain must be a tuple for true immutability."""
    plan = TierRouter.route(_make_target())
    assert isinstance(plan.fallback_chain, tuple)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Create tier_router.py**

```python
# app/scraping/control/tier_router.py
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Step:
    tier: int
    scraper_name: str
    parser_name: str = "adaptive"
    timeout_s: int = 30
    browser_required: bool = False

@dataclass(frozen=True)
class ExecutionPlan:
    primary_tier: int
    max_tier: int
    primary_step: Step
    fallback_chain: tuple[Step, ...]  # tuple, not list — truly immutable
    rate_policy: str = "generic"

TIER_0_VENDORS = {"greenhouse", "lever", "ashby", "workday"}

ATS_SCRAPER_MAP = {
    "greenhouse": "greenhouse", "lever": "lever",
    "ashby": "ashby", "workday": "workday",
}
ATS_PARSER_MAP = {
    "greenhouse": "greenhouse_api", "lever": "lever_api",
    "ashby": "ashby_graphql", "workday": "workday_json",
}

FULL_FALLBACK_CHAIN = [
    Step(tier=1, scraper_name="cloudscraper", parser_name="adaptive"),
    Step(tier=1, scraper_name="scrapling_fast", parser_name="adaptive"),
    Step(tier=2, scraper_name="nodriver", parser_name="adaptive",
         timeout_s=60, browser_required=True),
    Step(tier=2, scraper_name="scrapling_stealth", parser_name="adaptive",
         timeout_s=60, browser_required=True),
    Step(tier=3, scraper_name="camoufox", parser_name="adaptive",
         timeout_s=90, browser_required=True),
    Step(tier=3, scraper_name="seleniumbase", parser_name="adaptive",
         timeout_s=90, browser_required=True),
]

class TierRouter:
    @staticmethod
    def route(target) -> ExecutionPlan:
        if target.ats_vendor in TIER_0_VENDORS:
            return ExecutionPlan(
                primary_tier=0,
                max_tier=0,
                primary_step=Step(
                    tier=0,
                    scraper_name=ATS_SCRAPER_MAP[target.ats_vendor],
                    parser_name=ATS_PARSER_MAP[target.ats_vendor],
                ),
                fallback_chain=(),  # empty tuple for ATS targets
                rate_policy=target.ats_vendor,
            )

        effective_start = target.last_success_tier or target.start_tier
        pruned = [s for s in FULL_FALLBACK_CHAIN
                  if s.tier >= effective_start and s.tier <= target.max_tier]

        if not pruned:
            pruned = [Step(tier=1, scraper_name="cloudscraper")]

        return ExecutionPlan(
            primary_tier=effective_start,
            max_tier=target.max_tier,
            primary_step=pruned[0],
            fallback_chain=tuple(pruned[1:]),  # convert to tuple for immutability
        )
```

- [ ] **Step 4: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_tier_router.py -v
git add app/scraping/control/tier_router.py tests/unit/scraping/test_tier_router.py
git commit -m "feat: add tier router with execution plan and fallback chain"
```

---

### Task 13: Build Escalation Engine

**Files:**
- Create: `backend/app/scraping/execution/escalation_engine.py`
- Test: `backend/tests/unit/scraping/test_escalation_engine.py`

- [ ] **Step 1: Write tests**

```python
# tests/unit/scraping/test_escalation_engine.py
import pytest
from app.scraping.execution.escalation_engine import should_escalate, EscalationReason

def test_403_triggers_escalation():
    assert should_escalate(status_code=403, jobs_found=0, html_length=0)
    assert should_escalate(status_code=403, jobs_found=0, html_length=0).reason == EscalationReason.HTTP_FORBIDDEN

def test_429_triggers_escalation():
    result = should_escalate(status_code=429, jobs_found=0, html_length=0)
    assert result
    assert result.reason == EscalationReason.RATE_LIMITED

def test_200_with_jobs_no_escalation():
    result = should_escalate(status_code=200, jobs_found=5, html_length=5000)
    assert result is None

def test_200_empty_page_escalates():
    result = should_escalate(status_code=200, jobs_found=0, html_length=0)
    assert result
    assert result.reason == EscalationReason.EMPTY_RESPONSE

def test_200_nonempty_zero_jobs_escalates():
    result = should_escalate(status_code=200, jobs_found=0, html_length=5000)
    assert result
    assert result.reason == EscalationReason.ZERO_EXTRACTION

def test_cloudflare_challenge_detected():
    result = should_escalate(status_code=403, jobs_found=0, html_length=2000,
                             html_snippet="Checking your browser")
    assert result
    assert result.reason == EscalationReason.CLOUDFLARE_CHALLENGE
    assert result.skip_to_tier >= 2

def test_timeout_triggers_escalation():
    result = should_escalate(status_code=None, jobs_found=0, html_length=0,
                             timed_out=True)
    assert result
    assert result.reason == EscalationReason.TIMEOUT
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Create escalation_engine.py**

```python
# app/scraping/execution/escalation_engine.py
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
```

- [ ] **Step 4: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_escalation_engine.py -v
git add app/scraping/execution/escalation_engine.py tests/unit/scraping/test_escalation_engine.py
git commit -m "feat: add escalation engine with trigger detection"
```

---

### Task 14: Build Priority Scorer

**Files:**
- Create: `backend/app/scraping/control/priority_scorer.py`
- Test: `backend/tests/unit/scraping/test_priority_scorer.py`

- [ ] **Step 1: Write tests**

```python
# tests/unit/scraping/test_priority_scorer.py
from app.scraping.control.priority_scorer import compute_priority_score
from types import SimpleNamespace
from datetime import datetime, timedelta, UTC

def _target(**kw):
    defaults = dict(priority_class="cool", consecutive_failures=0,
                    last_success_tier=1, last_success_at=None,
                    next_scheduled_at=None, schedule_interval_m=720)
    defaults.update(kw)
    return SimpleNamespace(**defaults)

def test_watchlist_highest():
    assert compute_priority_score(_target(priority_class="watchlist")) > \
           compute_priority_score(_target(priority_class="hot"))

def test_hot_above_warm():
    assert compute_priority_score(_target(priority_class="hot")) > \
           compute_priority_score(_target(priority_class="warm"))

def test_never_scraped_gets_bonus():
    never = compute_priority_score(_target(last_success_at=None))
    recent = compute_priority_score(_target(
        last_success_at=datetime.now(UTC)))
    assert never > recent

def test_failures_reduce_score():
    clean = compute_priority_score(_target(consecutive_failures=0))
    failing = compute_priority_score(_target(consecutive_failures=5))
    assert clean > failing

def test_expensive_tier_penalized():
    cheap = compute_priority_score(_target(last_success_tier=0))
    expensive = compute_priority_score(_target(last_success_tier=3))
    assert cheap > expensive

def test_overdue_bonus_requires_both_fields():
    """Overdue bonus only applies when BOTH last_success_at and next_scheduled_at exist."""
    # Has last_success_at but no next_scheduled_at — should NOT crash
    score = compute_priority_score(_target(
        last_success_at=datetime.now(UTC),
        next_scheduled_at=None,
    ))
    assert isinstance(score, (int, float))
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Create priority_scorer.py**

```python
# app/scraping/control/priority_scorer.py
from __future__ import annotations
from datetime import datetime, UTC

BASE_PRIORITY = {"watchlist": 100, "hot": 70, "warm": 40, "cool": 10}

def compute_priority_score(target) -> float:
    score = BASE_PRIORITY.get(target.priority_class, 10)

    # Recency bonus
    if target.last_success_at is None:
        score += 20  # never scraped
    elif target.last_success_at and target.next_scheduled_at:
        # Only compute overdue if BOTH values exist (defensive check)
        overdue = (datetime.now(UTC) - target.next_scheduled_at).total_seconds()
        interval_s = target.schedule_interval_m * 60
        if overdue > interval_s * 2:
            score += 10
        elif overdue > interval_s:
            score += 5

    # Failure penalty
    score -= target.consecutive_failures * 15

    # Cost penalty
    tier = target.last_success_tier or 0
    if tier >= 3:
        score -= 10
    elif tier >= 2:
        score -= 5

    return score
```

- [ ] **Step 4: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_priority_scorer.py -v
git add app/scraping/control/priority_scorer.py tests/unit/scraping/test_priority_scorer.py
git commit -m "feat: add priority scorer for scheduler"
```

---

## Chunk Status
- [x] All tasks completed
- [x] All tests passing (26 tests: 5 ports + 8 router + 7 escalation + 6 scorer)
- [x] Execution ports defined (FetcherPort, BrowserPort, ExtractorPort)
- [x] TierRouter routes targets correctly (Tier 0 ATS, Tier 1-3 generic)
- [x] EscalationEngine detects all trigger conditions
- [x] PriorityScorer ranks targets for scheduling

### Notes / Issues Encountered

| Date | Note |
|------|------|
| 2026-03-19 | Plan intentionally omits `success_rate_bonus` from priority scorer (spec section 5.2) — requires historical attempt data not available through lightweight target interface. Deferred to integration chunk. |
| 2026-03-19 | Plan intentionally omits "Tier 3 fails 3x -> quarantine" trigger from escalation engine (spec section 3.5) — quarantine logic belongs at orchestration layer, not in per-attempt decisions. |
| 2026-03-19 | Plan intentionally omits "0 jobs -> AIScraper LLM fallback" trigger — LLM fallback is a separate execution step, not an escalation decision. |
| 2026-03-19 | Code review found missing ExtractorPort abstractness test — fixed in commit 0344aa3. |
