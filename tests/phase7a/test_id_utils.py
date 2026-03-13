"""Tests for Phase 7A ID generation and normalization utilities."""

import re

from backend.phase7a.id_utils import (
    compute_company_id,
    compute_source_id,
    compute_raw_job_id,
    compute_canonical_job_id,
    compute_template_id,
    generate_application_id,
    normalize_title,
    normalize_location,
    normalize_domain,
    normalize_company_name,
)

HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class TestNormalizeDomain:
    def test_basic(self):
        assert normalize_domain("stripe.com") == "stripe.com"

    def test_uppercase(self):
        assert normalize_domain("Stripe.COM") == "stripe.com"

    def test_strips_www(self):
        assert normalize_domain("www.stripe.com") == "stripe.com"

    def test_strips_protocol(self):
        assert normalize_domain("https://stripe.com") == "stripe.com"

    def test_strips_protocol_and_www(self):
        assert normalize_domain("https://www.stripe.com") == "stripe.com"

    def test_strips_trailing_slash(self):
        assert normalize_domain("stripe.com/") == "stripe.com"

    def test_full_url(self):
        assert normalize_domain("https://www.Stripe.COM/jobs") == "stripe.com"

    def test_whitespace(self):
        assert normalize_domain("  stripe.com  ") == "stripe.com"


class TestNormalizeCompanyName:
    def test_basic(self):
        assert normalize_company_name("Stripe") == "stripe"

    def test_strips_inc(self):
        assert normalize_company_name("Stripe, Inc.") == "stripe"

    def test_strips_corporation(self):
        assert normalize_company_name("Acme Corporation") == "acme"

    def test_strips_llc(self):
        assert normalize_company_name("Tech LLC") == "tech"

    def test_strips_ltd(self):
        assert normalize_company_name("Widget Ltd.") == "widget"

    def test_preserves_name_without_suffix(self):
        assert normalize_company_name("OpenAI") == "openai"

    def test_collapses_whitespace(self):
        assert normalize_company_name("  Acme   Corp  ") == "acme"


class TestNormalizeTitle:
    def test_basic(self):
        assert normalize_title("Software Engineer") == "software engineer"

    def test_strips_senior(self):
        assert normalize_title("Senior Machine Learning Engineer") == "machine learning engineer"

    def test_strips_sr_dot(self):
        assert normalize_title("Sr. ML Engineer") == "ml engineer"

    def test_strips_staff(self):
        assert normalize_title("Staff Backend Developer") == "backend developer"

    def test_strips_lead(self):
        assert normalize_title("Lead Data Scientist") == "data scientist"

    def test_strips_principal(self):
        assert normalize_title("Principal Engineer") == "engineer"

    def test_strips_junior(self):
        assert normalize_title("Junior Developer") == "developer"

    def test_strips_associate(self):
        assert normalize_title("Associate Software Engineer") == "software engineer"

    def test_strips_intern(self):
        assert normalize_title("Intern Data Analyst") == "data analyst"

    def test_no_prefix(self):
        assert normalize_title("Data Scientist") == "data scientist"

    def test_collapses_whitespace(self):
        assert normalize_title("  Senior   ML   Engineer  ") == "ml engineer"


class TestNormalizeLocation:
    def test_basic_city_state(self):
        assert normalize_location("San Francisco, CA") == "san francisco"

    def test_city_state_country(self):
        assert normalize_location("San Francisco, CA, US") == "san francisco"

    def test_remote(self):
        assert normalize_location("Remote") == "remote"

    def test_remote_mixed_case(self):
        assert normalize_location("REMOTE") == "remote"

    def test_remote_in_string(self):
        assert normalize_location("Remote - US") == "remote"

    def test_city_only(self):
        assert normalize_location("London") == "london"

    def test_empty(self):
        assert normalize_location("") == ""

    def test_whitespace_only(self):
        assert normalize_location("   ") == ""

    def test_new_york(self):
        assert normalize_location("New York, NY") == "new york"


