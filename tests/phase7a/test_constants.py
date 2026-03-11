"""Tests for Phase 7A shared constants and enums."""

from backend.phase7a.constants import (
    ATSProvider,
    SourceType,
    ValidationState,
    HealthState,
    ApplicationStatus,
    RemoteType,
    ExperienceLevel,
    JobType,
    ChangeSource,
    CheckType,
    CheckStatus,
    QueryStrictness,
    SOURCE_QUALITY_ORDER,
    CONFIDENCE_SIGNALS,
    CONFIDENCE_MAX,
    BACKOFF_SCHEDULE,
    HEALTH_DEGRADED_THRESHOLD,
    HEALTH_FAILING_THRESHOLD,
    HEALTH_DEAD_THRESHOLD,
)


class TestATSProvider:
    def test_expected_members(self):
        expected = {"greenhouse", "lever", "ashby", "workday", "icims", "taleo", "custom", "unknown"}
        actual = {m.value for m in ATSProvider}
        assert actual == expected

    def test_values_are_lowercase(self):
        for member in ATSProvider:
            assert member.value == member.value.lower()

    def test_string_comparison(self):
        assert ATSProvider.GREENHOUSE == "greenhouse"
        assert ATSProvider.LEVER == "lever"


class TestSourceType:
    def test_expected_members(self):
        expected = {"serpapi", "greenhouse", "lever", "ashby", "jobspy", "theirstack", "apify"}
        actual = {m.value for m in SourceType}
        assert actual == expected

    def test_values_are_lowercase(self):
        for member in SourceType:
            assert member.value == member.value.lower()


class TestValidationState:
    def test_expected_members(self):
        expected = {"unverified", "probing", "verified", "stale", "invalid"}
        actual = {m.value for m in ValidationState}
        assert actual == expected

    def test_initial_state(self):
        assert ValidationState.UNVERIFIED == "unverified"


class TestHealthState:
    def test_expected_members(self):
        expected = {"healthy", "degraded", "failing", "dead", "unknown"}
        actual = {m.value for m in HealthState}
        assert actual == expected

    def test_initial_state(self):
        assert HealthState.UNKNOWN == "unknown"


class TestApplicationStatus:
    def test_expected_members(self):
        expected = {
            "saved", "applied", "phone_screen", "interviewing", "final_round",
            "offer", "accepted", "declined", "rejected", "ghosted", "withdrawn",
        }
        actual = {m.value for m in ApplicationStatus}
        assert actual == expected

    def test_initial_state(self):
        assert ApplicationStatus.SAVED == "saved"

    def test_all_statuses_are_lowercase(self):
        for member in ApplicationStatus:
            assert member.value == member.value.lower()


class TestRemoteType:
    def test_expected_members(self):
        expected = {"remote", "hybrid", "onsite", "unknown"}
        actual = {m.value for m in RemoteType}
        assert actual == expected


class TestExperienceLevel:
    def test_expected_members(self):
        expected = {"entry", "mid", "senior", "exec"}
        actual = {m.value for m in ExperienceLevel}
        assert actual == expected


class TestJobType:
    def test_expected_members(self):
        expected = {"full-time", "part-time", "contract", "internship"}
        actual = {m.value for m in JobType}
        assert actual == expected


class TestChangeSource:
    def test_expected_members(self):
        expected = {"user", "system", "auto"}
        actual = {m.value for m in ChangeSource}
        assert actual == expected


class TestCheckType:
    def test_expected_members(self):
        expected = {"scrape", "probe", "health"}
        actual = {m.value for m in CheckType}
        assert actual == expected


class TestCheckStatus:
    def test_expected_members(self):
        expected = {"success", "failure", "timeout", "rate_limited"}
        actual = {m.value for m in CheckStatus}
        assert actual == expected


class TestQueryStrictness:
    def test_expected_members(self):
        expected = {"strict", "balanced", "broad"}
        actual = {m.value for m in QueryStrictness}
        assert actual == expected


class TestSourceQualityOrder:
    def test_contains_all_source_types(self):
        source_values = {s.value for s in SourceType}
        order_set = set(SOURCE_QUALITY_ORDER)
        assert order_set == source_values

    def test_no_duplicates(self):
        assert len(SOURCE_QUALITY_ORDER) == len(set(SOURCE_QUALITY_ORDER))

    def test_greenhouse_first(self):
        assert SOURCE_QUALITY_ORDER[0] == "greenhouse"

    def test_order_is_correct(self):
        assert SOURCE_QUALITY_ORDER.index("greenhouse") < SOURCE_QUALITY_ORDER.index("serpapi")
        assert SOURCE_QUALITY_ORDER.index("lever") < SOURCE_QUALITY_ORDER.index("jobspy")


class TestConfidenceSignals:
    def test_has_expected_signals(self):
        expected_keys = {
            "domain_verified", "careers_page_200", "ats_pattern_matched",
            "ats_api_responds", "multi_source_confirm", "jobs_scraped",
        }
        assert set(CONFIDENCE_SIGNALS.keys()) == expected_keys

    def test_all_values_positive(self):
        for value in CONFIDENCE_SIGNALS.values():
            assert value > 0

    def test_max_not_exceeded(self):
        assert CONFIDENCE_MAX == 100


class TestBackoffSchedule:
    def test_is_sorted_by_threshold(self):
        thresholds = [t[0] for t in BACKOFF_SCHEDULE]
        assert thresholds == sorted(thresholds)

    def test_backoff_increases(self):
        durations = [t[1] for t in BACKOFF_SCHEDULE]
        assert durations == sorted(durations)

    def test_starts_at_5_minutes(self):
        assert BACKOFF_SCHEDULE[0] == (1, 300)


class TestHealthThresholds:
    def test_ordering(self):
        assert HEALTH_DEGRADED_THRESHOLD < HEALTH_FAILING_THRESHOLD < HEALTH_DEAD_THRESHOLD

    def test_degraded_at_3(self):
        assert HEALTH_DEGRADED_THRESHOLD == 3


class TestNoDuplicateEnumValues:
    """Verify no enum has duplicate values (catches copy-paste errors)."""

    def test_all_enums_unique_values(self):
        enums = [
            ATSProvider, SourceType, ValidationState, HealthState,
            ApplicationStatus, RemoteType, ExperienceLevel, JobType,
            ChangeSource, CheckType, CheckStatus, QueryStrictness,
        ]
        for enum_cls in enums:
            values = [m.value for m in enum_cls]
            assert len(values) == len(set(values)), (
                f"Duplicate values in {enum_cls.__name__}: {values}"
            )
