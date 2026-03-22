from __future__ import annotations

import pytest
from sqlalchemy import DateTime

from app.auth.models import User
from app.auto_apply.models import AutoApplyProfile, AutoApplyRule, AutoApplyRun
from app.canonical_jobs.models import CanonicalJob, RawJobSource
from app.companies.models import Company
from app.copilot.models import CoverLetter
from app.followup.models import FollowupReminder
from app.interview.models import InterviewSession
from app.jobs.models import Job
from app.pipeline.models import Application, ApplicationStatusHistory
from app.profile.models import UserProfile
from app.resume.models import ResumeVersion
from app.salary.models import SalaryCache
from app.search_expansion.models import ExpansionRule, QueryPerformance, QueryTemplate
from app.settings.models import SavedSearch
from app.source_health.models import SourceCheckLog, SourceRegistry
from app.scraping.models import ScrapeAttempt


@pytest.mark.parametrize(
    "model, columns",
    [
        (User, ["created_at", "updated_at"]),
        (AutoApplyProfile, ["created_at"]),
        (AutoApplyRule, ["created_at"]),
        (AutoApplyRun, ["started_at", "completed_at"]),
        (Job, ["expires_at"]),
        (Application, ["applied_at", "offer_at", "rejected_at", "follow_up_at", "reminder_at", "created_at", "updated_at"]),
        (ApplicationStatusHistory, ["changed_at"]),
        (CanonicalJob, ["first_seen_at", "last_refreshed_at", "created_at", "updated_at"]),
        (RawJobSource, ["scraped_at", "created_at"]),
        (Company, ["last_validated_at", "last_probe_at", "created_at", "updated_at"]),
        (CoverLetter, ["created_at"]),
        (FollowupReminder, ["reminder_at", "created_at"]),
        (InterviewSession, ["created_at"]),
        (UserProfile, ["available_start", "created_at", "updated_at"]),
        (ResumeVersion, ["created_at"]),
        (SalaryCache, ["created_at"]),
        (QueryTemplate, ["created_at", "updated_at"]),
        (ExpansionRule, ["created_at"]),
        (QueryPerformance, ["executed_at"]),
        (SavedSearch, ["last_checked_at", "created_at"]),
        (SourceRegistry, ["last_check_at", "backoff_until", "created_at"]),
        (SourceCheckLog, ["checked_at"]),
        (ScrapeAttempt, ["created_at"]),
    ],
)
def test_datetime_columns_are_timezone_aware(model, columns):
    for column in columns:
        field = model.__table__.columns[column]
        assert isinstance(field.type, DateTime)
        assert field.type.timezone is True


def test_user_token_version_defaults_to_zero():
    col = User.__table__.columns["token_version"]

    assert col.default is not None
    assert col.default.arg == 0
    assert col.server_default is not None


@pytest.mark.parametrize(
    "model, column",
    [
        (AutoApplyRun, "job_id"),
        (Application, "job_id"),
        (CoverLetter, "job_id"),
        (InterviewSession, "job_id"),
    ],
)
def test_nullable_job_foreign_keys_set_null(model, column):
    foreign_keys = list(model.__table__.columns[column].foreign_keys)

    assert len(foreign_keys) == 1
    assert foreign_keys[0].ondelete == "SET NULL"
