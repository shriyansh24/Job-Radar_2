"""Tests for FieldMapper and FIELD_PATTERNS."""

from __future__ import annotations

import re

import pytest

from app.auto_apply.field_mapper import (
    _RAW_PATTERNS,
    EEOC_DEFAULT,
    FIELD_PATTERNS,
    FieldMapper,
    MappedField,
)
from app.auto_apply.form_extractor import FormField

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_PROFILE: dict[str, str] = {
    "first_name": "Jane",
    "last_name": "Doe",
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1-555-0100",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94102",
    "country": "United States",
    "linkedin_url": "https://linkedin.com/in/janedoe",
    "github_url": "https://github.com/janedoe",
    "website_url": "https://janedoe.dev",
    "current_company": "Acme Corp",
    "current_title": "Senior Engineer",
    "years_experience": "8",
    "desired_salary": "180000",
    "work_authorization": "Yes",
    "requires_sponsorship": "No",
    "start_date": "2026-04-15",
    "highest_degree": "Bachelor's",
    "school_name": "Stanford University",
    "major": "Computer Science",
    "resume_file": "/path/to/resume.pdf",
    "cover_letter": "I am excited to apply...",
}


def _make_field(
    label: str,
    field_type: str = "text",
    *,
    name_attr: str | None = None,
    placeholder: str | None = None,
) -> FormField:
    return FormField(
        label=label,
        field_type=field_type,
        required=False,
        aria_role="textbox",
        locator_desc=f"#f_{label.replace(' ', '_').lower()}",
        name_attr=name_attr,
        placeholder=placeholder,
    )


# ---------------------------------------------------------------------------
# Pattern compilation tests
# ---------------------------------------------------------------------------


class TestFieldPatterns:
    def test_all_patterns_compile(self) -> None:
        """All patterns in FIELD_PATTERNS must compile without error."""
        for pattern in FIELD_PATTERNS:
            assert isinstance(pattern, re.Pattern), f"Pattern not compiled: {pattern}"

    def test_pattern_count_minimum(self) -> None:
        """Must have at least 120 patterns."""
        assert len(FIELD_PATTERNS) >= 120, f"Only {len(FIELD_PATTERNS)} patterns, need 120+"

    def test_raw_patterns_match_compiled(self) -> None:
        """_RAW_PATTERNS and FIELD_PATTERNS should have same count."""
        assert len(_RAW_PATTERNS) == len(FIELD_PATTERNS)


