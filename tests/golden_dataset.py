"""Golden test dataset for Phase 7A integration and regression testing.

Provides deterministic, realistic test data covering:
- 10 companies with varied states
- 5 company sources per company
- 50 jobs linked to companies
- 20 applications in various statuses
- Query templates for common intents
- Expansion rules for search testing

All IDs are generated using real id_utils functions for consistency.
"""

from datetime import datetime, timedelta, timezone

from backend.phase7a.constants import (
    ATSProvider,
    ApplicationStatus,
    ExperienceLevel,
    HealthState,
    JobType,
    QueryStrictness,
    RemoteType,
    SourceType,
    ValidationState,
)
from backend.phase7a.id_utils import (
    compute_canonical_job_id,
    compute_company_id,
    compute_raw_job_id,
    compute_source_id,
    compute_template_id,
    generate_application_id,
)

# ---------------------------------------------------------------------------
# Timestamps anchored to a fixed reference point for deterministic tests
# ---------------------------------------------------------------------------
_REF_TIME = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)


def _ts(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    """Return a deterministic timestamp offset from the reference time."""
    return _REF_TIME - timedelta(days=days_ago, hours=hours_ago)


# ---------------------------------------------------------------------------
# 1. Companies (10 total with varied states)
# ---------------------------------------------------------------------------

def get_test_companies() -> list[dict]:
    """Return 10 companies with varied validation states and ATS providers.

    Mix includes:
    - 3 Greenhouse companies (verified, stale, unverified)
    - 2 Lever companies (verified, probing)
    - 2 Ashby companies (verified, invalid)
    - 1 Workday company (unverified)
    - 1 company with no domain (name-only)
    - 1 company with domain aliases (rebrand scenario)
    """
    companies = [
        # --- Greenhouse companies ---
        {
            "company_id": compute_company_id("stripe.com"),
            "canonical_name": "Stripe",
            "domain": "stripe.com",
            "domain_aliases": None,
            "ats_provider": ATSProvider.GREENHOUSE.value,
            "ats_slug": "stripe",
            "careers_url": "https://stripe.com/jobs",
            "board_urls": ["https://boards.greenhouse.io/stripe"],
            "logo_url": "https://logo.clearbit.com/stripe.com",
            "validation_state": ValidationState.VERIFIED.value,
            "confidence_score": 95,
            "last_validated_at": _ts(days_ago=2),
            "last_probe_at": _ts(days_ago=2),
            "probe_error": None,
            "manual_override": False,
            "override_fields": None,
            "created_at": _ts(days_ago=90),
            "updated_at": _ts(days_ago=2),
        },
        {
            "company_id": compute_company_id("figma.com"),
            "canonical_name": "Figma",
            "domain": "figma.com",
            "domain_aliases": None,
            "ats_provider": ATSProvider.GREENHOUSE.value,
            "ats_slug": "figma",
            "careers_url": "https://figma.com/careers",
            "board_urls": ["https://boards.greenhouse.io/figma"],
            "logo_url": "https://logo.clearbit.com/figma.com",
            "validation_state": ValidationState.STALE.value,
            "confidence_score": 70,
            "last_validated_at": _ts(days_ago=45),
            "last_probe_at": _ts(days_ago=45),
            "probe_error": None,
            "manual_override": False,
            "override_fields": None,
            "created_at": _ts(days_ago=120),
            "updated_at": _ts(days_ago=45),
        },
        {
            "company_id": compute_company_id("openai.com"),
            "canonical_name": "OpenAI",
            "domain": "openai.com",
            "domain_aliases": None,
            "ats_provider": ATSProvider.GREENHOUSE.value,
            "ats_slug": "openai",
            "careers_url": "https://openai.com/careers",
            "board_urls": ["https://boards.greenhouse.io/openai"],
            "logo_url": "https://logo.clearbit.com/openai.com",
            "validation_state": ValidationState.UNVERIFIED.value,
            "confidence_score": 40,
            "last_validated_at": None,
            "last_probe_at": None,
            "probe_error": None,
            "manual_override": False,
            "override_fields": None,
            "created_at": _ts(days_ago=10),
            "updated_at": _ts(days_ago=10),
        },
        # --- Lever companies ---
        {
            "company_id": compute_company_id("notion.so"),
            "canonical_name": "Notion",
            "domain": "notion.so",
            "domain_aliases": None,
            "ats_provider": ATSProvider.LEVER.value,
            "ats_slug": "notion",
            "careers_url": "https://notion.so/careers",
            "board_urls": ["https://jobs.lever.co/notion"],
            "logo_url": "https://logo.clearbit.com/notion.so",
            "validation_state": ValidationState.VERIFIED.value,
            "confidence_score": 90,
            "last_validated_at": _ts(days_ago=5),
            "last_probe_at": _ts(days_ago=5),
            "probe_error": None,
            "manual_override": False,
            "override_fields": None,
            "created_at": _ts(days_ago=60),
            "updated_at": _ts(days_ago=5),
        },
        {
            "company_id": compute_company_id("vercel.com"),
            "canonical_name": "Vercel",
            "domain": "vercel.com",
            "domain_aliases": ["zeit.co"],
            "ats_provider": ATSProvider.LEVER.value,
            "ats_slug": "vercel",
            "careers_url": "https://vercel.com/careers",
            "board_urls": ["https://jobs.lever.co/vercel"],
            "logo_url": "https://logo.clearbit.com/vercel.com",
            "validation_state": ValidationState.PROBING.value,
            "confidence_score": 55,
            "last_validated_at": None,
            "last_probe_at": _ts(hours_ago=1),
            "probe_error": None,
            "manual_override": False,
            "override_fields": None,
            "created_at": _ts(days_ago=30),
            "updated_at": _ts(hours_ago=1),
        },
        # --- Ashby companies ---
        {
            "company_id": compute_company_id("anthropic.com"),
            "canonical_name": "Anthropic",
            "domain": "anthropic.com",
            "domain_aliases": None,
            "ats_provider": ATSProvider.ASHBY.value,
            "ats_slug": "anthropic",
            "careers_url": "https://anthropic.com/careers",
            "board_urls": ["https://jobs.ashbyhq.com/anthropic"],
            "logo_url": "https://logo.clearbit.com/anthropic.com",
            "validation_state": ValidationState.VERIFIED.value,
            "confidence_score": 85,
            "last_validated_at": _ts(days_ago=3),
            "last_probe_at": _ts(days_ago=3),
            "probe_error": None,
            "manual_override": True,
            "override_fields": ["canonical_name", "ats_provider"],
            "created_at": _ts(days_ago=80),
            "updated_at": _ts(days_ago=3),
        },
        {
            "company_id": compute_company_id("databricks.com"),
            "canonical_name": "Databricks",
            "domain": "databricks.com",
            "domain_aliases": None,
            "ats_provider": ATSProvider.ASHBY.value,
            "ats_slug": "databricks",
            "careers_url": "https://databricks.com/careers",
            "board_urls": ["https://jobs.ashbyhq.com/databricks"],
            "logo_url": None,
            "validation_state": ValidationState.INVALID.value,
            "confidence_score": 15,
            "last_validated_at": _ts(days_ago=60),
            "last_probe_at": _ts(days_ago=7),
            "probe_error": "404 Not Found - Board no longer exists",
            "manual_override": False,
            "override_fields": None,
            "created_at": _ts(days_ago=100),
            "updated_at": _ts(days_ago=7),
        },
        # --- Workday company (unverified) ---
        {
            "company_id": compute_company_id("amazon.com"),
            "canonical_name": "Amazon",
            "domain": "amazon.com",
            "domain_aliases": ["aws.amazon.com"],
            "ats_provider": ATSProvider.WORKDAY.value,
            "ats_slug": None,
            "careers_url": "https://amazon.jobs",
            "board_urls": None,
            "logo_url": "https://logo.clearbit.com/amazon.com",
            "validation_state": ValidationState.UNVERIFIED.value,
            "confidence_score": 30,
            "last_validated_at": None,
            "last_probe_at": None,
            "probe_error": None,
            "manual_override": False,
            "override_fields": None,
            "created_at": _ts(days_ago=15),
            "updated_at": _ts(days_ago=15),
        },
        # --- Name-only company (no domain) ---
        {
            "company_id": compute_company_id("Acme Corp"),
            "canonical_name": "Acme Corp",
            "domain": None,
            "domain_aliases": None,
            "ats_provider": ATSProvider.UNKNOWN.value,
            "ats_slug": None,
            "careers_url": None,
            "board_urls": None,
            "logo_url": None,
            "validation_state": ValidationState.UNVERIFIED.value,
            "confidence_score": 0,
            "last_validated_at": None,
            "last_probe_at": None,
            "probe_error": None,
            "manual_override": False,
            "override_fields": None,
            "created_at": _ts(days_ago=5),
            "updated_at": _ts(days_ago=5),
        },
        # --- Rebrand scenario ---
        {
            "company_id": compute_company_id("newbrand.com"),
            "canonical_name": "NewBrand",
            "domain": "newbrand.com",
            "domain_aliases": ["oldbrand.com", "legacy-brand.io"],
            "ats_provider": ATSProvider.GREENHOUSE.value,
            "ats_slug": "newbrand",
            "careers_url": "https://newbrand.com/careers",
            "board_urls": ["https://boards.greenhouse.io/newbrand"],
            "logo_url": None,
            "validation_state": ValidationState.VERIFIED.value,
            "confidence_score": 75,
            "last_validated_at": _ts(days_ago=10),
            "last_probe_at": _ts(days_ago=10),
            "probe_error": None,
            "manual_override": True,
            "override_fields": ["domain", "domain_aliases"],
            "created_at": _ts(days_ago=200),
            "updated_at": _ts(days_ago=10),
        },
    ]
    return companies


# ---------------------------------------------------------------------------
# 2. Company Sources (50 total: 5 per company)
# ---------------------------------------------------------------------------

def get_test_company_sources() -> list[dict]:
    """Return 50 company source records (5 per company).

    Mix of greenhouse, lever, ashby, serpapi, and jobspy sources.
    """
    companies = get_test_companies()
    sources = []
    source_id_counter = 1

    for company in companies:
        cid = company["company_id"]
        cname = company["canonical_name"].lower()
        # Each company gets 5 source entries from different platforms
        source_defs = [
            {
                "source": SourceType.GREENHOUSE.value,
                "source_identifier": f"gh-{cname}",
                "source_url": f"https://boards-api.greenhouse.io/v1/boards/{cname}/jobs",
                "jobs_count": 15,
            },
            {
                "source": SourceType.LEVER.value,
                "source_identifier": f"lv-{cname}",
                "source_url": f"https://api.lever.co/v0/postings/{cname}",
                "jobs_count": 8,
            },
            {
                "source": SourceType.ASHBY.value,
                "source_identifier": f"ab-{cname}",
                "source_url": f"https://api.ashbyhq.com/posting-api/job-board/{cname}",
                "jobs_count": 5,
            },
            {
                "source": SourceType.SERPAPI.value,
                "source_identifier": f"serp-{cname}",
                "source_url": f"https://serpapi.com/search?engine=google_jobs&q={cname}",
                "jobs_count": 25,
            },
            {
                "source": SourceType.JOBSPY.value,
                "source_identifier": f"spy-{cname}",
                "source_url": None,
                "jobs_count": 12,
            },
        ]
        for sdef in source_defs:
            sources.append({
                "id": source_id_counter,
                "company_id": cid,
                "source": sdef["source"],
                "source_identifier": sdef["source_identifier"],
                "source_url": sdef["source_url"],
                "jobs_count": sdef["jobs_count"],
                "last_seen_at": _ts(days_ago=1),
                "first_seen_at": _ts(days_ago=60),
            })
            source_id_counter += 1

    return sources


# ---------------------------------------------------------------------------
# 3. Jobs (50 total, linked to companies, varied states)
# ---------------------------------------------------------------------------

_JOB_DEFINITIONS = [
    # Stripe jobs (5)
    {"company": "stripe.com", "title": "Senior ML Engineer", "location": "San Francisco, CA", "source": "greenhouse", "status": "new", "experience": "senior", "remote": "hybrid", "salary_min": 180000, "salary_max": 250000, "enriched": True},
    {"company": "stripe.com", "title": "Backend Engineer", "location": "Remote", "source": "greenhouse", "status": "saved", "experience": "mid", "remote": "remote", "salary_min": 150000, "salary_max": 200000, "enriched": True},
    {"company": "stripe.com", "title": "Data Scientist", "location": "New York, NY", "source": "serpapi", "status": "applied", "experience": "mid", "remote": "hybrid", "salary_min": 140000, "salary_max": 190000, "enriched": True},
    {"company": "stripe.com", "title": "Frontend Engineer", "location": "San Francisco, CA", "source": "lever", "status": "new", "experience": "entry", "remote": "onsite", "salary_min": 120000, "salary_max": 170000, "enriched": False},
    {"company": "stripe.com", "title": "Staff Platform Engineer", "location": "Remote", "source": "jobspy", "status": "new", "experience": "senior", "remote": "remote", "salary_min": 200000, "salary_max": 300000, "enriched": True},
    # Figma jobs (5)
    {"company": "figma.com", "title": "Product Designer", "location": "San Francisco, CA", "source": "greenhouse", "status": "new", "experience": "mid", "remote": "hybrid", "salary_min": 130000, "salary_max": 180000, "enriched": True},
    {"company": "figma.com", "title": "Senior Frontend Engineer", "location": "New York, NY", "source": "greenhouse", "status": "interviewing", "experience": "senior", "remote": "hybrid", "salary_min": 170000, "salary_max": 230000, "enriched": True},
    {"company": "figma.com", "title": "ML Engineer", "location": "Remote", "source": "serpapi", "status": "new", "experience": "mid", "remote": "remote", "salary_min": 160000, "salary_max": 210000, "enriched": False},
    {"company": "figma.com", "title": "Backend Engineer", "location": "San Francisco, CA", "source": "lever", "status": "rejected", "experience": "mid", "remote": "onsite", "salary_min": 150000, "salary_max": 200000, "enriched": True},
    {"company": "figma.com", "title": "Data Analyst", "location": "Remote", "source": "jobspy", "status": "new", "experience": "entry", "remote": "remote", "salary_min": 90000, "salary_max": 130000, "enriched": True},
    # OpenAI jobs (5)
    {"company": "openai.com", "title": "Research Scientist", "location": "San Francisco, CA", "source": "greenhouse", "status": "saved", "experience": "senior", "remote": "onsite", "salary_min": 250000, "salary_max": 400000, "enriched": True},
    {"company": "openai.com", "title": "ML Engineer", "location": "San Francisco, CA", "source": "greenhouse", "status": "new", "experience": "mid", "remote": "hybrid", "salary_min": 200000, "salary_max": 300000, "enriched": True},
    {"company": "openai.com", "title": "AI Safety Researcher", "location": "Remote", "source": "serpapi", "status": "new", "experience": "senior", "remote": "remote", "salary_min": 220000, "salary_max": 350000, "enriched": False},
    {"company": "openai.com", "title": "DevOps Engineer", "location": "San Francisco, CA", "source": "jobspy", "status": "new", "experience": "mid", "remote": "onsite", "salary_min": 160000, "salary_max": 220000, "enriched": True},
    {"company": "openai.com", "title": "Technical Writer", "location": "Remote", "source": "serpapi", "status": "ghosted", "experience": "mid", "remote": "remote", "salary_min": 100000, "salary_max": 150000, "enriched": True},
    # Notion jobs (5)
    {"company": "notion.so", "title": "Senior Backend Engineer", "location": "San Francisco, CA", "source": "lever", "status": "new", "experience": "senior", "remote": "hybrid", "salary_min": 180000, "salary_max": 250000, "enriched": True},
    {"company": "notion.so", "title": "Frontend Engineer", "location": "New York, NY", "source": "lever", "status": "applied", "experience": "mid", "remote": "hybrid", "salary_min": 150000, "salary_max": 200000, "enriched": True},
    {"company": "notion.so", "title": "Data Scientist", "location": "Remote", "source": "serpapi", "status": "new", "experience": "mid", "remote": "remote", "salary_min": 160000, "salary_max": 210000, "enriched": False},
    {"company": "notion.so", "title": "Product Manager", "location": "San Francisco, CA", "source": "lever", "status": "new", "experience": "senior", "remote": "onsite", "salary_min": 170000, "salary_max": 240000, "enriched": True},
    {"company": "notion.so", "title": "Junior Engineer", "location": "Remote", "source": "jobspy", "status": "new", "experience": "entry", "remote": "remote", "salary_min": 100000, "salary_max": 140000, "enriched": True},
    # Vercel jobs (5)
    {"company": "vercel.com", "title": "Senior Frontend Engineer", "location": "Remote", "source": "lever", "status": "new", "experience": "senior", "remote": "remote", "salary_min": 180000, "salary_max": 240000, "enriched": True},
    {"company": "vercel.com", "title": "Backend Engineer", "location": "San Francisco, CA", "source": "lever", "status": "saved", "experience": "mid", "remote": "hybrid", "salary_min": 160000, "salary_max": 210000, "enriched": True},
    {"company": "vercel.com", "title": "DevOps Engineer", "location": "Remote", "source": "serpapi", "status": "new", "experience": "mid", "remote": "remote", "salary_min": 150000, "salary_max": 200000, "enriched": False},
    {"company": "vercel.com", "title": "Technical Lead", "location": "New York, NY", "source": "lever", "status": "new", "experience": "senior", "remote": "hybrid", "salary_min": 200000, "salary_max": 280000, "enriched": True},
    {"company": "vercel.com", "title": "Data Engineer", "location": "Remote", "source": "jobspy", "status": "new", "experience": "mid", "remote": "remote", "salary_min": 140000, "salary_max": 190000, "enriched": True},
    # Anthropic jobs (5)
    {"company": "anthropic.com", "title": "Research Scientist", "location": "San Francisco, CA", "source": "ashby", "status": "applied", "experience": "senior", "remote": "hybrid", "salary_min": 250000, "salary_max": 380000, "enriched": True},
    {"company": "anthropic.com", "title": "ML Engineer", "location": "San Francisco, CA", "source": "ashby", "status": "interviewing", "experience": "mid", "remote": "hybrid", "salary_min": 200000, "salary_max": 300000, "enriched": True},
    {"company": "anthropic.com", "title": "AI Safety Researcher", "location": "Remote", "source": "serpapi", "status": "new", "experience": "senior", "remote": "remote", "salary_min": 230000, "salary_max": 350000, "enriched": True},
    {"company": "anthropic.com", "title": "Software Engineer", "location": "San Francisco, CA", "source": "ashby", "status": "new", "experience": "mid", "remote": "onsite", "salary_min": 180000, "salary_max": 260000, "enriched": False},
    {"company": "anthropic.com", "title": "Technical Program Manager", "location": "Remote", "source": "serpapi", "status": "new", "experience": "senior", "remote": "remote", "salary_min": 170000, "salary_max": 240000, "enriched": True},
    # Databricks jobs (5)
    {"company": "databricks.com", "title": "Data Engineer", "location": "San Francisco, CA", "source": "ashby", "status": "new", "experience": "mid", "remote": "hybrid", "salary_min": 160000, "salary_max": 220000, "enriched": True},
    {"company": "databricks.com", "title": "Senior ML Engineer", "location": "Remote", "source": "serpapi", "status": "saved", "experience": "senior", "remote": "remote", "salary_min": 190000, "salary_max": 270000, "enriched": True},
    {"company": "databricks.com", "title": "Backend Engineer", "location": "Amsterdam", "source": "ashby", "status": "new", "experience": "mid", "remote": "onsite", "salary_min": None, "salary_max": None, "enriched": False},
    {"company": "databricks.com", "title": "Solutions Architect", "location": "New York, NY", "source": "serpapi", "status": "new", "experience": "senior", "remote": "hybrid", "salary_min": 170000, "salary_max": 240000, "enriched": True},
    {"company": "databricks.com", "title": "Intern Software Engineer", "location": "San Francisco, CA", "source": "jobspy", "status": "new", "experience": "entry", "remote": "onsite", "salary_min": 50000, "salary_max": 70000, "enriched": True},
    # Amazon jobs (5)
    {"company": "amazon.com", "title": "SDE II", "location": "Seattle, WA", "source": "serpapi", "status": "new", "experience": "mid", "remote": "onsite", "salary_min": 150000, "salary_max": 210000, "enriched": True},
    {"company": "amazon.com", "title": "Senior Data Scientist", "location": "Remote", "source": "serpapi", "status": "applied", "experience": "senior", "remote": "remote", "salary_min": 180000, "salary_max": 260000, "enriched": True},
    {"company": "amazon.com", "title": "ML Engineer", "location": "New York, NY", "source": "jobspy", "status": "new", "experience": "mid", "remote": "hybrid", "salary_min": 170000, "salary_max": 230000, "enriched": False},
    {"company": "amazon.com", "title": "Cloud Solutions Architect", "location": "Seattle, WA", "source": "serpapi", "status": "new", "experience": "senior", "remote": "hybrid", "salary_min": 160000, "salary_max": 240000, "enriched": True},
    {"company": "amazon.com", "title": "Frontend Engineer", "location": "Remote", "source": "jobspy", "status": "new", "experience": "entry", "remote": "remote", "salary_min": 120000, "salary_max": 160000, "enriched": True},
    # Acme Corp jobs (5) - name-only company
    {"company": "Acme Corp", "title": "Software Engineer", "location": "Remote", "source": "jobspy", "status": "new", "experience": "mid", "remote": "remote", "salary_min": None, "salary_max": None, "enriched": False},
    {"company": "Acme Corp", "title": "Backend Developer", "location": "Austin, TX", "source": "serpapi", "status": "new", "experience": "mid", "remote": "onsite", "salary_min": 120000, "salary_max": 160000, "enriched": False},
    {"company": "Acme Corp", "title": "QA Engineer", "location": "Remote", "source": "jobspy", "status": "new", "experience": "entry", "remote": "remote", "salary_min": 80000, "salary_max": 110000, "enriched": False},
    {"company": "Acme Corp", "title": "DevOps Engineer", "location": "Austin, TX", "source": "serpapi", "status": "new", "experience": "mid", "remote": "hybrid", "salary_min": 130000, "salary_max": 170000, "enriched": False},
    {"company": "Acme Corp", "title": "Data Analyst", "location": "Remote", "source": "jobspy", "status": "new", "experience": "entry", "remote": "remote", "salary_min": 70000, "salary_max": 95000, "enriched": False},
    # NewBrand jobs (5) - rebrand scenario
    {"company": "newbrand.com", "title": "Senior Engineer", "location": "London", "source": "greenhouse", "status": "new", "experience": "senior", "remote": "onsite", "salary_min": None, "salary_max": None, "enriched": True},
    {"company": "newbrand.com", "title": "Product Manager", "location": "Remote", "source": "greenhouse", "status": "saved", "experience": "mid", "remote": "remote", "salary_min": 130000, "salary_max": 180000, "enriched": True},
    {"company": "newbrand.com", "title": "ML Engineer", "location": "London", "source": "serpapi", "status": "new", "experience": "mid", "remote": "hybrid", "salary_min": None, "salary_max": None, "enriched": False},
    {"company": "newbrand.com", "title": "Data Engineer", "location": "Remote", "source": "greenhouse", "status": "new", "experience": "mid", "remote": "remote", "salary_min": 140000, "salary_max": 190000, "enriched": True},
    {"company": "newbrand.com", "title": "Junior Frontend Developer", "location": "London", "source": "jobspy", "status": "new", "experience": "entry", "remote": "onsite", "salary_min": None, "salary_max": None, "enriched": False},
]


def _build_job_id(source: str, company: str, title: str) -> str:
    """Build a legacy-compatible job_id using the same pattern as BaseScraper."""
    import hashlib
    key = f"{source}:{company.lower().strip()}:{title.lower().strip()}"
    return hashlib.sha256(key.encode()).hexdigest()[:64]


def get_test_jobs() -> list[dict]:
    """Return 50 jobs with realistic data linked to test companies.

    Jobs include varied:
    - Sources (greenhouse, lever, ashby, serpapi, jobspy)
    - Statuses (new, saved, applied, interviewing, rejected, ghosted)
    - Experience levels (entry, mid, senior)
    - Remote types (remote, hybrid, onsite)
    - Enrichment states (enriched and unenriched)
    - Salary data (present and missing)
    """
    jobs = []
    for idx, jdef in enumerate(_JOB_DEFINITIONS):
        company_domain_or_name = jdef["company"]
        company_id = compute_company_id(company_domain_or_name)

        # Derive company name from company field
        company_names = {
            "stripe.com": "Stripe",
            "figma.com": "Figma",
            "openai.com": "OpenAI",
            "notion.so": "Notion",
            "vercel.com": "Vercel",
            "anthropic.com": "Anthropic",
            "databricks.com": "Databricks",
            "amazon.com": "Amazon",
            "Acme Corp": "Acme Corp",
            "newbrand.com": "NewBrand",
        }
        company_name = company_names[company_domain_or_name]
        domain = company_domain_or_name if "." in company_domain_or_name else None

        job_id = _build_job_id(jdef["source"], company_name, jdef["title"])

        # Parse location
        loc_parts = jdef["location"].split(",")
        city = loc_parts[0].strip() if loc_parts else None
        state = loc_parts[1].strip() if len(loc_parts) > 1 else None

        # Build skill/tech data for enriched jobs
        skills = None
        tech_stack = None
        summary_ai = None
        match_score = None
        if jdef["enriched"]:
            skills = ["Python", "SQL", "Machine Learning"]
            tech_stack = ["Python", "PostgreSQL", "AWS"]
            summary_ai = f"A {jdef['experience']}-level {jdef['title']} role at {company_name}."
            match_score = 60.0 + (idx % 40)  # Scores between 60-99

        posted_days_ago = 1 + (idx % 14)
        scraped_hours_ago = idx % 24

        jobs.append({
            "job_id": job_id,
            "source": jdef["source"],
            "url": f"https://example.com/jobs/{job_id[:12]}",
            "posted_at": _ts(days_ago=posted_days_ago),
            "scraped_at": _ts(hours_ago=scraped_hours_ago),
            "is_active": True,
            "duplicate_of": None,
            "company_name": company_name,
            "company_domain": domain,
            "company_logo_url": f"https://logo.clearbit.com/{domain}" if domain else None,
            "title": jdef["title"],
            "location_city": city,
            "location_state": state,
            "location_country": "US" if state else None,
            "remote_type": jdef["remote"],
            "job_type": JobType.FULL_TIME.value,
            "experience_level": jdef["experience"],
            "department": None,
            "industry": "Technology",
            "salary_min": jdef["salary_min"],
            "salary_max": jdef["salary_max"],
            "salary_currency": "USD" if jdef["salary_min"] else None,
            "salary_period": "annual" if jdef["salary_min"] else None,
            "description_raw": f"<p>Join {company_name} as a {jdef['title']}.</p>",
            "description_clean": f"Join {company_name} as a {jdef['title']}.",
            "description_markdown": f"Join **{company_name}** as a **{jdef['title']}**.",
            "skills_required": skills,
            "skills_nice_to_have": ["Docker", "Kubernetes"] if jdef["enriched"] else None,
            "tech_stack": tech_stack,
            "seniority_score": 70.0 if jdef["enriched"] else None,
            "remote_score": 80.0 if jdef["remote"] == "remote" and jdef["enriched"] else (50.0 if jdef["enriched"] else None),
            "match_score": match_score,
            "summary_ai": summary_ai,
            "red_flags": ["Requires security clearance"] if jdef["enriched"] and idx % 5 == 0 else None,
            "green_flags": ["Strong engineering culture"] if jdef["enriched"] else None,
            "is_enriched": jdef["enriched"],
            "enriched_at": _ts(hours_ago=1) if jdef["enriched"] else None,
            "status": jdef["status"],
            "notes": None,
            "applied_at": _ts(days_ago=3) if jdef["status"] in ("applied", "interviewing") else None,
            "last_updated": _ts(hours_ago=scraped_hours_ago),
            "is_starred": idx % 7 == 0,
            "tags": ["ml", "ai"] if "ML" in jdef["title"] or "AI" in jdef["title"] else None,
        })

    return jobs


# ---------------------------------------------------------------------------
# 4. Applications (20 total, varied statuses)
# ---------------------------------------------------------------------------

# Pre-generated deterministic application IDs (not UUID4) for reproducibility
_APP_IDS = [f"app{str(i).zfill(28)}" for i in range(1, 21)]


def get_test_applications() -> list[dict]:
    """Return 20 application records in various statuses.

    Covers all ApplicationStatus values with realistic data.
    Uses legacy job_ids from get_test_jobs().
    """
    jobs = get_test_jobs()
    # Pick specific jobs for applications
    applied_jobs = [j for j in jobs if j["status"] in ("applied", "saved", "interviewing", "rejected", "ghosted")]
    # Pad with more jobs if needed
    all_jobs = applied_jobs + [j for j in jobs if j not in applied_jobs]
    selected = all_jobs[:20]

    statuses = [
        ApplicationStatus.SAVED,
        ApplicationStatus.SAVED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.PHONE_SCREEN,
        ApplicationStatus.PHONE_SCREEN,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.FINAL_ROUND,
        ApplicationStatus.FINAL_ROUND,
        ApplicationStatus.OFFER,
        ApplicationStatus.ACCEPTED,
        ApplicationStatus.DECLINED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.GHOSTED,
        ApplicationStatus.GHOSTED,
        ApplicationStatus.WITHDRAWN,
    ]

    applications = []
    for idx, (job, status) in enumerate(zip(selected, statuses)):
        days_offset = 20 - idx
        applications.append({
            "application_id": _APP_IDS[idx],
            "job_id": job["job_id"],
            "canonical_job_id": None,  # Not yet available (M4 not built)
            "status": status.value,
            "applied_at": _ts(days_ago=days_offset) if status != ApplicationStatus.SAVED else None,
            "status_updated_at": _ts(days_ago=max(0, days_offset - 2)),
            "notes": f"Application #{idx + 1} notes" if idx % 3 == 0 else None,
            "resume_version": "v1.0",
            "cover_letter_used": idx % 4 == 0,
            "source_url": job["url"],
            "created_at": _ts(days_ago=days_offset),
            "updated_at": _ts(days_ago=max(0, days_offset - 2)),
        })

    return applications


# ---------------------------------------------------------------------------
# 5. Query Templates for Search Expansion (M2)
# ---------------------------------------------------------------------------

def get_test_query_templates() -> list[dict]:
    """Return query templates for common job search intents.

    Each template includes the base intent and expected expansion variants.
    """
    return [
        {
            "template_id": compute_template_id("ML Engineer"),
            "intent": "ML Engineer",
            "base_queries": ["ML Engineer", "Machine Learning Engineer"],
            "expansion_variants": [
                "Machine Learning Engineer",
                "Applied Scientist",
                "AI Engineer",
                "Deep Learning Engineer",
            ],
            "strictness": QueryStrictness.BALANCED.value,
        },
        {
            "template_id": compute_template_id("Backend Engineer"),
            "intent": "Backend Engineer",
            "base_queries": ["Backend Engineer", "Backend Developer"],
            "expansion_variants": [
                "Backend Developer",
                "Server Engineer",
                "API Engineer",
                "Platform Engineer",
            ],
            "strictness": QueryStrictness.BALANCED.value,
        },
        {
            "template_id": compute_template_id("Data Scientist"),
            "intent": "Data Scientist",
            "base_queries": ["Data Scientist"],
            "expansion_variants": [
                "Data Analyst",
                "Applied Scientist",
                "Research Scientist",
                "Quantitative Analyst",
            ],
            "strictness": QueryStrictness.BROAD.value,
        },
        {
            "template_id": compute_template_id("Frontend Engineer"),
            "intent": "Frontend Engineer",
            "base_queries": ["Frontend Engineer", "Front-End Engineer"],
            "expansion_variants": [
                "Frontend Developer",
                "UI Engineer",
                "Web Developer",
                "React Developer",
            ],
            "strictness": QueryStrictness.BALANCED.value,
        },
        {
            "template_id": compute_template_id("DevOps Engineer"),
            "intent": "DevOps Engineer",
            "base_queries": ["DevOps Engineer"],
            "expansion_variants": [
                "Site Reliability Engineer",
                "SRE",
                "Infrastructure Engineer",
                "Platform Engineer",
                "Cloud Engineer",
            ],
            "strictness": QueryStrictness.BROAD.value,
        },
    ]


# ---------------------------------------------------------------------------
# 6. Expansion Rules for Search Testing (M2)
# ---------------------------------------------------------------------------

def get_test_expansion_rules() -> list[dict]:
    """Return deterministic expansion rules for regression testing.

    These are rule-based (not LLM/embedding) per Phase 7A locked decisions.
    """
    return [
        {
            "rule_id": "synonym_ml",
            "pattern": "ML Engineer",
            "expansions": ["Machine Learning Engineer", "Applied ML Engineer"],
            "bidirectional": True,
        },
        {
            "rule_id": "synonym_fe",
            "pattern": "Frontend Engineer",
            "expansions": ["Front-End Engineer", "Frontend Developer", "UI Engineer"],
            "bidirectional": True,
        },
        {
            "rule_id": "synonym_be",
            "pattern": "Backend Engineer",
            "expansions": ["Backend Developer", "Server-Side Engineer"],
            "bidirectional": True,
        },
        {
            "rule_id": "synonym_sre",
            "pattern": "SRE",
            "expansions": ["Site Reliability Engineer", "Infrastructure Engineer"],
            "bidirectional": True,
        },
        {
            "rule_id": "seniority_strip",
            "pattern": "Senior {role}",
            "expansions": ["{role}", "Staff {role}", "Lead {role}"],
            "bidirectional": False,
        },
        {
            "rule_id": "abbreviation_ds",
            "pattern": "Data Scientist",
            "expansions": ["Data Science Engineer", "Applied Scientist"],
            "bidirectional": True,
        },
    ]


# ---------------------------------------------------------------------------
# 7. Merge Scenarios for Canonical Jobs Testing (M4)
# ---------------------------------------------------------------------------

def get_test_merge_scenarios() -> list[dict]:
    """Return merge test scenarios for canonical job deduplication.

    Each scenario describes raw sources and expected canonical outcome.
    """
    stripe_id = compute_company_id("stripe.com")
    return [
        {
            "description": "Same job, different titles - Greenhouse wins",
            "company_id": stripe_id,
            "raw_sources": [
                {"source": "greenhouse", "title": "Senior Machine Learning Engineer", "location": "San Francisco, CA"},
                {"source": "serpapi", "title": "Sr. ML Engineer", "location": "San Francisco, CA, US"},
            ],
            "expected_canonical_title": "Senior Machine Learning Engineer",
            "expected_source_count": 2,
        },
        {
            "description": "Same job, different locations - normalize to same",
            "company_id": stripe_id,
            "raw_sources": [
                {"source": "greenhouse", "title": "Backend Engineer", "location": "Remote - US"},
                {"source": "lever", "title": "Backend Engineer", "location": "Remote"},
            ],
            "expected_canonical_title": "Backend Engineer",
            "expected_source_count": 2,
        },
        {
            "description": "Different jobs, same company - no merge",
            "company_id": stripe_id,
            "raw_sources": [
                {"source": "greenhouse", "title": "ML Engineer", "location": "San Francisco, CA"},
                {"source": "greenhouse", "title": "Data Scientist", "location": "San Francisco, CA"},
            ],
            "expected_canonical_title": None,  # No merge expected
            "expected_source_count": 1,
        },
    ]


# ---------------------------------------------------------------------------
# 8. Source Health Scenarios for M3 Testing
# ---------------------------------------------------------------------------

def get_test_source_health_scenarios() -> list[dict]:
    """Return source health test scenarios for Source Cache (M3)."""
    return [
        {
            "description": "Healthy source - consistent success",
            "source_type": SourceType.GREENHOUSE.value,
            "url": "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
            "consecutive_successes": 10,
            "consecutive_failures": 0,
            "expected_state": HealthState.HEALTHY.value,
        },
        {
            "description": "Degraded source - 3 failures",
            "source_type": SourceType.LEVER.value,
            "url": "https://api.lever.co/v0/postings/defunct-company",
            "consecutive_successes": 0,
            "consecutive_failures": 3,
            "expected_state": HealthState.DEGRADED.value,
        },
        {
            "description": "Failing source - 8 failures",
            "source_type": SourceType.ASHBY.value,
            "url": "https://api.ashbyhq.com/posting-api/job-board/broken",
            "consecutive_successes": 0,
            "consecutive_failures": 8,
            "expected_state": HealthState.FAILING.value,
        },
        {
            "description": "Dead source - 18+ failures",
            "source_type": SourceType.SERPAPI.value,
            "url": "https://serpapi.com/search?dead=true",
            "consecutive_successes": 0,
            "consecutive_failures": 20,
            "expected_state": HealthState.DEAD.value,
        },
    ]


# ---------------------------------------------------------------------------
# Convenience: All data in one call
# ---------------------------------------------------------------------------

def get_full_golden_dataset() -> dict:
    """Return the complete golden dataset as a dictionary.

    Keys:
        companies, company_sources, jobs, applications,
        query_templates, expansion_rules, merge_scenarios,
        source_health_scenarios
    """
    return {
        "companies": get_test_companies(),
        "company_sources": get_test_company_sources(),
        "jobs": get_test_jobs(),
        "applications": get_test_applications(),
        "query_templates": get_test_query_templates(),
        "expansion_rules": get_test_expansion_rules(),
        "merge_scenarios": get_test_merge_scenarios(),
        "source_health_scenarios": get_test_source_health_scenarios(),
    }
