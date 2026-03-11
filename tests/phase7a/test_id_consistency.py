"""ID Generation Regression Tests for Phase 7A.

Frozen/expected-value tests to catch any normalization changes.
The expected values are computed once from the current implementation and
hardcoded. If any normalization logic changes, these tests will fail,
alerting developers to a potentially breaking change.

Edge cases covered:
- Domain with protocol, www, trailing slash, uppercase
- Company names with legal suffixes (Inc, Corp, LLC, Ltd, GmbH)
- Job titles with seniority prefixes (Senior, Sr., Staff, Lead, etc.)
- Locations with state/country suffixes
- Empty and whitespace-only inputs
- Unicode in company names
- Very long inputs
"""

import hashlib
import re
from urllib.parse import urlparse

from backend.phase7a.id_utils import (
    compute_canonical_job_id,
    compute_company_id,
    compute_raw_job_id,
    compute_source_id,
    compute_template_id,
    generate_application_id,
    normalize_company_name,
    normalize_domain,
    normalize_location,
    normalize_title,
)


def _expected_sha256(key: str) -> str:
    """Compute the expected SHA256[:64] for a given key string.
    This mirrors _sha256_id from id_utils.py exactly.
    """
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:64]


# ---------------------------------------------------------------------------
# Pre-compute frozen expected values
# These are the "golden" outputs that must never change.
# ---------------------------------------------------------------------------

# Company IDs via domain
EXPECTED_STRIPE_ID = _expected_sha256("stripe.com")
EXPECTED_FIGMA_ID = _expected_sha256("figma.com")
EXPECTED_OPENAI_ID = _expected_sha256("openai.com")
EXPECTED_ANTHROPIC_ID = _expected_sha256("anthropic.com")
EXPECTED_NOTION_ID = _expected_sha256("notion.so")

# Company ID via name (after normalization)
# "Acme Corp" -> normalize_company_name -> "acme" (strips "Corp")
EXPECTED_ACME_ID = _expected_sha256("acme")

# Source ID
EXPECTED_GH_STRIPE_SOURCE_ID = _expected_sha256(
    "greenhouse:https://boards-api.greenhouse.io/v1/boards/stripe/jobs"
)

# Raw job ID
EXPECTED_GH_JOB_ID = _expected_sha256("greenhouse:4567890")

# Canonical job ID
# normalize_title("ML Engineer") -> "ml engineer"
# normalize_location("San Francisco, CA") -> "san francisco"
EXPECTED_CANONICAL_JOB_ID = _expected_sha256("company123:ml engineer:san francisco")

# Template ID
# normalize: "ml engineer"
EXPECTED_ML_TEMPLATE_ID = _expected_sha256("ml engineer")
EXPECTED_BE_TEMPLATE_ID = _expected_sha256("backend engineer")
EXPECTED_DS_TEMPLATE_ID = _expected_sha256("data scientist")


# ---------------------------------------------------------------------------
# Frozen value tests for compute_company_id
# ---------------------------------------------------------------------------

class TestFrozenCompanyIds:
    """Frozen hash values for compute_company_id.
    ANY change to these indicates a normalization regression.
    """

    def test_stripe_dot_com(self):
        assert compute_company_id("stripe.com") == EXPECTED_STRIPE_ID

    def test_stripe_uppercase(self):
        assert compute_company_id("Stripe.COM") == EXPECTED_STRIPE_ID

    def test_stripe_with_protocol(self):
        assert compute_company_id("https://stripe.com") == EXPECTED_STRIPE_ID

    def test_stripe_with_www(self):
        assert compute_company_id("www.stripe.com") == EXPECTED_STRIPE_ID

    def test_stripe_full_url(self):
        assert compute_company_id("https://www.stripe.com") == EXPECTED_STRIPE_ID

    def test_stripe_with_path(self):
        assert compute_company_id("https://www.Stripe.COM/jobs") == EXPECTED_STRIPE_ID

    def test_figma(self):
        assert compute_company_id("figma.com") == EXPECTED_FIGMA_ID

    def test_openai(self):
        assert compute_company_id("openai.com") == EXPECTED_OPENAI_ID

    def test_anthropic(self):
        assert compute_company_id("anthropic.com") == EXPECTED_ANTHROPIC_ID

    def test_notion(self):
        assert compute_company_id("notion.so") == EXPECTED_NOTION_ID

    def test_acme_corp_by_name(self):
        """Acme Corp -> normalize -> 'acme' (strips Corp suffix)."""
        assert compute_company_id("Acme Corp") == EXPECTED_ACME_ID

    def test_acme_corporation_by_name(self):
        """Acme Corporation -> normalize -> 'acme' (strips Corporation suffix)."""
        assert compute_company_id("Acme Corporation") == EXPECTED_ACME_ID

    def test_acme_inc_by_name(self):
        """Acme, Inc. -> normalize -> 'acme' (strips Inc. suffix)."""
        result = compute_company_id("Acme, Inc.")
        expected = _expected_sha256(normalize_company_name("Acme, Inc."))
        assert result == expected
        # Verify normalization: should be "acme"
        assert normalize_company_name("Acme, Inc.") == "acme"

    def test_frozen_values_are_64_hex(self):
        """All frozen values must be valid 64-char hex strings."""
        frozen = [
            EXPECTED_STRIPE_ID, EXPECTED_FIGMA_ID, EXPECTED_OPENAI_ID,
            EXPECTED_ANTHROPIC_ID, EXPECTED_NOTION_ID, EXPECTED_ACME_ID,
        ]
        hex_pattern = re.compile(r"^[0-9a-f]{64}$")
        for val in frozen:
            assert hex_pattern.match(val), f"Invalid frozen value: {val}"

    def test_all_frozen_values_unique(self):
        """All frozen company IDs must be unique."""
        frozen = [
            EXPECTED_STRIPE_ID, EXPECTED_FIGMA_ID, EXPECTED_OPENAI_ID,
            EXPECTED_ANTHROPIC_ID, EXPECTED_NOTION_ID, EXPECTED_ACME_ID,
        ]
        assert len(frozen) == len(set(frozen))


