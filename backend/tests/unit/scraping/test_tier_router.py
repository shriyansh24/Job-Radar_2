from app.scraping.control.tier_router import TierRouter


def _make_target(**kwargs):
    """Create a minimal target-like object for testing."""
    from types import SimpleNamespace

    defaults = dict(
        ats_vendor=None, start_tier=1, max_tier=3, last_success_tier=None, consecutive_failures=0
    )
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
