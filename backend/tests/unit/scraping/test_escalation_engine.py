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