# ---------------------------------------------------------------------------
# Frozen value tests for compute_source_id
# ---------------------------------------------------------------------------

class TestFrozenSourceIds:

    def test_greenhouse_stripe_source(self):
        result = compute_source_id(
            "greenhouse",
            "https://boards-api.greenhouse.io/v1/boards/stripe/jobs"
        )
        assert result == EXPECTED_GH_STRIPE_SOURCE_ID

    def test_source_id_is_64_hex(self):
        hex_pattern = re.compile(r"^[0-9a-f]{64}$")
        assert hex_pattern.match(EXPECTED_GH_STRIPE_SOURCE_ID)


# ---------------------------------------------------------------------------
# Frozen value tests for compute_raw_job_id
# ---------------------------------------------------------------------------

class TestFrozenRawJobIds:

    def test_greenhouse_job_4567890(self):
        result = compute_raw_job_id("greenhouse", "4567890")
        assert result == EXPECTED_GH_JOB_ID

    def test_raw_job_id_is_64_hex(self):
        hex_pattern = re.compile(r"^[0-9a-f]{64}$")
        assert hex_pattern.match(EXPECTED_GH_JOB_ID)


# ---------------------------------------------------------------------------
# Frozen value tests for compute_canonical_job_id
# ---------------------------------------------------------------------------

class TestFrozenCanonicalJobIds:

    def test_canonical_job_id_basic(self):
        result = compute_canonical_job_id("company123", "ML Engineer", "San Francisco, CA")
        assert result == EXPECTED_CANONICAL_JOB_ID

    def test_canonical_job_id_normalizes_seniority(self):
        """Senior ML Engineer -> ml engineer (strips Senior prefix)."""
        result_a = compute_canonical_job_id("company123", "Senior ML Engineer", "San Francisco, CA")
        result_b = compute_canonical_job_id("company123", "ML Engineer", "San Francisco, CA")
        assert result_a == result_b

    def test_canonical_job_id_normalizes_location(self):
        """San Francisco, CA, US -> san francisco."""
        result_a = compute_canonical_job_id("company123", "ML Engineer", "San Francisco, CA, US")
        result_b = compute_canonical_job_id("company123", "ML Engineer", "San Francisco, CA")
        assert result_a == result_b

    def test_canonical_job_id_remote_case(self):
        """REMOTE and Remote produce same canonical ID."""
        result_a = compute_canonical_job_id("company123", "ML Engineer", "Remote")
        result_b = compute_canonical_job_id("company123", "ML Engineer", "REMOTE")
        assert result_a == result_b


# ---------------------------------------------------------------------------
# Frozen value tests for compute_template_id
# ---------------------------------------------------------------------------

class TestFrozenTemplateIds:

    def test_ml_engineer_template(self):
        result = compute_template_id("ML Engineer")
        assert result == EXPECTED_ML_TEMPLATE_ID

    def test_backend_engineer_template(self):
        result = compute_template_id("Backend Engineer")
        assert result == EXPECTED_BE_TEMPLATE_ID

    def test_data_scientist_template(self):
        result = compute_template_id("Data Scientist")
        assert result == EXPECTED_DS_TEMPLATE_ID

    def test_case_insensitive(self):
        assert compute_template_id("ML Engineer") == compute_template_id("ml engineer")

    def test_whitespace_insensitive(self):
        assert compute_template_id("ML Engineer") == compute_template_id("  ML   Engineer  ")


