from __future__ import annotations

from dataclasses import dataclass


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