class TestPatternMatching:
    """Test that common field labels match expected semantic keys."""

    @pytest.mark.parametrize(
        "label,expected_key",
        [
            # Names
            ("First Name", "first_name"),
            ("first name", "first_name"),
            ("FirstName", "first_name"),
            ("Last Name", "last_name"),
            ("Surname", "last_name"),
            ("Family Name", "last_name"),
            ("Given Name", "first_name"),
            ("Full Name", "full_name"),
            ("Legal Name", "full_name"),
            ("Middle Name", "middle_name"),
            ("Middle Initial", "middle_name"),
            ("Preferred Name", "preferred_name"),
            # Contact
            ("Email", "email"),
            ("E-mail", "email"),
            ("Email Address", "email"),
            ("e-mail address", "email"),
            ("Phone", "phone"),
            ("Phone Number", "phone"),
            ("Mobile", "phone"),
            ("Mobile Number", "phone"),
            ("Cell Phone", "phone"),
            # Address
            ("City", "city"),
            ("State", "state"),
            ("Province", "state"),
            ("Zip Code", "zip_code"),
            ("Postal Code", "zip_code"),
            ("Country", "country"),
            ("Street Address", "street_address"),
            ("Address Line 1", "address_line1"),
            ("Address Line 2", "address_line2"),
            # Links
            ("LinkedIn", "linkedin_url"),
            ("LinkedIn URL", "linkedin_url"),
            ("GitHub", "github_url"),
            ("Portfolio", "website_url"),
            ("Personal Website", "website_url"),
            ("Website URL", "website_url"),
            # Position
            ("Current Company", "current_company"),
            ("Current Employer", "current_company"),
            ("Current Title", "current_title"),
            ("Job Title", "current_title"),
            # Experience
            ("Years of Experience", "years_experience"),
            ("Total Experience", "years_experience"),
            ("Years Experience", "years_experience"),
            # Salary
            ("Salary Expectation", "desired_salary"),
            ("Desired Salary", "desired_salary"),
            ("Expected Compensation", "desired_salary"),
            ("Compensation", "desired_salary"),
            # Availability
            ("Start Date", "start_date"),
            ("Available From", "start_date"),
            ("Date Available", "start_date"),
            ("Willing to Relocate", "willing_to_relocate"),
            # Authorization
            ("Work Authorization", "work_authorization"),
            ("Authorized to Work", "work_authorization"),
            ("Legally Authorized", "work_authorization"),
            ("Require Sponsorship", "requires_sponsorship"),
            ("Visa Sponsorship", "requires_sponsorship"),
            # Education
            ("Highest Degree", "highest_degree"),
            ("Education Level", "highest_degree"),
            ("University", "school_name"),
            ("College", "school_name"),
            ("GPA", "gpa"),
            ("Major", "major"),
            ("Field of Study", "major"),
            ("Graduation Date", "graduation_date"),
            # Documents
            ("Resume", "resume_file"),
            ("CV", "resume_file"),
            ("Cover Letter", "cover_letter"),
            # EEOC
            ("Gender", "__eeoc_gender"),
            ("Gender Identity", "__eeoc_gender"),
            ("Race", "__eeoc_race"),
            ("Ethnicity", "__eeoc_race"),
            ("Veteran Status", "__eeoc_veteran"),
            ("Disability Status", "__eeoc_disability"),
            ("Sexual Orientation", "__eeoc_sexual_orientation"),
            # Source
            ("How did you hear about us", "source"),
            ("Referral Source", "referral_source"),
            ("Referred By", "referred_by"),
            # Misc
            ("Additional Information", "additional_info"),
            ("Skills", "skills"),
            ("Languages", "languages"),
            ("Certifications", "certifications"),
        ],
    )
    def test_pattern_matches(self, label: str, expected_key: str) -> None:
        for pattern, key in FIELD_PATTERNS.items():
            if pattern.search(label):
                assert key == expected_key, (
                    f"Label '{label}' matched pattern '{pattern.pattern}' -> '{key}', "
                    f"expected '{expected_key}'"
                )
                return
        pytest.fail(f"No pattern matched label '{label}' (expected '{expected_key}')")

    def test_state_does_not_match_statement(self) -> None:
        """The 'state' pattern should NOT match 'statement'."""
        mapper = FieldMapper()
        result = mapper._tier1_regex(["statement"])
        assert result != "state"

    def test_no_false_positive_on_unrelated_text(self) -> None:
        """Random text should not match any pattern."""
        mapper = FieldMapper()
        result = mapper._tier1_regex(["xyz_random_field_123"])
        assert result is None


class TestPIIBlocking:
    """PII fields (SSN, etc.) should be blocked from auto-fill."""

    @pytest.mark.parametrize("label", ["Social Security Number", "SSN", "Social Security"])
    def test_pii_patterns_detected(self, label: str) -> None:
        mapper = FieldMapper()
        result = mapper._tier1_regex([label])
        assert result is not None
        assert result.startswith("__pii_")


# ---------------------------------------------------------------------------
# FieldMapper integration tests
# ---------------------------------------------------------------------------


class TestFieldMapperTier1:
    @pytest.mark.asyncio
    async def test_maps_first_name(self) -> None:
        mapper = FieldMapper()
        field = _make_field("First Name")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        assert len(results) == 1
        m = results[0]
        assert m.semantic_key == "first_name"
        assert m.value == "Jane"
        assert m.confidence == 0.95
        assert m.source_tier == "tier1_regex"

    @pytest.mark.asyncio
    async def test_maps_email(self) -> None:
        mapper = FieldMapper()
        field = _make_field("Email Address")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        assert results[0].semantic_key == "email"
        assert results[0].value == "jane@example.com"

    @pytest.mark.asyncio
    async def test_maps_via_name_attr_fallback(self) -> None:
        """If label doesn't match, name_attr should be tried."""
        mapper = FieldMapper()
        field = _make_field("unknown_label_xyz", name_attr="first_name")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        assert results[0].semantic_key == "first_name"
        assert results[0].value == "Jane"

    @pytest.mark.asyncio
    async def test_maps_via_placeholder_fallback(self) -> None:
        mapper = FieldMapper()
        field = _make_field("", placeholder="Enter your email address")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        assert results[0].semantic_key == "email"

    @pytest.mark.asyncio
    async def test_missing_profile_value_returns_empty(self) -> None:
        mapper = FieldMapper()
        field = _make_field("GPA")
        sparse_profile: dict[str, str] = {"first_name": "Jane"}
        results = await mapper.map_fields([field], sparse_profile)

        assert results[0].semantic_key == "gpa"
        assert results[0].value == ""
        assert results[0].source_tier == "tier1_regex"