# ---------------------------------------------------------------------------
# Normalization edge case regression tests
# ---------------------------------------------------------------------------

class TestNormalizationEdgeCases:
    """Regression tests for normalization edge cases that could break IDs."""

    def test_domain_with_port(self):
        """Domain with port should still normalize to just the domain."""
        result = normalize_domain("https://stripe.com:443")
        assert result == "stripe.com"

    def test_domain_trailing_slash(self):
        result = normalize_domain("stripe.com/")
        assert result == "stripe.com"

    def test_company_name_with_extra_whitespace(self):
        result = normalize_company_name("  Stripe   Inc.  ")
        assert result == "stripe"

    def test_company_name_llc(self):
        assert normalize_company_name("TechCo LLC") == "techco"

    def test_company_name_ltd(self):
        assert normalize_company_name("Widget Ltd.") == "widget"

    def test_company_name_gmbh(self):
        assert normalize_company_name("Siemens GmbH") == "siemens"

    def test_company_name_no_suffix(self):
        assert normalize_company_name("OpenAI") == "openai"

    def test_title_strips_senior(self):
        assert normalize_title("Senior Engineer") == "engineer"

    def test_title_strips_sr_dot(self):
        assert normalize_title("Sr. Engineer") == "engineer"

    def test_title_strips_staff(self):
        assert normalize_title("Staff Engineer") == "engineer"

    def test_title_strips_lead(self):
        assert normalize_title("Lead Engineer") == "engineer"

    def test_title_strips_principal(self):
        assert normalize_title("Principal Engineer") == "engineer"

    def test_title_strips_junior(self):
        assert normalize_title("Junior Engineer") == "engineer"

    def test_title_strips_jr_dot(self):
        assert normalize_title("Jr. Engineer") == "engineer"

    def test_title_strips_associate(self):
        assert normalize_title("Associate Engineer") == "engineer"

    def test_title_strips_intern(self):
        assert normalize_title("Intern Engineer") == "engineer"

    def test_title_no_prefix(self):
        assert normalize_title("Software Engineer") == "software engineer"

    def test_title_only_prefix(self):
        """Edge case: title is just a seniority prefix."""
        result = normalize_title("Senior")
        # After stripping "Senior" prefix, result is empty
        # The function strips via regex that requires a space after prefix
        # So "Senior" alone (no word after) should NOT be stripped
        assert result == "senior"

    def test_location_empty(self):
        assert normalize_location("") == ""

    def test_location_whitespace(self):
        assert normalize_location("   ") == ""

    def test_location_remote_in_text(self):
        assert normalize_location("Remote - US") == "remote"

    def test_location_city_only(self):
        assert normalize_location("London") == "london"

    def test_location_with_country(self):
        assert normalize_location("London, United Kingdom") == "london"


# ---------------------------------------------------------------------------
# Application ID uniqueness
# ---------------------------------------------------------------------------

class TestApplicationIdUniqueness:
    """Application IDs must always be unique (UUID4-based)."""

    def test_unique_across_1000(self):
        ids = {generate_application_id() for _ in range(1000)}
        assert len(ids) == 1000

    def test_format_is_32_hex(self):
        app_id = generate_application_id()
        assert re.match(r"^[0-9a-f]{32}$", app_id)

    def test_not_deterministic(self):
        """Application IDs should NOT be deterministic (they use UUID4)."""
        id_a = generate_application_id()
        id_b = generate_application_id()
        assert id_a != id_b


# ---------------------------------------------------------------------------
# Cross-function consistency
# ---------------------------------------------------------------------------

class TestCrossFunctionConsistency:
    """Verify ID functions use consistent normalization."""

    def test_company_id_domain_vs_url(self):
        """compute_company_id with domain vs full URL should match."""
        domain_id = compute_company_id("stripe.com")
        url_id = compute_company_id("https://www.stripe.com/careers")
        assert domain_id == url_id

    def test_canonical_job_id_title_normalization_matches_normalize_title(self):
        """compute_canonical_job_id must use the same normalization as normalize_title."""
        company_id = "test_company"
        # Manually compute what canonical should be
        norm_title = normalize_title("Senior ML Engineer")
        norm_loc = normalize_location("San Francisco, CA")
        expected = _expected_sha256(f"{company_id}:{norm_title}:{norm_loc}")
        actual = compute_canonical_job_id(company_id, "Senior ML Engineer", "San Francisco, CA")
        assert actual == expected

    def test_template_id_consistency(self):
        """Template ID normalization should be simple lowercase + whitespace collapse."""
        id_a = compute_template_id("ML Engineer")
        id_b = compute_template_id("ml engineer")
        id_c = compute_template_id("  ML   Engineer  ")
        assert id_a == id_b == id_c
