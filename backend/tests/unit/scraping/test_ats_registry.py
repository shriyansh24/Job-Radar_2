# tests/unit/scraping/test_ats_registry.py
from app.scraping.control.ats_registry import ATS_RULES, classify_url


def test_greenhouse_url():
    result = classify_url("https://boards.greenhouse.io/huggingface")
    assert result.vendor == "greenhouse"
    assert result.board_token == "huggingface"
    assert result.start_tier == 0


def test_lever_url():
    result = classify_url("https://jobs.lever.co/stripe")
    assert result.vendor == "lever"
    assert result.board_token == "stripe"
    assert result.start_tier == 0


def test_ashby_url():
    result = classify_url("https://jobs.ashbyhq.com/ramp")
    assert result.vendor == "ashby"
    assert result.board_token == "ramp"
    assert result.start_tier == 0


def test_workday_url():
    result = classify_url("https://microsoft.wd5.myworkdayjobs.com/en-US/Global/")
    assert result.vendor == "workday"
    assert result.start_tier == 0


def test_unknown_url():
    result = classify_url("https://careers.google.com/jobs")
    assert result.vendor is None
    assert result.start_tier == 1


def test_icims_url():
    result = classify_url("https://careers-acme.icims.com/jobs")
    assert result.vendor == "icims"
    assert result.start_tier == 1


def test_registry_is_extensible():
    assert isinstance(ATS_RULES, list)
    required_keys = {"vendor", "url_patterns", "start_tier"}
    assert all(required_keys.issubset(rule.keys()) for rule in ATS_RULES)