class TestFieldMapperEEOC:
    @pytest.mark.asyncio
    async def test_eeoc_gender_returns_default(self) -> None:
        mapper = FieldMapper()
        field = _make_field("Gender", "select")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        m = results[0]
        assert m.semantic_key == "__eeoc_gender"
        assert m.value == EEOC_DEFAULT
        assert m.source_tier == "eeoc_default"
        assert m.confidence == 1.0

    @pytest.mark.asyncio
    async def test_eeoc_veteran_returns_default(self) -> None:
        mapper = FieldMapper()
        field = _make_field("Veteran Status", "select")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        assert results[0].value == EEOC_DEFAULT
        assert results[0].source_tier == "eeoc_default"

    @pytest.mark.asyncio
    async def test_eeoc_disability_returns_default(self) -> None:
        mapper = FieldMapper()
        field = _make_field("Disability Status", "select")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        assert results[0].value == EEOC_DEFAULT

    @pytest.mark.asyncio
    async def test_eeoc_race_returns_default(self) -> None:
        mapper = FieldMapper()
        field = _make_field("Race / Ethnicity", "select")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        assert results[0].value == EEOC_DEFAULT


class TestFieldMapperPII:
    @pytest.mark.asyncio
    async def test_pii_ssn_blocked(self) -> None:
        mapper = FieldMapper()
        field = _make_field("Social Security Number")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        m = results[0]
        assert m.source_tier == "pii_blocked"
        assert m.value == ""
        assert m.confidence == 1.0


class TestFieldMapperTier2:
    @pytest.mark.asyncio
    async def test_db_cache_hit(self) -> None:
        mapper = FieldMapper()
        mapper.load_db_cache({"custom field label": "first_name"})

        field = _make_field("Custom Field Label")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        # Tier 1 regex won't match, but tier 2 DB should
        # Note: depends on whether "Custom Field Label" matches any regex
        # Since it doesn't, tier 2 should catch it
        assert results[0].semantic_key == "first_name"
        assert results[0].source_tier == "tier2_db"
        assert results[0].confidence == 0.85

    @pytest.mark.asyncio
    async def test_db_cache_miss_returns_unmatched(self) -> None:
        mapper = FieldMapper()
        field = _make_field("xyzzy_unknown_field_42")
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        assert results[0].semantic_key is None
        assert results[0].source_tier == "unmatched"
        assert results[0].value == ""
        assert results[0].confidence == 0.0


class TestFieldMapperTier3Stub:
    @pytest.mark.asyncio
    async def test_tier3_returns_none_without_llm(self) -> None:
        mapper = FieldMapper()
        field = _make_field("Some Unknown Field")
        # Ensure it doesn't match any regex or db
        results = await mapper.map_fields([field], SAMPLE_PROFILE)

        # Should be unmatched since tier 3 is a stub
        assert results[0].source_tier == "unmatched"


class TestFieldMapperMultipleFields:
    @pytest.mark.asyncio
    async def test_maps_full_form(self) -> None:
        mapper = FieldMapper()
        fields = [
            _make_field("First Name"),
            _make_field("Last Name"),
            _make_field("Email Address"),
            _make_field("Phone Number"),
            _make_field("LinkedIn URL"),
            _make_field("Resume", "file"),
            _make_field("Gender", "select"),
            _make_field("xyzzy_unknown_42"),
        ]
        results = await mapper.map_fields(fields, SAMPLE_PROFILE)

        assert len(results) == 8

        matched = [r for r in results if r.source_tier != "unmatched"]
        unmatched = [r for r in results if r.source_tier == "unmatched"]

        assert len(matched) == 7  # All except xyzzy
        assert len(unmatched) == 1

        # Check specific values
        by_key = {r.semantic_key: r for r in results if r.semantic_key}
        assert by_key["first_name"].value == "Jane"
        assert by_key["last_name"].value == "Doe"
        assert by_key["email"].value == "jane@example.com"
        assert by_key["phone"].value == "+1-555-0100"
        assert by_key["linkedin_url"].value == "https://linkedin.com/in/janedoe"
        assert by_key["resume_file"].value == "/path/to/resume.pdf"
        assert by_key["__eeoc_gender"].value == EEOC_DEFAULT


class TestMappedFieldDataclass:
    def test_mapped_field_attributes(self) -> None:
        field = _make_field("Test")
        m = MappedField(
            field=field,
            semantic_key="first_name",
            confidence=0.95,
            source_tier="tier1_regex",
            value="Jane",
        )
        assert m.semantic_key == "first_name"
        assert m.confidence == 0.95
        assert m.value == "Jane"
        assert m.field is field