class TestComputeCompanyId:
    def test_returns_64_hex(self):
        result = compute_company_id("stripe.com")
        assert HEX_64.match(result)

    def test_deterministic(self):
        a = compute_company_id("stripe.com")
        b = compute_company_id("stripe.com")
        assert a == b

    def test_case_insensitive_domain(self):
        a = compute_company_id("stripe.com")
        b = compute_company_id("Stripe.COM")
        assert a == b

    def test_strips_www(self):
        a = compute_company_id("stripe.com")
        b = compute_company_id("www.stripe.com")
        assert a == b

    def test_strips_protocol(self):
        a = compute_company_id("stripe.com")
        b = compute_company_id("https://stripe.com")
        assert a == b

    def test_different_domains_differ(self):
        a = compute_company_id("stripe.com")
        b = compute_company_id("figma.com")
        assert a != b

    def test_name_fallback(self):
        result = compute_company_id("Acme Corp")
        assert HEX_64.match(result)

    def test_name_case_insensitive(self):
        a = compute_company_id("Stripe")
        b = compute_company_id("stripe")
        assert a == b


class TestComputeSourceId:
    def test_returns_64_hex(self):
        result = compute_source_id("greenhouse", "https://boards-api.greenhouse.io/v1/boards/stripe/jobs")
        assert HEX_64.match(result)

    def test_deterministic(self):
        url = "https://boards-api.greenhouse.io/v1/boards/stripe/jobs"
        a = compute_source_id("greenhouse", url)
        b = compute_source_id("greenhouse", url)
        assert a == b

    def test_different_types_differ(self):
        url = "https://example.com/jobs"
        a = compute_source_id("greenhouse", url)
        b = compute_source_id("lever", url)
        assert a != b

    def test_different_urls_differ(self):
        a = compute_source_id("greenhouse", "https://example.com/a")
        b = compute_source_id("greenhouse", "https://example.com/b")
        assert a != b


class TestComputeRawJobId:
    def test_returns_64_hex(self):
        result = compute_raw_job_id("greenhouse", "4567890")
        assert HEX_64.match(result)

    def test_deterministic(self):
        a = compute_raw_job_id("greenhouse", "4567890")
        b = compute_raw_job_id("greenhouse", "4567890")
        assert a == b

    def test_different_sources_differ(self):
        a = compute_raw_job_id("greenhouse", "123")
        b = compute_raw_job_id("lever", "123")
        assert a != b


class TestComputeCanonicalJobId:
    def test_returns_64_hex(self):
        result = compute_canonical_job_id("company123", "ML Engineer", "San Francisco, CA")
        assert HEX_64.match(result)

    def test_deterministic(self):
        a = compute_canonical_job_id("c1", "ML Engineer", "San Francisco")
        b = compute_canonical_job_id("c1", "ML Engineer", "San Francisco")
        assert a == b

    def test_normalizes_title(self):
        a = compute_canonical_job_id("c1", "Senior ML Engineer", "SF")
        b = compute_canonical_job_id("c1", "ML Engineer", "SF")
        assert a == b, "Seniority prefix should be stripped"

    def test_normalizes_location(self):
        a = compute_canonical_job_id("c1", "Engineer", "San Francisco, CA, US")
        b = compute_canonical_job_id("c1", "Engineer", "San Francisco, CA")
        assert a == b, "Location should normalize to city only"

    def test_different_companies_differ(self):
        a = compute_canonical_job_id("company_a", "Engineer", "Remote")
        b = compute_canonical_job_id("company_b", "Engineer", "Remote")
        assert a != b

    def test_remote_normalization(self):
        a = compute_canonical_job_id("c1", "Engineer", "Remote")
        b = compute_canonical_job_id("c1", "Engineer", "REMOTE")
        assert a == b


class TestComputeTemplateId:
    def test_returns_64_hex(self):
        result = compute_template_id("ML Engineer")
        assert HEX_64.match(result)

    def test_deterministic(self):
        a = compute_template_id("ML Engineer")
        b = compute_template_id("ML Engineer")
        assert a == b

    def test_case_insensitive(self):
        a = compute_template_id("ML Engineer")
        b = compute_template_id("ml engineer")
        assert a == b

    def test_whitespace_normalized(self):
        a = compute_template_id("ML Engineer")
        b = compute_template_id("  ML   Engineer  ")
        assert a == b

    def test_different_intents_differ(self):
        a = compute_template_id("ML Engineer")
        b = compute_template_id("Backend Engineer")
        assert a != b


class TestGenerateApplicationId:
    def test_returns_hex_string(self):
        result = generate_application_id()
        assert re.match(r"^[0-9a-f]{32}$", result)

    def test_unique(self):
        ids = {generate_application_id() for _ in range(100)}
        assert len(ids) == 100, "Application IDs should be unique"

    def test_not_64_chars(self):
        # Application IDs are UUID4 hex (32 chars), not SHA256 (64 chars)
        result = generate_application_id()
        assert len(result) == 32
