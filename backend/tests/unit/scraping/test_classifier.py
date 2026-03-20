# tests/unit/scraping/test_classifier.py
from app.scraping.control.classifier import classify_target, assign_priority


def test_classify_greenhouse_target():
    result = classify_target(
        url="https://boards.greenhouse.io/huggingface",
        company_name="Hugging Face",
    )
    assert result["ats_vendor"] == "greenhouse"
    assert result["ats_board_token"] == "huggingface"
    assert result["start_tier"] == 0
    assert result["source_kind"] == "ats_board"


def test_classify_unknown_target():
    result = classify_target(
        url="https://careers.google.com/jobs",
        company_name="Google",
    )
    assert result["ats_vendor"] is None
    assert result["start_tier"] == 1
    assert result["source_kind"] == "career_page"


def test_assign_priority_watchlist():
    p = assign_priority(lca_filings=5000, company_name="Google",
                        watchlist=["Google", "Meta", "OpenAI"])
    assert p["priority_class"] == "watchlist"
    assert p["schedule_interval_m"] == 120


def test_assign_priority_hot():
    p = assign_priority(lca_filings=2000, company_name="Acme Corp", watchlist=[])
    assert p["priority_class"] == "hot"
    assert p["schedule_interval_m"] == 240


def test_assign_priority_warm():
    p = assign_priority(lca_filings=500, company_name="MidCorp", watchlist=[])
    assert p["priority_class"] == "warm"


def test_assign_priority_cool():
    p = assign_priority(lca_filings=50, company_name="SmallCo", watchlist=[])
    assert p["priority_class"] == "cool"


def test_watchlist_override_low_filings():
    """Watchlist companies get watchlist priority regardless of LCA count."""
    p = assign_priority(lca_filings=10, company_name="OpenAI",
                        watchlist=["OpenAI"])
    assert p["priority_class"] == "watchlist"
