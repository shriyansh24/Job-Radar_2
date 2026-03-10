# JobRadar Phase 7A — Implementation Details Package

**Version:** 1.0 | **Date:** March 10, 2026  
**Companion to:** Phase 7A Core Architecture Package  
**Purpose:** Testing, observability, operational guidance, and implementation clarity for parallel agent development

---

## Table of Contents

1. [Cross-Module Testing Strategy](#1-cross-module-testing-strategy)
2. [Module Implementation Details](#2-module-implementation-details)
   - [2.1 Company Intelligence Registry](#21-module-1-company-intelligence-registry)
   - [2.2 Search Expansion Engine](#22-module-2-search-expansion-engine)
   - [2.3 Validated Source Cache](#23-module-3-validated-source-cache)
   - [2.4 Canonical Jobs Pipeline](#24-module-4-canonical-jobs-pipeline)
   - [2.5 Application Tracker](#25-module-5-application-tracker)
3. [Operational Runbooks](#3-operational-runbooks)
4. [Quality Gates](#4-quality-gates)
5. [Self-Assessment Scores](#5-self-assessment-scores)

---

## 1. Cross-Module Testing Strategy

### 1.1 Integration Tests Spanning Multiple Modules

| Test Suite | Modules Involved | Purpose |
|------------|------------------|---------|
| `test_company_to_source_flow` | M1 → M3 | Company creation triggers source registry entries |
| `test_source_health_affects_merge` | M3 → M4 | Source quality scores influence canonical field selection |
| `test_query_expansion_scraper_roundtrip` | M2 → M3 → M4 | Expanded queries produce jobs that merge correctly |
| `test_canonical_to_application_link` | M4 → M5 | Applications maintain stable links when canonicals update |
| `test_full_scrape_to_application` | M1 → M2 → M3 → M4 → M5 | End-to-end job discovery to user tracking |
| `test_company_rebrand_propagation` | M1 → M4 → M5 | Company rename updates canonical jobs and preserves applications |

### 1.2 End-to-End Test Scenarios

#### E2E Scenario 1: New Company Discovery
```
GIVEN: User adds "Anthropic" to company watchlist
WHEN: System probes anthropic.com careers page
THEN: 
  - Company created in registry with ATS=greenhouse
  - Source created in source_registry with health=unknown
  - First scrape populates raw_job_sources
  - Canonical jobs created with company_id link
  - Jobs visible in frontend job board
```

#### E2E Scenario 2: Multi-Source Job Merge
```
GIVEN: Same job exists on Greenhouse AND Google Jobs (via SerpApi)
WHEN: Both scrapers run within 24h window
THEN:
  - Two raw_job_sources records created
  - Single canonical_job created with source_count=2
  - Greenhouse data wins for salary (higher quality source)
  - SerpApi provides fallback for missing fields
  - Frontend shows single job with "2 sources" indicator
```

#### E2E Scenario 3: Application Survives Job Closure
```
GIVEN: User has application with status="interviewing" for job X
WHEN: Job X disappears from all sources for 14 days
THEN:
  - canonical_job.is_active = FALSE
  - canonical_job.closed_at set
  - application record unchanged
  - Application still visible in Pipeline kanban
  - Job detail shows "[Closed]" badge
```

#### E2E Scenario 4: Query Expansion Recall Test
```
GIVEN: User searches for "ML Engineer"
WHEN: Search expansion engine processes query
THEN:
  - Generates variants: ["Machine Learning Engineer", "Applied Scientist", "AI Engineer"]
  - Each source receives translated query
  - Total recall measured: >40% more unique jobs vs literal search
  - Duplicates suppressed via canonical matching
```

#### E2E Scenario 5: Source Health Recovery
```
GIVEN: Greenhouse API returns 503 for 3 consecutive checks
WHEN: Source transitions to health_state="failing"
THEN:
  - Backoff applied (2-hour wait)
  - Source excluded from priority queue
  - After recovery (200 response), health="healthy"
  - Backoff cleared, consecutive_failures=0
  - Quality score recalculated
```

### 1.3 Golden Dataset Requirements

#### Minimum Golden Dataset Contents

| Entity | Count | Requirements |
|--------|-------|--------------|
| Companies | 50 | Mix of ATS providers: 15 Greenhouse, 15 Lever, 10 Ashby, 10 unknown |
| Sources | 75 | 50 company boards + 25 aggregator endpoints |
| Raw Job Sources | 500 | Across all 7 scraper types |
| Canonical Jobs | 350 | Including 50 multi-source merges |
| Applications | 100 | All status values represented |
| Query Templates | 20 | Common role types with expansions |

#### Golden Dataset Characteristics

```python
# File: tests/fixtures/golden_dataset.py

GOLDEN_COMPANIES = [
    # Known Greenhouse companies
    {"name": "Stripe", "domain": "stripe.com", "ats_provider": "greenhouse", "ats_slug": "stripe"},
    {"name": "Figma", "domain": "figma.com", "ats_provider": "greenhouse", "ats_slug": "figma"},
    # Known Lever companies
    {"name": "Notion", "domain": "notion.so", "ats_provider": "lever", "ats_slug": "notion"},
    # Edge cases
    {"name": "Acme Corp", "domain": "acme.com", "ats_provider": "unknown"},  # No discoverable board
    {"name": "Rebrand Inc", "domain": "newbrand.com", "domain_aliases": ["oldbrand.com"]},
]

GOLDEN_MERGE_SCENARIOS = [
    {
        "description": "Same job, different titles",
        "raw_sources": [
            {"source": "greenhouse", "title": "Senior Machine Learning Engineer"},
            {"source": "serpapi", "title": "Sr. ML Engineer"},
        ],
        "expected_canonical_title": "Senior Machine Learning Engineer",  # Greenhouse wins
    },
    # ... more scenarios
]
```

### 1.4 Regression Suite Design

#### Regression Categories

1. **Schema Regression** — Ensure migrations don't break existing queries
2. **API Regression** — All endpoints return expected shapes
3. **State Machine Regression** — Status transitions follow defined rules
4. **Merge Logic Regression** — Field precedence unchanged
5. **Performance Regression** — Query times within thresholds

#### Regression Test Execution

```bash
# Run before each PR merge
make test-regression

# Regression suite structure
tests/
├── regression/
│   ├── test_schema_regression.py      # Table structure validation
│   ├── test_api_contracts.py          # OpenAPI schema compliance
│   ├── test_state_machines.py         # All state transitions
│   ├── test_merge_precedence.py       # Field merge rules
│   └── test_performance_baselines.py  # Query timing assertions
```

#### Performance Baselines

| Operation | Baseline | Threshold |
|-----------|----------|-----------|
| Company lookup by domain | 2ms | <10ms |
| Source priority queue (top 20) | 5ms | <25ms |
| Canonical job match | 3ms | <15ms |
| Application list (50 items) | 10ms | <50ms |
| Query expansion | 5ms | <20ms |

### 1.5 Test Data Seeding Strategy

#### Seeding Layers

```python
# Layer 1: Foundation (run first)
async def seed_foundation():
    """Companies, sources, expansion rules - no dependencies."""
    await seed_companies(count=50)
    await seed_sources(count=75)
    await seed_expansion_rules()

# Layer 2: Jobs (depends on foundation)
async def seed_jobs():
    """Raw and canonical jobs - requires companies and sources."""
    await seed_raw_job_sources(count=500)
    await seed_canonical_jobs(count=350)

# Layer 3: User State (depends on jobs)
async def seed_user_state():
    """Applications - requires canonical jobs."""
    await seed_applications(count=100)
    await seed_application_history()
```

#### Seed Commands

```bash
# Development seeding
make seed-dev          # Full dataset for local development
make seed-minimal      # Just enough to test basic flows
make seed-stress       # 10x data for performance testing

# Test isolation
make seed-test         # Fresh DB per test run (pytest fixture)
```

#### Factory Pattern for Tests

```python
# tests/factories.py
from factory import Factory, Faker, SubFactory

class CompanyFactory(Factory):
    class Meta:
        model = Company
    
    company_id = Faker('sha256')
    canonical_name = Faker('company')
    domain = Faker('domain_name')
    ats_provider = Faker('random_element', elements=['greenhouse', 'lever', 'ashby', 'unknown'])
    validation_state = 'verified'

class CanonicalJobFactory(Factory):
    class Meta:
        model = CanonicalJob
    
    company = SubFactory(CompanyFactory)
    title = Faker('job')
    location_city = Faker('city')
    # ...
```

---

## 2. Module Implementation Details

---

## 2.1 Module 1: Company Intelligence Registry

### 2.1.1 Edge Cases and Failure Modes

| # | Failure Scenario | Handling | Recovery Strategy | User Impact |
|---|-----------------|----------|-------------------|-------------|
| 1 | **Domain DNS failure** — Company domain doesn't resolve | Set `validation_state=invalid`, log error, continue | Re-probe after 7 days | Company shows "unverified" badge |
| 2 | **Careers page 404** — Domain works but /careers returns 404 | Try alternate paths (/jobs, /job-openings), mark as `probe_error` if all fail | Store failed paths, try new patterns weekly | ATS detection incomplete |
| 3 | **ATS pattern mismatch** — URL looks like Greenhouse but API fails | Log detection mismatch, set `confidence_score` low, mark `ats_provider=unknown` | Manual override available | Jobs may be missed until corrected |
| 4 | **Duplicate domain insertion** — Race condition creates two companies for same domain | UNIQUE constraint on `domain` column; catch IntegrityError, return existing | N/A—prevented by constraint | None |
| 5 | **Company rebrand** — stripe.com becomes stripe.dev | Support `domain_aliases` array; lookup checks all aliases | Admin merges companies via API | Brief duplicate period possible |
| 6 | **ATS provider change** — Company switches Greenhouse→Lever | Detect via probe, update `ats_provider`, invalidate old sources | Old source marked `dead`, new source created | ~6-hour gap in job updates |
| 7 | **Rate limited during probe** — Careers page returns 429 | Exponential backoff on probe, don't change validation_state | Retry with increasing delays | Delayed verification only |
| 8 | **Malformed response** — Careers page returns garbage HTML | Catch parsing errors, log raw response prefix, mark `probe_error` | Manual investigation via audit log | Company stays unverified |
| 9 | **Subsidiary confusion** — Multiple boards for AWS, Amazon, Twitch (all Amazon) | V1: Treat as separate companies; V2: Add parent_company_id | Document for V2 | Minor duplicate risk |
| 10 | **Manual override conflict** — User sets `ats_provider=lever`, probe detects greenhouse | `manual_override=true` fields NEVER updated by automation | User must clear override to re-enable auto | User-controlled |

### 2.1.2 Testing Strategy

#### Unit Tests

**What to test:**
- `compute_company_id()` determinism with same input
- `normalize_domain()` handles www, trailing slash, protocol
- `detect_ats_from_url()` pattern matching for all 7 providers
- `confidence_score` calculation from signal inputs
- State machine transitions validity

**Mocking strategy:**
- Mock `httpx.AsyncClient` for domain probing
- Mock DNS resolution for invalid domain tests
- Use in-memory SQLite for DB tests

#### Integration Tests

**Database fixtures needed:**
- 10 companies in various validation states
- 5 companies with domain aliases
- 3 companies with manual overrides

**Key integration tests:**
```python
async def test_company_creation_triggers_source_creation():
    """When company with known ATS is created, source_registry entry should exist."""
    
async def test_probe_updates_validation_state():
    """Successful probe transitions unverified → probing → verified."""
    
async def test_manual_override_survives_probe():
    """Company with manual_override=True doesn't change on probe."""
```

#### Contract Tests

- API response shapes match Pydantic schemas
- Error responses include required fields (error, message, detail)
- Pagination response includes total, page, pages

#### Red-Team Failure Cases

1. **SQL Injection via company name** — Ensure parameterized queries
2. **Extremely long domain** — Test 512+ char domains are rejected
3. **Unicode domain attacks** — IDN homograph detection (stripe.com vs strıpe.com)
4. **Concurrent probe spam** — Same company probed 100x simultaneously
5. **Invalid JSON in domain_aliases** — Malformed JSON doesn't crash

#### Example Test Function Names

```python
# tests/test_company_registry.py
def test_compute_company_id_deterministic()
def test_compute_company_id_normalized_case_insensitive()
def test_normalize_domain_strips_www_and_protocol()
def test_detect_ats_greenhouse_board_url()
def test_detect_ats_lever_jobs_url()
def test_detect_ats_returns_unknown_for_custom_ats()
def test_validation_state_transition_unverified_to_probing()
def test_validation_state_transition_probing_to_verified()
def test_validation_state_cannot_skip_probing()
def test_confidence_score_maxes_at_100()
def test_manual_override_blocks_automated_updates()
def test_bulk_import_skips_existing_domains()
def test_domain_alias_lookup_finds_company()
```

#### Test Coverage Expectations

| Category | Target |
|----------|--------|
| Unit tests | 90% line coverage |
| Integration tests | All API endpoints |
| State machine | 100% transition coverage |

### 2.1.3 Observability

#### Metrics (Prometheus-style names)

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `company_registry_total` | Gauge | - | Total companies in registry |
| `company_registry_by_state` | Gauge | `state` | Companies by validation_state |
| `company_registry_by_ats` | Gauge | `ats_provider` | Companies by ATS provider |
| `company_probe_duration_seconds` | Histogram | `result` | Probe latency distribution |
| `company_probe_total` | Counter | `result` | Probes by success/failure |
| `company_ats_detection_total` | Counter | `detected_provider` | ATS detections |
| `company_validation_transitions_total` | Counter | `from_state`, `to_state` | State changes |

#### Logs

| Level | Event | Key Fields |
|-------|-------|------------|
| INFO | Company created | `company_id`, `domain`, `source` |
| INFO | Probe completed | `company_id`, `result`, `duration_ms`, `detected_ats` |
| INFO | Validation state changed | `company_id`, `old_state`, `new_state` |
| WARN | Probe failed | `company_id`, `error`, `http_status` |
| WARN | ATS detection mismatch | `company_id`, `expected`, `detected` |
| ERROR | Database constraint violation | `operation`, `error` |

#### Alerts (Local Monitoring)

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| High probe failure rate | `probe_failures / probe_total > 0.3` | 30% in 1h window | Check network/rate limits |
| Stale companies growing | `state=stale count > 50` | 50 companies | Review probe schedule |
| ATS detection dropping | `unknown ATS > 40%` of new companies | 40% | Update detection patterns |

#### Data Quality Checks

```sql
-- Orphaned companies (no sources, no jobs)
SELECT company_id, canonical_name 
FROM companies c
WHERE NOT EXISTS (SELECT 1 FROM company_sources WHERE company_id = c.company_id)
  AND NOT EXISTS (SELECT 1 FROM canonical_jobs WHERE company_id = c.company_id)
  AND created_at < datetime('now', '-7 days');

-- Companies with stale validation
SELECT company_id, canonical_name, last_validated_at
FROM companies
WHERE validation_state = 'verified'
  AND last_validated_at < datetime('now', '-30 days');

-- Domain alias conflicts
SELECT domain, COUNT(*) as cnt
FROM (
    SELECT domain FROM companies
    UNION ALL
    SELECT value FROM companies, json_each(domain_aliases)
)
GROUP BY domain
HAVING cnt > 1;
```

#### Manual Repair Workflows

**Workflow: Fix misdetected ATS**
```bash
# 1. Check current state
curl http://localhost:8000/api/companies/abc123

# 2. View probe history
curl http://localhost:8000/api/companies/abc123/probes

# 3. Force manual override
curl -X PATCH http://localhost:8000/api/companies/abc123 \
  -d '{"ats_provider": "lever", "manual_override": true, "override_fields": ["ats_provider"]}'

# 4. Trigger source creation for new ATS
curl -X POST http://localhost:8000/api/companies/abc123/validate
```

**Workflow: Merge duplicate companies**
```sql
-- Manual SQL operation (no API in V1)
BEGIN TRANSACTION;
-- Update all references to use target company
UPDATE company_sources SET company_id = 'target_id' WHERE company_id = 'duplicate_id';
UPDATE canonical_jobs SET company_id = 'target_id' WHERE company_id = 'duplicate_id';
-- Delete duplicate
DELETE FROM companies WHERE company_id = 'duplicate_id';
COMMIT;
```

### 2.1.4 Security and Privacy

#### PII Exposure Risks

| Data Element | PII Risk | Mitigation |
|--------------|----------|------------|
| Company names | None | Public information |
| Company domains | None | Public information |
| Careers URLs | None | Public URLs |
| Logo URLs | Low | Clearbit URLs may track; cache locally if concerned |

#### Secret Handling

- No secrets stored in company registry tables
- Clearbit API key (if used for logos) stored in environment only
- All probe requests use standard User-Agent (no auth tokens exposed)

#### Scraping Compliance

- **robots.txt:** Check before probing careers pages; respect `Disallow: /careers` (rare but possible)
- **Rate limits:** Max 5 probes per domain per hour; track in `ats_detection_log`
- **User-Agent:** `"JobRadar/1.0 (+https://github.com/user/jobradar)"` — identifiable, non-deceptive

#### Auditability

- All probes logged in `ats_detection_log` with timestamp
- Validation state changes tracked via `updated_at` column
- Manual overrides explicitly flagged for audit

### 2.1.5 Decision Record

#### Recommended Approach (Summary from Phase A)

**SHA256-based company_id** derived from normalized domain (or name if no domain). Companies are the foundation for all downstream modules. Validation state machine ensures data quality. Manual overrides provide escape hatch.

#### Rejected Alternative 1: UUID-based company_id

**Approach:** Generate random UUIDs for company_id.

**Why rejected:** 
- Prevents deterministic company resolution
- Same company could get different IDs on re-import
- Complicates deduplication and merge logic

**Revisit trigger:** If hash collisions become measurable problem (extremely unlikely with SHA256).

#### Rejected Alternative 2: Third-party company database (Clearbit, PitchBook)

**Approach:** Use commercial API to resolve company identity.

**Why rejected:**
- Adds external dependency and cost
- Violates local-first constraint
- Most companies in job search are well-known; manual seeding sufficient
- V2 can add enrichment later without changing core model

**Revisit trigger:** If company identity problems exceed 10% of registry; if user requests enrichment features.

### 2.1.6 Solo-Builder Filter

#### Simplest Viable V1

1. Create `companies` table with just: `company_id`, `canonical_name`, `domain`, `ats_provider`, `ats_slug`
2. Seed manually from existing `jobs.company_name` distinct values
3. Skip automated probing entirely—populate ATS info by hand for top 50 companies
4. Add validation state machine later

**Ship in 2 days:** Skip `company_sources` table, skip `ats_detection_log`, skip automated probing. Just a lookup table.

#### Biggest Overengineering Trap

**AVOID:** Building a full company data pipeline with automated discovery, subsidiary hierarchies, and enrichment before shipping anything.

**Instead:** Start with manual seeding. Prove the company_id FK pattern works. Add automation incrementally.

#### What to Cut

| Feature | Cut? | Rationale |
|---------|------|-----------|
| Automated ATS detection | DEFER | Manual seeding faster for V1 |
| Domain alias support | DEFER | Rare edge case |
| Confidence scoring | DEFER | Binary verified/unverified sufficient |
| Bulk import API | KEEP | Needed for seeding |
| Manual override | KEEP | Essential escape hatch |

#### Complexity Budget

**V1 Target:** 2-3 days implementation  
**Tables:** 1-2 (companies, optionally company_sources)  
**Endpoints:** 4 (CRUD)  
**Tests:** 15-20 unit tests, 5 integration tests

### 2.1.7 Open Questions / Assumptions

| # | Assumption | Why Made | Risk If False | Validation Method |
|---|------------|----------|---------------|-------------------|
| 1 | Most target companies use Greenhouse, Lever, or Ashby | Based on tech industry job boards | Miss jobs from Workday/iCIMS companies | Survey user's watchlist after 30 days |
| 2 | Company domains are stable (rarely change) | Rebrands are infrequent | Orphaned company records | Monitor `domain_aliases` usage |
| 3 | ATS URL patterns are detectable | Public board URLs follow conventions | Low detection rate | Track `ats_provider=unknown` percentage |
| 4 | Manual seeding is acceptable for V1 | Solo builder can curate 50-100 companies | Bottleneck if user wants 500+ companies | Measure time spent on manual seeding |
| 5 | Subsidiary handling can wait for V2 | Rare enough to handle manually | Duplicate jobs from Amazon/AWS/Twitch | Count multi-board companies in registry |

---

## 2.2 Module 2: Search Expansion Engine

### 2.2.1 Edge Cases and Failure Modes

| # | Failure Scenario | Handling | Recovery Strategy | User Impact |
|---|-----------------|----------|-------------------|-------------|
| 1 | **Query explosion** — "Engineer" expands to 500+ variants | Cap at 50 variants per intent; use strictness=strict | Adjust expansion rules to reduce breadth | Slightly reduced recall |
| 2 | **Empty expansion** — Unknown role title has no rules | Return original query unchanged | Log for rule gap analysis | No expansion benefit |
| 3 | **Circular rule reference** — Rule A expands to B, B expands to A | Detect cycles during rule loading; skip circular rules | Fix rules in database | Rules don't apply |
| 4 | **Source translator missing** — New scraper added without translator | Fallback to raw intent string | Add translator for new source | Suboptimal query format |
| 5 | **Performance tracking overflow** — Millions of query_performance rows | Partition by month; auto-delete rows >90 days old | Archive old data before delete | Historical analytics limited |
| 6 | **Invalid AST structure** — Malformed JSON in expansion_ast | JSON schema validation on save; reject invalid | Return error to caller | Save operation fails |
| 7 | **Conflicting rules** — Two rules match same input, different outputs | Priority field determines winner; log conflicts | Review overlapping rules | Predictable behavior |
| 8 | **Unicode handling** — Role title in non-ASCII | Normalize to NFKC form; test with CJK/emoji | Ensure UTF-8 throughout | No issues if normalized |
| 9 | **Strictness mismatch** — User expects "broad" but results are narrow | Clear UI explanation of strictness levels | Adjust defaults based on feedback | User confusion |
| 10 | **Stale cached template** — Rules updated but cached template served | TTL on cache (1 hour); cache invalidation on rule change | Clear cache on rule update | Up to 1 hour stale |

### 2.2.2 Testing Strategy

#### Unit Tests

**What to test:**
- `normalize_intent()` — case, whitespace, punctuation handling
- `apply_expansion_rules()` — rule matching and priority
- `build_ast()` — AND/OR tree construction
- `apply_seniority_variants()` — prefix generation
- `dedupe_variants()` — equivalent variant suppression
- `translate_for_source()` — per-source query format

**Mocking strategy:**
- No external mocks needed—pure logic
- Use in-memory rule dictionaries

#### Integration Tests

**Database fixtures needed:**
- 20 expansion rules (synonym, seniority, skill types)
- 10 query templates with various strictness levels
- 100 query_performance records for analytics tests

**Key integration tests:**
```python
async def test_expand_ml_engineer_returns_expected_variants():
    """ML Engineer expands to Machine Learning Engineer, Applied Scientist, etc."""
    
async def test_source_translation_serpapi_uses_or_syntax():
    """SerpApi queries use quoted OR syntax."""
    
async def test_performance_tracking_records_execution():
    """Query execution records result count."""
```

#### Contract Tests

- Expansion AST conforms to JSON schema
- Source translations are valid query strings
- Performance metrics are numeric

#### Red-Team Failure Cases

1. **Rule injection** — Rule input_pattern contains regex metacharacters
2. **AST depth attack** — Deeply nested AND/OR tree (>10 levels)
3. **Massive intent string** — 10KB intent input
4. **Concurrent template updates** — Race condition on save
5. **Malicious source name** — Source translator for "'; DROP TABLE"

#### Example Test Function Names

```python
# tests/test_search_expansion.py
def test_normalize_intent_lowercases()
def test_normalize_intent_strips_whitespace()
def test_normalize_intent_removes_punctuation()
def test_apply_rules_synonym_type()
def test_apply_rules_priority_ordering()
def test_apply_rules_no_match_returns_original()
def test_build_ast_simple_or()
def test_build_ast_with_seniority_variants()
def test_dedupe_removes_equivalent_titles()
def test_translate_serpapi_quoted_or()
def test_translate_greenhouse_simple_string()
def test_template_cache_invalidation_on_rule_update()
def test_strictness_strict_fewer_variants()
def test_strictness_broad_more_variants()
def test_performance_record_created_on_execution()
```

#### Test Coverage Expectations

| Category | Target |
|----------|--------|
| Unit tests | 95% line coverage |
| Rule types | 100% type coverage |
| Source translators | All 7 sources |

### 2.2.3 Observability

#### Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `search_expansion_requests_total` | Counter | `strictness` | Expansion requests |
| `search_expansion_variants_generated` | Histogram | - | Variants per expansion |
| `search_expansion_duration_seconds` | Histogram | - | Expansion latency |
| `search_expansion_rules_total` | Gauge | `rule_type` | Active rules by type |
| `search_expansion_cache_hits_total` | Counter | - | Template cache hits |
| `search_expansion_cache_misses_total` | Counter | - | Template cache misses |
| `search_query_results_total` | Counter | `source`, `template_id` | Jobs found per query |
| `search_query_new_jobs_total` | Counter | `source`, `template_id` | Net new jobs |

#### Logs

| Level | Event | Key Fields |
|-------|-------|------------|
| INFO | Expansion completed | `intent`, `strictness`, `variant_count`, `duration_ms` |
| INFO | Template created | `template_id`, `intent` |
| DEBUG | Rule applied | `rule_id`, `input`, `output` |
| WARN | Query explosion capped | `intent`, `original_count`, `capped_count` |
| WARN | No rules matched | `intent` |
| ERROR | Invalid AST | `template_id`, `error` |

#### Alerts

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| Low expansion rate | `avg variants < 2` for 1 hour | <2 variants | Review rule coverage |
| High cache miss rate | `cache_misses / total > 0.5` | 50% | Check cache config |
| Query returning zero jobs | `results=0` for template >5 times | 5 consecutive | Review query format |

#### Data Quality Checks

```sql
-- Rules with no matches (last 30 days)
SELECT rule_id, input_pattern 
FROM expansion_rules er
WHERE NOT EXISTS (
    SELECT 1 FROM query_performance qp 
    WHERE qp.template_id IN (
        SELECT template_id FROM query_templates 
        WHERE expansion_ast LIKE '%' || er.input_pattern || '%'
    )
    AND qp.executed_at > datetime('now', '-30 days')
);

-- Templates with poor performance
SELECT template_id, intent, 
       AVG(results_count) as avg_results,
       AVG(new_jobs_count) as avg_new
FROM query_performance
GROUP BY template_id
HAVING avg_results < 5;
```

#### Manual Repair Workflows

**Workflow: Add missing expansion rule**
```bash
# 1. Check current rules for role
curl "http://localhost:8000/api/search/rules?input_pattern=Data%20Engineer"

# 2. Add new synonym rule
curl -X POST http://localhost:8000/api/search/rules \
  -d '{"rule_type": "synonym", "input_pattern": "Data Engineer", "output_variants": ["Analytics Engineer", "Data Platform Engineer"]}'

# 3. Test expansion
curl "http://localhost:8000/api/search/expand/preview?intent=Data+Engineer"
```

### 2.2.4 Security and Privacy

#### PII Exposure Risks

| Data Element | PII Risk | Mitigation |
|--------------|----------|------------|
| Search intents | Low | Job titles, not personal data |
| Query templates | None | Reusable patterns |
| Performance data | None | Aggregate counts only |

#### Secret Handling

- No secrets in this module

#### Scraping Compliance

- N/A—this module generates queries, doesn't scrape

#### Auditability

- All templates versioned via `updated_at`
- Performance tracking enables query effectiveness audit

### 2.2.5 Decision Record

#### Recommended Approach (Summary)

Rule-based expansion with AST storage. Deterministic, fast (<10ms), debuggable. Per-source translators handle query format differences.

#### Rejected Alternative 1: Embedding-based semantic expansion

**Approach:** Use sentence embeddings to find similar job titles.

**Why rejected:**
- Adds model dependency (sentence-transformers)
- Non-deterministic—results change with model updates
- Harder to debug why certain titles appear
- V1 rule-based is sufficient; semantic can layer on in V2

**Revisit trigger:** Rule-based recall <60% of semantic approach in A/B test.

#### Rejected Alternative 2: LLM-generated expansions

**Approach:** Call OpenRouter to generate variants.

**Why rejected:**
- Latency (1-2s vs <10ms)
- Cost per expansion
- Non-deterministic
- Overkill for well-defined synonym lists

**Revisit trigger:** If expansion rule maintenance becomes >2 hours/week.

### 2.2.6 Solo-Builder Filter

#### Simplest Viable V1

1. Hardcode 10 expansion rules in Python dict (no database)
2. Single `expand(intent) -> list[str]` function
3. No per-source translation—use same query everywhere
4. No performance tracking

**Ship in 2 days:** Just a utility function with hardcoded synonyms.

#### Biggest Overengineering Trap

**AVOID:** Building a full rule management UI, versioning, A/B testing, and semantic expansion before proving basic expansion helps.

**Instead:** Start with 10 rules. Measure if recall improves. Add sophistication based on data.

#### What to Cut

| Feature | Cut? | Rationale |
|---------|------|-----------|
| Rule database | DEFER | Hardcode in code for V1 |
| Performance tracking | DEFER | Measure later |
| Source-specific translation | DEFER | Use one format initially |
| Strictness levels | DEFER | Single mode first |
| Query preview API | KEEP | Helps debugging |

#### Complexity Budget

**V1 Target:** 1 day implementation  
**Tables:** 0 (hardcoded rules)  
**Endpoints:** 1 (expand)  
**Tests:** 10 unit tests

### 2.2.7 Open Questions / Assumptions

| # | Assumption | Why Made | Risk If False | Validation Method |
|---|------------|----------|---------------|-------------------|
| 1 | Rule-based expansion covers 80% of use cases | Common roles have known synonyms | Miss niche roles | Track "no rules matched" rate |
| 2 | 50 variants is sufficient cap | Balances recall vs query cost | Recall ceiling | A/B test with higher cap |
| 3 | Seniority variants are universal | Most roles have entry/senior/staff | Some roles don't (Founder) | Allow per-rule seniority config |
| 4 | Source query formats are stable | APIs don't change often | Translation breaks | Monitor scraper success rates |
| 5 | Users want expansion, not precision | Recall preferred over precision | Users annoyed by irrelevant jobs | Add strictness controls if complained |

---

## 2.3 Module 3: Validated Source Cache

### 2.3.1 Edge Cases and Failure Modes

| # | Failure Scenario | Handling | Recovery Strategy | User Impact |
|---|-----------------|----------|-------------------|-------------|
| 1 | **Permanent 410 Gone** — Source URL returns 410 | Immediately mark `health_state=dead`; log | Manual review required | Source excluded |
| 2 | **Intermittent 500s** — Source flaps between 200 and 500 | Require 3 consecutive failures before degrading | Success resets counter | Brief gaps possible |
| 3 | **Slow response** — Source returns 200 but takes 30s | Track latency; don't penalize health state for slowness | Separate latency score from health | Slower scrape cycles |
| 4 | **Rate limit (429)** — Source returns 429 | Increment `rate_limit_hits`; apply extra backoff | Reduce scrape frequency for source | Longer intervals |
| 5 | **Cloudflare block** — 403 with Cloudflare challenge | Log as `blocked`; mark `health_state=failing` | May need browser automation (V2) | Source unavailable |
| 6 | **Source URL change** — Company changes board URL | Detect via company probe; create new source | Old source goes `dead`, new source created | Brief gap |
| 7 | **Clock skew** — `next_check_at` in past due to system clock | Use `datetime.utcnow()` consistently; validate timestamps | Recompute on startup | None |
| 8 | **Log table bloat** — `source_check_log` grows unbounded | Auto-delete logs >30 days; batch writes | Scheduled cleanup job | None |
| 9 | **All sources failing** — Network outage | Circuit breaker pauses all scraping | Resume when any source succeeds | No new jobs during outage |
| 10 | **Zombie source** — Source in registry but company deleted | Cascade delete or orphan detection | Cleanup job removes orphans | None |

### 2.3.2 Testing Strategy

#### Unit Tests

**What to test:**
- `compute_source_id()` determinism
- Health state machine transitions
- Backoff calculation formula
- Quality score calculation
- Priority queue ordering

**Mocking strategy:**
- Mock `httpx.AsyncClient` for HTTP checks
- Mock `datetime.utcnow()` for time-dependent tests

#### Integration Tests

**Database fixtures needed:**
- 50 sources in various health states
- 200 check log entries
- Mix of source types

**Key integration tests:**
```python
async def test_source_creation_from_company():
    """Creating company with known ATS creates source entry."""
    
async def test_health_degrades_after_three_failures():
    """Three consecutive failures transition healthy→degraded."""
    
async def test_backoff_increases_exponentially():
    """Backoff duration doubles with each failure."""
    
async def test_priority_queue_excludes_backoff_sources():
    """Sources in backoff don't appear in priority queue."""
```

#### Contract Tests

- Health state values are valid enum members
- Check log status values are valid
- Quality score is 0-100

#### Red-Team Failure Cases

1. **Source ID collision** — Different URLs hash to same ID (extremely unlikely)
2. **Negative backoff** — Calculation error produces negative duration
3. **Infinite loop in state machine** — Transition loop
4. **Race condition on health update** — Concurrent checks update same source
5. **Log insertion failure** — DB write fails mid-batch

#### Example Test Function Names

```python
# tests/test_source_cache.py
def test_compute_source_id_deterministic()
def test_compute_source_id_includes_type_and_url()
def test_health_transition_unknown_to_healthy()
def test_health_transition_healthy_to_degraded_after_failures()
def test_health_transition_degraded_to_failing()
def test_health_transition_failing_to_dead()
def test_health_transition_dead_to_healthy_on_success()
def test_backoff_one_failure_five_minutes()
def test_backoff_ten_failures_twelve_hours()
def test_backoff_caps_at_seven_days()
def test_quality_score_combines_four_factors()
def test_quality_score_clamps_to_zero_hundred()
def test_priority_queue_orders_by_score_desc()
def test_priority_queue_filters_backoff()
def test_record_check_updates_health_state()
def test_batch_write_logs_in_transaction()
```

#### Test Coverage Expectations

| Category | Target |
|----------|--------|
| Unit tests | 90% line coverage |
| State machine | 100% transition coverage |
| Backoff policy | All tiers tested |

### 2.3.3 Observability

#### Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `source_cache_total` | Gauge | `source_type`, `health_state` | Sources by type and health |
| `source_check_duration_seconds` | Histogram | `source_type`, `status` | Check latency |
| `source_check_total` | Counter | `source_type`, `status` | Checks by result |
| `source_health_transitions_total` | Counter | `from_state`, `to_state` | State changes |
| `source_backoff_active_total` | Gauge | `source_type` | Sources currently in backoff |
| `source_quality_score` | Gauge | `source_id` | Per-source quality |
| `source_rate_limit_hits_total` | Counter | `source_type` | 429 responses |
| `source_job_yield_avg` | Gauge | `source_type` | Avg jobs per scrape |

#### Logs

| Level | Event | Key Fields |
|-------|-------|------------|
| INFO | Source created | `source_id`, `source_type`, `url` |
| INFO | Check completed | `source_id`, `status`, `duration_ms`, `jobs_found` |
| INFO | Health changed | `source_id`, `old_state`, `new_state` |
| WARN | Rate limited | `source_id`, `backoff_until` |
| WARN | Source degraded | `source_id`, `consecutive_failures` |
| ERROR | Source dead | `source_id`, `last_error` |

#### Alerts

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| High failure rate | `failing+dead > 20%` of sources | 20% | Check network/APIs |
| Source type down | All sources of type are failing | 100% of type | Provider outage likely |
| Scrape yield dropping | `avg_job_yield < 50%` of baseline | 50% drop | Review scraper logic |

#### Data Quality Checks

```sql
-- Sources never checked
SELECT source_id, url, created_at
FROM source_registry
WHERE last_check_at IS NULL
  AND created_at < datetime('now', '-1 day');

-- Sources stuck in backoff
SELECT source_id, url, backoff_until, consecutive_failures
FROM source_registry
WHERE backoff_until > datetime('now', '+7 days');

-- Orphaned sources (no company)
SELECT source_id, url
FROM source_registry sr
WHERE company_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM companies WHERE company_id = sr.company_id);
```

#### Manual Repair Workflows

**Workflow: Force re-enable dead source**
```bash
# 1. Check source state
curl http://localhost:8000/api/sources/src_abc123

# 2. Force enable via manual override
curl -X PATCH http://localhost:8000/api/sources/src_abc123 \
  -d '{"manual_enabled": true}'

# 3. Trigger immediate check
curl -X POST http://localhost:8000/api/sources/src_abc123/check

# 4. Monitor result
curl http://localhost:8000/api/sources/src_abc123
```

### 2.3.4 Security and Privacy

#### PII Exposure Risks

| Data Element | PII Risk | Mitigation |
|--------------|----------|------------|
| Source URLs | None | Public endpoints |
| Check logs | None | Technical data only |
| Error messages | Low | May contain URL params; sanitize if needed |

#### Secret Handling

- No secrets stored in source tables
- API keys for paid sources (TheirStack, Apify) in environment only

#### Scraping Compliance

- **robots.txt:** Store `robots_compliant` flag per source; respect disallow rules
- **Rate limits:** `rate_limit_hits` counter triggers automatic backoff increase
- **Identification:** All requests use identifiable User-Agent

#### Auditability

- All checks logged with timestamp
- Health transitions observable via logs
- Manual overrides explicitly tracked

### 2.3.5 Decision Record

#### Recommended Approach (Summary)

Centralized source registry with health state machine. Exponential backoff prevents hammering failed sources. Quality scoring enables intelligent prioritization.

#### Rejected Alternative 1: Per-scraper health tracking

**Approach:** Each scraper maintains its own health state.

**Why rejected:**
- Duplicated logic across 7 scrapers
- No unified dashboard
- Harder to correlate failures

**Revisit trigger:** Never—centralized is strictly better.

#### Rejected Alternative 2: Redis for real-time health

**Approach:** Store health state in Redis for faster updates.

**Why rejected:**
- Adds external dependency
- Violates SQLite-only constraint
- Health updates aren't high-frequency enough to need Redis

**Revisit trigger:** If SQLite write contention becomes measurable problem.

### 2.3.6 Solo-Builder Filter

#### Simplest Viable V1

1. Skip health state machine—just track `last_success_at` and `failure_count`
2. Simple rule: skip source if `failure_count > 5` and `last_success_at` > 24h ago
3. No quality scoring—equal priority for all sources
4. No check log—just update source record

**Ship in 2 days:** Basic fail tracking without state machine complexity.

#### Biggest Overengineering Trap

**AVOID:** Building dashboards, alerting, and priority optimization before basic tracking works.

**Instead:** Track failures. Prove it helps skip dead sources. Add sophistication later.

#### What to Cut

| Feature | Cut? | Rationale |
|---------|------|-----------|
| Health state machine | SIMPLIFY | Binary working/broken sufficient |
| Quality scoring | DEFER | Equal priority fine for V1 |
| Check log table | DEFER | Just update source record |
| Batch write optimization | DEFER | Low volume initially |
| robots.txt checking | KEEP | Legal compliance |

#### Complexity Budget

**V1 Target:** 1-2 days implementation  
**Tables:** 1 (source_registry)  
**Endpoints:** 3 (list, get, record-check)  
**Tests:** 15 unit tests

### 2.3.7 Open Questions / Assumptions

| # | Assumption | Why Made | Risk If False | Validation Method |
|---|------------|----------|---------------|-------------------|
| 1 | 200-500 sources is manageable | Company watchlist + aggregators | Performance issues at scale | Load test with 2000 sources |
| 2 | 30-day log retention sufficient | Debug window, not long-term analytics | Miss historical patterns | Extend if users request |
| 3 | Exponential backoff is appropriate | Industry standard | May be too aggressive | Adjust multiplier if needed |
| 4 | Quality score formula is correct | Based on intuition | Suboptimal prioritization | A/B test priority orderings |
| 5 | SQLite handles write batching well | WAL mode + batching | Write contention | Monitor SQLite metrics |

---

## 2.4 Module 4: Canonical Jobs Pipeline

### 2.4.1 Edge Cases and Failure Modes

| # | Failure Scenario | Handling | Recovery Strategy | User Impact |
|---|-----------------|----------|-------------------|-------------|
| 1 | **Same job, wildly different titles** — "Senior ML Engineer" vs "AI/ML Staff" | Fuzzy match with company + location; accept if >85% similarity | Manual merge via API | Possible duplicate |
| 2 | **Location ambiguity** — "New York" vs "NYC" vs "New York, NY" | Normalize all to canonical form; use geocoding lookup | Mapping table for common aliases | Correct matching |
| 3 | **Salary currency mismatch** — EUR vs USD | Store both original and normalized (to annual USD) | Use exchange rate at scrape time | Approximate salary |
| 4 | **Description HTML variations** — Same content, different formatting | Strip HTML, normalize whitespace, compare text | Description not used for matching | None |
| 5 | **Job reposted** — Same job appears with new source_job_id | Canonical ID based on company+title+location, not source ID | Merge into existing canonical | source_count increases |
| 6 | **Company not in registry** — Raw job has unknown company | Create company record with `validation_state=unverified` | Trigger company probe async | Minor delay |
| 7 | **All sources report job gone** — Job disappears | Mark raw sources `is_active=false`; after 14 days, mark canonical closed | Reversible if job reappears | Job marked closed |
| 8 | **Merge creates incorrect canonical** — Wrong jobs merged together | Expose split API for manual correction | Admin splits canonical into two | User sees wrong data |
| 9 | **Backfill conflicts with live writes** — Migration runs while scrapers active | Backfill uses INSERT OR IGNORE; scrapers use normal upsert | Both paths produce consistent result | None |
| 10 | **Enrichment targets wrong table** — LLM enriches raw instead of canonical | Clear API separation; enrichment service only reads/writes canonical | Code review enforcement | Wasted LLM calls |

### 2.4.2 Testing Strategy

#### Unit Tests

**What to test:**
- `compute_canonical_job_id()` determinism
- `normalize_title()` strips seniority, case, punctuation
- `normalize_location()` handles city/state/country parsing
- Merge logic field precedence
- Stale detection rules

**Mocking strategy:**
- Mock company registry lookups
- Mock source quality scores

#### Integration Tests

**Database fixtures needed:**
- 50 companies
- 100 raw_job_sources (some mergeable)
- 60 canonical_jobs
- Cross-source duplicates

**Key integration tests:**
```python
async def test_raw_job_creates_canonical():
    """First raw job for company+title+location creates canonical."""
    
async def test_second_source_merges_into_canonical():
    """Second raw job for same canonical merges, increments source_count."""
    
async def test_greenhouse_wins_over_serpapi():
    """Greenhouse salary used when both sources have salary."""
    
async def test_stale_detection_marks_inactive():
    """Job not seen in 14 days becomes is_active=false."""
    
async def test_legacy_jobs_table_synced():
    """canonical_jobs writes also update jobs table."""
```

#### Contract Tests

- Canonical job ID format validation
- Source precedence rules documented and enforced
- Merge output matches expected schema

#### Red-Team Failure Cases

1. **Canonical ID collision** — Different jobs produce same ID
2. **Circular merge** — Job A merges into B, B merges into A
3. **Source quality not available** — Source not in registry
4. **Null company_id** — Company lookup fails
5. **Massive description** — 1MB job description

#### Example Test Function Names

```python
# tests/test_canonical_pipeline.py
def test_compute_canonical_id_deterministic()
def test_compute_canonical_id_case_insensitive()
def test_normalize_title_strips_seniority_prefix()
def test_normalize_title_strips_punctuation()
def test_normalize_location_parses_city_state()
def test_normalize_location_handles_remote()
def test_merge_prefers_greenhouse_salary()
def test_merge_prefers_longest_description()
def test_merge_uses_company_registry_name()
def test_stale_job_marked_after_fourteen_days()
def test_closed_job_has_closed_at_timestamp()
def test_raw_job_links_to_canonical()
def test_source_count_increments_on_merge()
def test_legacy_sync_updates_jobs_table()
def test_backfill_idempotent()
```

#### Test Coverage Expectations

| Category | Target |
|----------|--------|
| Unit tests | 90% line coverage |
| Merge logic | 100% field coverage |
| State machine | 100% transition coverage |

### 2.4.3 Observability

#### Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `canonical_jobs_total` | Gauge | `is_active` | Total canonical jobs |
| `canonical_jobs_by_source_count` | Histogram | - | Distribution of source counts |
| `raw_job_sources_total` | Gauge | `source`, `is_active` | Raw sources by type |
| `canonical_merge_total` | Counter | `action` | create/update/skip actions |
| `canonical_merge_duration_seconds` | Histogram | - | Merge operation latency |
| `canonical_stale_total` | Gauge | - | Jobs marked stale |
| `canonical_closed_total` | Counter | - | Jobs marked closed |
| `canonical_quality_score` | Histogram | - | Distribution of quality scores |

#### Logs

| Level | Event | Key Fields |
|-------|-------|------------|
| INFO | Canonical created | `canonical_job_id`, `company_name`, `title` |
| INFO | Canonical merged | `canonical_job_id`, `raw_id`, `source`, `source_count` |
| INFO | Job marked stale | `canonical_job_id`, `last_seen_days_ago` |
| INFO | Job marked closed | `canonical_job_id`, `closed_at` |
| WARN | Company not found | `company_name_raw`, creating new |
| WARN | Merge conflict | `canonical_job_id`, `field`, `values` |
| ERROR | Canonical ID collision | `id`, `existing_job`, `new_job` |

#### Alerts

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| High duplicate rate | `merges / creates > 2` | 2:1 ratio | Review matching logic |
| Low quality scores | `avg quality_score < 50` | <50 | Check source data |
| Stale jobs growing | `stale jobs > 30%` | 30% | Review scraper schedules |

#### Data Quality Checks

```sql
-- Canonical jobs with no raw sources
SELECT canonical_job_id, title
FROM canonical_jobs cj
WHERE NOT EXISTS (
    SELECT 1 FROM raw_job_sources WHERE canonical_job_id = cj.canonical_job_id
);

-- Raw sources not linked to canonical
SELECT raw_id, title_raw, source
FROM raw_job_sources
WHERE canonical_job_id IS NULL
  AND first_seen_at < datetime('now', '-1 hour');

-- Source count mismatch
SELECT canonical_job_id, source_count,
       (SELECT COUNT(*) FROM raw_job_sources WHERE canonical_job_id = cj.canonical_job_id) as actual
FROM canonical_jobs cj
WHERE source_count != actual;
```

#### Manual Repair Workflows

**Workflow: Split incorrectly merged jobs**
```sql
-- Manual SQL (no API in V1)
BEGIN TRANSACTION;
-- Create new canonical for split-off job
INSERT INTO canonical_jobs (canonical_job_id, company_id, title, ...)
SELECT 'new_canonical_id', company_id, title_raw, ...
FROM raw_job_sources
WHERE raw_id = 'raw_to_split';

-- Update raw source to point to new canonical
UPDATE raw_job_sources
SET canonical_job_id = 'new_canonical_id'
WHERE raw_id = 'raw_to_split';

-- Decrement source count on original
UPDATE canonical_jobs
SET source_count = source_count - 1
WHERE canonical_job_id = 'original_canonical_id';
COMMIT;
```

### 2.4.4 Security and Privacy

#### PII Exposure Risks

| Data Element | PII Risk | Mitigation |
|--------------|----------|------------|
| Job titles | None | Public postings |
| Company names | None | Public information |
| Salary data | Low | Aggregated, not individual |
| Apply URLs | None | Public links |
| Raw payload | Low | May contain recruiter names; don't expose in API |

#### Secret Handling

- No secrets in job data

#### Scraping Compliance

- Raw payload stores source data for audit
- Respect copyright on job descriptions (don't republish verbatim publicly)

#### Auditability

- Raw sources preserve original data
- Merge decisions traceable via source precedence rules

### 2.4.5 Decision Record

#### Recommended Approach (Summary)

Two-tier model: raw_job_sources preserves scraper output; canonical_jobs is merged view. Deterministic canonical_job_id from company+title+location. Source quality weights field selection.

#### Rejected Alternative 1: Single merged jobs table

**Approach:** Write merged data directly to jobs table, overwriting previous.

**Why rejected:**
- Loses provenance information
- Can't debug merge decisions
- Can't recover if merge logic wrong
- No source attribution

**Revisit trigger:** Never—two-tier is strictly better for this use case.

#### Rejected Alternative 2: Event sourcing for all job changes

**Approach:** Store every job update as immutable event.

**Why rejected:**
- Massive storage overhead
- Complex replay logic
- Solo builder doesn't need full audit history
- raw_job_sources provides sufficient provenance

**Revisit trigger:** If compliance requires complete change history.

### 2.4.6 Solo-Builder Filter

#### Simplest Viable V1

1. Keep existing `jobs` table as-is
2. Add `canonical_job_id` column (nullable)
3. Simple dedup: if same company+title exists in last 7 days, set `duplicate_of`
4. Skip raw_job_sources table entirely

**Ship in 2 days:** Enhanced dedup on existing table, no new tables.

#### Biggest Overengineering Trap

**AVOID:** Building full provenance tracking, merge UI, and quality scoring before proving basic dedup helps.

**Instead:** Add canonical_job_id column. Improve dedup. Add raw_job_sources later.

#### What to Cut

| Feature | Cut? | Rationale |
|---------|------|-----------|
| raw_job_sources table | DEFER | Use existing jobs table |
| Source quality weighting | DEFER | Simple "ATS wins" rule |
| Stale detection | DEFER | Manual review sufficient |
| Legacy sync | N/A | Still using jobs table |
| Merge API | DEFER | Manual SQL if needed |

#### Complexity Budget

**V1 Target:** 2-3 days implementation  
**Tables:** 0 new (modify jobs)  
**Endpoints:** 0 new (enhance existing)  
**Tests:** 20 tests for dedup logic

### 2.4.7 Open Questions / Assumptions

| # | Assumption | Why Made | Risk If False | Validation Method |
|---|------------|----------|---------------|-------------------|
| 1 | Company+title+location is unique enough | Standard job identity | Collisions (same role, diff teams) | Track canonical merge rate |
| 2 | 14 days is right stale threshold | Jobs typically filled in 2-4 weeks | Mark active jobs as closed | Survey closed job accuracy |
| 3 | ATS data is higher quality than aggregators | Direct source vs scraped | Wrong precedence decisions | Compare field accuracy |
| 4 | Dual-write period is safe | Both tables updated together | Data inconsistency | Integration tests |
| 5 | Backfill can run during normal operation | Low write conflict | Data corruption | Run backfill during low activity |

---

## 2.5 Module 5: Application Tracker

### 2.5.1 Edge Cases and Failure Modes

| # | Failure Scenario | Handling | Recovery Strategy | User Impact |
|---|-----------------|----------|-------------------|-------------|
| 1 | **Job deleted while user tracking** — Canonical job removed | Application retains `canonical_job_id` FK; job details cached in UI | Job shows "[Deleted]" badge | Tracking continues |
| 2 | **Status transition invalid** — "saved" → "offer" (skipping applied) | Validate against state machine; reject invalid transitions | Return 400 error with valid options | User informed |
| 3 | **Concurrent status updates** — User and system update simultaneously | Optimistic locking via `updated_at`; user wins on conflict | Retry with fresh data | Occasional retry needed |
| 4 | **Reminder in past** — User sets reminder_at to yesterday | Accept and immediately trigger; or reject with error | Return warning, proceed | Immediate notification |
| 5 | **Module 4 not deployed** — Application created before canonical_jobs | Link to `legacy_job_id` instead | Migrate link when M4 available | Graceful degradation |
| 6 | **Duplicate application** — User saves same job twice | UNIQUE constraint on (canonical_job_id OR legacy_job_id) | Return existing application | No duplicate |
| 7 | **Bulk status change** — User archives 50 applications | Batch update in single transaction | Transaction rollback on failure | All or nothing |
| 8 | **Notes contain HTML/scripts** — XSS risk | Sanitize HTML on input; escape on output | Strip dangerous tags | Safe display |
| 9 | **Custom fields schema drift** — User adds fields, forgets structure | JSON schema not enforced; app handles arbitrary keys | Document suggested fields | Flexible but unvalidated |
| 10 | **Export with 1000+ applications** — CSV generation slow | Stream response; limit to 500 per export | Pagination or background job | Timeout if too large |

### 2.5.2 Testing Strategy

#### Unit Tests

**What to test:**
- Status state machine validity
- Transition validation logic
- Reminder scheduling logic
- Tag normalization
- Custom field handling

**Mocking strategy:**
- Mock job lookups
- Mock datetime for reminder tests

#### Integration Tests

**Database fixtures needed:**
- 100 applications in all statuses
- Status history entries
- Tags and custom fields
- Reminder data

**Key integration tests:**
```python
async def test_application_creation_links_to_canonical():
    """New application links to canonical_job_id when available."""
    
async def test_status_change_creates_history():
    """Status transition creates history entry."""
    
async def test_invalid_transition_rejected():
    """Jumping from saved to offer returns 400."""
    
async def test_user_edits_survive_job_refresh():
    """Notes and tags unchanged when canonical updates."""
    
async def test_reminder_appears_in_upcoming():
    """Reminder within 24h appears in reminders endpoint."""
```

#### Contract Tests

- Status values are valid enum members
- Timeline events have required fields
- Export format matches specification

#### Red-Team Failure Cases

1. **SQL injection via notes** — Ensure parameterized queries
2. **XSS via tags** — Sanitize tag names
3. **JSON injection via custom_fields** — Validate JSON structure
4. **Concurrent application creation** — Race to create same app
5. **Massive notes field** — 10MB of text

#### Example Test Function Names

```python
# tests/test_application_tracker.py
def test_create_application_generates_id()
def test_create_application_links_canonical_job()
def test_create_application_fallback_to_legacy_job()
def test_duplicate_application_returns_existing()
def test_status_transition_saved_to_applied()
def test_status_transition_applied_to_interviewing()
def test_status_transition_invalid_rejected()
def test_status_change_creates_history_entry()
def test_notes_update_preserves_status()
def test_tags_normalized_lowercase()
def test_custom_fields_stored_as_json()
def test_reminder_set_updates_record()
def test_reminders_endpoint_filters_by_due()
def test_export_csv_format()
def test_archive_hides_from_list()
def test_optimistic_lock_detects_conflict()
```

#### Test Coverage Expectations

| Category | Target |
|----------|--------|
| Unit tests | 90% line coverage |
| Status transitions | 100% valid paths |
| API endpoints | All CRUD operations |

### 2.5.3 Observability

#### Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `applications_total` | Gauge | `status`, `is_archived` | Applications by status |
| `application_status_transitions_total` | Counter | `from_status`, `to_status` | Transitions |
| `application_created_total` | Counter | - | New applications |
| `application_reminder_total` | Gauge | - | Active reminders |
| `application_export_total` | Counter | `format` | Exports by format |
| `application_api_duration_seconds` | Histogram | `endpoint` | API latency |

#### Logs

| Level | Event | Key Fields |
|-------|-------|------------|
| INFO | Application created | `application_id`, `canonical_job_id`, `status` |
| INFO | Status changed | `application_id`, `old_status`, `new_status` |
| INFO | Reminder set | `application_id`, `reminder_at` |
| INFO | Application archived | `application_id` |
| WARN | Invalid transition | `application_id`, `current`, `attempted` |
| WARN | Optimistic lock conflict | `application_id`, `expected_version`, `actual_version` |
| ERROR | Export failed | `application_ids`, `error` |

#### Alerts

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| High rejection rate | `rejected+ghosted > 50%` | 50% of total | User may want to adjust strategy |
| Stale applications | `status=applied for >30 days` | 30 days | Suggest follow-up |
| Overdue reminders | `reminder_at < now - 1 day` | 1 day overdue | Check reminder system |

#### Data Quality Checks

```sql
-- Applications with invalid job links
SELECT application_id, canonical_job_id, legacy_job_id
FROM applications
WHERE canonical_job_id IS NOT NULL 
  AND NOT EXISTS (SELECT 1 FROM canonical_jobs WHERE canonical_job_id = applications.canonical_job_id)
  AND legacy_job_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM jobs WHERE job_id = applications.legacy_job_id);

-- Status history gaps
SELECT a.application_id, a.status, h.new_status
FROM applications a
LEFT JOIN application_status_history h 
  ON h.application_id = a.application_id 
  AND h.new_status = a.status
WHERE h.id IS NULL AND a.status != 'saved';

-- Orphaned history entries
SELECT h.application_id
FROM application_status_history h
WHERE NOT EXISTS (SELECT 1 FROM applications WHERE application_id = h.application_id);
```

#### Manual Repair Workflows

**Workflow: Fix stuck application status**
```bash
# 1. Check current state
curl http://localhost:8000/api/applications/app_abc123

# 2. View history
curl http://localhost:8000/api/applications/app_abc123/history

# 3. Force status (bypasses validation)
curl -X PATCH http://localhost:8000/api/applications/app_abc123 \
  -d '{"status": "applied", "_force": true}'

# 4. Add history entry manually
curl -X POST http://localhost:8000/api/applications/app_abc123/history \
  -d '{"old_status": "saved", "new_status": "applied", "note": "Manual correction"}'
```

### 2.5.4 Security and Privacy

#### PII Exposure Risks

| Data Element | PII Risk | Mitigation |
|--------------|----------|------------|
| Notes | HIGH | May contain personal info; encrypt at rest in V2 |
| Tags | LOW | User-defined labels |
| Custom fields | MEDIUM | May contain referrer names, etc. |
| Applied_via | LOW | Application method |

#### Secret Handling

- No secrets in application data
- Future: If storing login credentials for auto-apply, use encrypted field

#### Scraping Compliance

- N/A—user-authored data only

#### Auditability

- Status history provides complete audit trail
- All changes timestamped

### 2.5.5 Decision Record

#### Recommended Approach (Summary)

Separate `applications` table from job data. Status state machine with history tracking. User-owned fields never modified by system. Links to canonical_job_id with graceful degradation.

#### Rejected Alternative 1: Status in jobs table

**Approach:** Keep tracking `jobs.status` as-is.

**Why rejected:**
- Mixes user state with system state
- Scraper updates could overwrite user edits
- Job deletion loses application history
- No audit trail

**Revisit trigger:** Never—separation is essential.

#### Rejected Alternative 2: Full event sourcing for applications

**Approach:** Every change is an immutable event; state derived from event log.

**Why rejected:**
- Overkill for personal tool
- Complex state reconstruction
- Status history table provides sufficient audit trail

**Revisit trigger:** If user needs to time-travel through application history.

### 2.5.6 Solo-Builder Filter

#### Simplest Viable V1

1. Keep using `jobs.status` for now
2. Add `jobs.notes` and `jobs.tags` columns
3. No status history tracking
4. No separate applications table

**Ship in 2 days:** Enhanced jobs table, no new tables.

#### Biggest Overengineering Trap

**AVOID:** Building full status state machine, history tracking, reminders, and export before proving basic tracking helps.

**Instead:** Add notes column. Ship. Add history later.

#### What to Cut

| Feature | Cut? | Rationale |
|---------|------|-----------|
| applications table | DEFER | Use jobs.status |
| Status history | DEFER | No audit needed for V1 |
| Reminders | DEFER | Manual calendar works |
| Custom fields | DEFER | Tags sufficient |
| Export API | DEFER | Manual copy-paste |

#### Complexity Budget

**V1 Target:** 1-2 days implementation  
**Tables:** 0 new (modify jobs)  
**Endpoints:** 2 new (notes, tags)  
**Tests:** 15 tests

### 2.5.7 Open Questions / Assumptions

| # | Assumption | Why Made | Risk If False | Validation Method |
|---|------------|----------|---------------|-------------------|
| 1 | Users track <500 applications | Personal job search | Performance issues | Monitor application count |
| 2 | Status state machine covers all workflows | Based on common paths | Users want custom statuses | Feedback collection |
| 3 | 11 status values is enough | Common interview stages | Missing states | Track rejected transitions |
| 4 | JSON custom_fields is flexible enough | Avoids schema changes | Query performance | Monitor query latency |
| 5 | Linking to canonical_job_id is sufficient | Canonical is stable | Canonical merges break links | Cascade update tests |

---

## 3. Operational Runbooks

### 3.1 Database Maintenance Procedures

#### Daily Maintenance (Automated via APScheduler)

```python
# Add to scheduler.py
scheduler.add_job(
    run_daily_maintenance,
    'cron',
    hour=4,
    minute=0,
    id='daily_maintenance'
)

async def run_daily_maintenance():
    """Run at 4 AM daily."""
    async with get_session() as session:
        # 1. Clean old source check logs
        await session.execute(text("""
            DELETE FROM source_check_log 
            WHERE checked_at < datetime('now', '-30 days')
        """))
        
        # 2. Clean old query performance data
        await session.execute(text("""
            DELETE FROM query_performance 
            WHERE executed_at < datetime('now', '-90 days')
        """))
        
        # 3. Update stale job detection
        await session.execute(text("""
            UPDATE canonical_jobs 
            SET is_active = FALSE, closed_at = datetime('now')
            WHERE is_active = TRUE 
              AND last_seen_at < datetime('now', '-14 days')
        """))
        
        await session.commit()
```

#### Weekly Maintenance (Manual or Scheduled)

```bash
#!/bin/bash
# scripts/weekly_maintenance.sh

DB_PATH="data/jobradar.db"

echo "Running weekly maintenance..."

# 1. Analyze tables for query optimization
sqlite3 "$DB_PATH" "ANALYZE;"

# 2. Check database integrity
sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | head -1

# 3. Report database size
echo "Database size: $(du -h $DB_PATH | cut -f1)"

# 4. Report table sizes
sqlite3 "$DB_PATH" "
SELECT name, 
       (SELECT COUNT(*) FROM pragma_table_info(name)) as columns,
       (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=name) as indexes
FROM sqlite_master 
WHERE type='table' AND name NOT LIKE 'sqlite_%'
ORDER BY name;
"
```

### 3.2 Manual State Repair

#### Repair Corrupted Company Validation State

```bash
# Scenario: Company stuck in 'probing' state due to crash

# 1. Identify stuck companies
sqlite3 data/jobradar.db "
SELECT company_id, canonical_name, validation_state, last_probe_at
FROM companies
WHERE validation_state = 'probing'
  AND last_probe_at < datetime('now', '-1 hour');
"

# 2. Reset to unverified
sqlite3 data/jobradar.db "
UPDATE companies
SET validation_state = 'unverified',
    probe_error = 'Reset due to stuck state',
    updated_at = datetime('now')
WHERE validation_state = 'probing'
  AND last_probe_at < datetime('now', '-1 hour');
"

# 3. Trigger re-probe via API
curl -X POST http://localhost:8000/api/companies/batch-validate
```

#### Repair Orphaned Raw Job Sources

```bash
# Scenario: Raw sources without canonical link

# 1. Find orphans
sqlite3 data/jobradar.db "
SELECT raw_id, source, title_raw, company_name_raw
FROM raw_job_sources
WHERE canonical_job_id IS NULL
  AND first_seen_at < datetime('now', '-2 hours')
LIMIT 20;
"

# 2. Trigger re-processing
curl -X POST http://localhost:8000/api/internal/reprocess-orphan-raws

# 3. If still orphaned, check for company issues
sqlite3 data/jobradar.db "
SELECT DISTINCT company_name_raw
FROM raw_job_sources
WHERE canonical_job_id IS NULL;
"
```

### 3.3 Force-Refresh Stale Data

#### Force Company Re-Probe

```bash
# Single company
curl -X POST http://localhost:8000/api/companies/abc123/validate

# All stale companies (>30 days since validation)
curl -X POST http://localhost:8000/api/companies/batch-validate?stale_days=30

# Force refresh even if recently probed
curl -X POST http://localhost:8000/api/companies/abc123/validate?force=true
```

#### Force Source Health Recheck

```bash
# Single source
curl -X POST http://localhost:8000/api/sources/src123/check

# All sources of type
curl -X POST http://localhost:8000/api/sources/batch-check?source_type=greenhouse

# Clear backoff and recheck
curl -X PATCH http://localhost:8000/api/sources/src123 \
  -d '{"backoff_until": null, "consecutive_failures": 0}'
curl -X POST http://localhost:8000/api/sources/src123/check
```

#### Force Canonical Job Re-Merge

```bash
# Trigger re-merge for specific canonical
curl -X POST http://localhost:8000/api/canonical-jobs/canon123/remerge

# Re-process all raw sources for a company
curl -X POST http://localhost:8000/api/companies/abc123/reprocess-jobs
```

### 3.4 Migration Rollback

#### Rollback Strategy (Additive Migrations Only)

Since all migrations are additive (no column drops, no data deletion), rollback means:
1. Deploy previous code version (doesn't use new columns/tables)
2. New columns/tables remain but are ignored
3. No data loss

#### Emergency Column Removal (If Absolutely Necessary)

```bash
# WARNING: Data loss - only for emergency
# Create backup first!

cp data/jobradar.db data/jobradar.db.backup

# Remove column via table recreation (SQLite limitation)
sqlite3 data/jobradar.db "
BEGIN TRANSACTION;

-- Create new table without column
CREATE TABLE jobs_new AS 
SELECT job_id, title, company_name, ...  -- exclude bad column
FROM jobs;

-- Drop old table
DROP TABLE jobs;

-- Rename new table
ALTER TABLE jobs_new RENAME TO jobs;

-- Recreate indexes
CREATE INDEX idx_jobs_company ON jobs(company_name);
-- ... other indexes

COMMIT;
"
```

### 3.5 SQLite-Specific Maintenance

#### VACUUM (Reclaim Space)

```bash
# Check if VACUUM needed
sqlite3 data/jobradar.db "
SELECT page_count * page_size as size_bytes,
       freelist_count * page_size as free_bytes,
       (freelist_count * 100.0 / page_count) as free_percent
FROM pragma_page_count(), pragma_freelist_count(), pragma_page_size();
"

# Run VACUUM if >20% free space
sqlite3 data/jobradar.db "VACUUM;"

# Note: VACUUM requires 2x disk space temporarily and locks DB
```

#### Integrity Check

```bash
# Quick check
sqlite3 data/jobradar.db "PRAGMA quick_check;"

# Full integrity check (slower)
sqlite3 data/jobradar.db "PRAGMA integrity_check;"

# Check foreign key violations
sqlite3 data/jobradar.db "PRAGMA foreign_key_check;"
```

#### WAL Checkpoint

```bash
# Check WAL size
ls -lh data/jobradar.db-wal

# Force checkpoint (writes WAL to main DB)
sqlite3 data/jobradar.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

#### Index Maintenance

```bash
# Check index usage (requires SQLITE_ENABLE_STAT4)
sqlite3 data/jobradar.db "
SELECT name, stat FROM sqlite_stat1 ORDER BY name;
"

# Rebuild indexes
sqlite3 data/jobradar.db "REINDEX;"
```

---

## 4. Quality Gates

### 4.1 Definition of Done Checklist (Reusable)

```markdown
## Module: [Name]
## PR: [Link]
## Date: [Date]

### Code Quality
- [ ] All new functions have docstrings
- [ ] Type hints on all function signatures
- [ ] No `# type: ignore` without justification
- [ ] Logging at appropriate levels (INFO for normal, WARN for issues, ERROR for failures)
- [ ] Error messages are actionable

### Testing
- [ ] Unit test coverage ≥ 90% for new code
- [ ] Integration tests for all API endpoints
- [ ] Edge cases from spec are tested
- [ ] Red-team failure cases are tested
- [ ] Tests run in < 30 seconds

### Database
- [ ] Migration is additive only (no column drops)
- [ ] Indexes exist for query patterns
- [ ] Foreign keys have ON DELETE behavior defined
- [ ] Example records documented

### API
- [ ] OpenAPI schema updated
- [ ] Error responses follow standard format
- [ ] Idempotency documented for POST/PUT endpoints
- [ ] Rate limits documented (if any)

### Observability
- [ ] Metrics defined and implemented
- [ ] Log statements include context fields
- [ ] Data quality queries documented

### Documentation
- [ ] README section updated
- [ ] API endpoint documentation
- [ ] Schema diagram updated (if tables added)
```

### 4.2 Product Acceptance Criteria Template

```markdown
## Feature: [Name]

### User Story
As a [user type], I want to [action] so that [benefit].

### Acceptance Criteria

#### Must Have (V1)
1. [ ] [Criterion 1]
2. [ ] [Criterion 2]
3. [ ] [Criterion 3]

#### Should Have (V1 stretch)
1. [ ] [Criterion 4]
2. [ ] [Criterion 5]

#### Nice to Have (V2)
1. [ ] [Criterion 6]

### Demo Scenarios
1. [Scenario 1 - happy path]
2. [Scenario 2 - edge case]
3. [Scenario 3 - error handling]

### Not In Scope
- [Explicitly excluded feature 1]
- [Explicitly excluded feature 2]
```

### 4.3 Engineering Acceptance Criteria Template

```markdown
## Module: [Name]

### Performance Requirements
- [ ] API response time p95 < [X]ms
- [ ] Database query time p95 < [X]ms
- [ ] Memory usage < [X]MB
- [ ] No N+1 query patterns

### Reliability Requirements
- [ ] Graceful degradation when [dependency] unavailable
- [ ] Retry logic for transient failures
- [ ] Circuit breaker for [external service]
- [ ] Idempotent operations where specified

### Security Requirements
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS prevention for user content
- [ ] Secrets not logged or exposed

### Operational Requirements
- [ ] Runbook documented for common issues
- [ ] Metrics exposed for monitoring
- [ ] Alerts defined with thresholds
- [ ] Backup/restore procedure tested
```

### 4.4 Test Coverage Expectations

| Module | Unit Tests | Integration | E2E | Total Target |
|--------|-----------|-------------|-----|--------------|
| M1: Company Registry | 90% | 80% | N/A | 85% |
| M2: Search Expansion | 95% | 70% | N/A | 90% |
| M3: Source Cache | 90% | 85% | N/A | 87% |
| M4: Canonical Pipeline | 90% | 85% | 2 scenarios | 87% |
| M5: Application Tracker | 90% | 80% | 3 scenarios | 85% |
| Cross-Module | N/A | N/A | 5 scenarios | N/A |

### 4.5 Operational Readiness Checklist

```markdown
## Module: [Name] - Operational Readiness

### Monitoring
- [ ] Metrics appearing in monitoring dashboard
- [ ] Alert rules configured and tested
- [ ] Log aggregation includes new log lines
- [ ] Dashboard shows key health indicators

### Documentation
- [ ] Runbook covers top 5 failure scenarios
- [ ] Architecture diagram updated
- [ ] API documentation published
- [ ] Data flow documented

### Data Quality
- [ ] Quality check queries documented
- [ ] Baseline metrics established
- [ ] Anomaly detection thresholds set

### Recovery
- [ ] Backup includes new tables
- [ ] Restore procedure tested
- [ ] Rollback procedure documented
- [ ] Data repair scripts ready

### Performance
- [ ] Load test completed
- [ ] Performance baseline established
- [ ] Query plans reviewed for new queries
- [ ] Index usage verified
```

---

## 5. Self-Assessment Scores

### Score Definitions

| Score | Meaning |
|-------|---------|
| 5 | Excellent - Production-ready, minimal risk |
| 4 | Good - Minor concerns, low risk |
| 3 | Adequate - Some concerns, moderate risk |
| 2 | Needs Work - Significant concerns, high risk |
| 1 | Insufficient - Major gaps, very high risk |

### Module Scores

#### Module 1: Company Intelligence Registry

| Criterion | Score | Justification |
|-----------|-------|---------------|
| Architectural clarity | 5 | Clear domain model, well-defined state machine, clean API |
| Migration safety | 5 | Fully additive, no breaking changes, graceful degradation |
| SQLite realism | 4 | Reasonable write volume; may need batching for bulk imports |
| Testability | 5 | Pure functions for ID/normalization, mockable dependencies |
| Future readiness | 4 | Supports subsidiaries in V2; may need parent_company_id |

**Overall: 4.6** — Minor concern around bulk import performance.

#### Module 2: Search Expansion Engine

| Criterion | Score | Justification |
|-----------|-------|---------------|
| Architectural clarity | 5 | Simple pipeline: rules → AST → translation |
| Migration safety | 5 | All new tables, no impact on existing |
| SQLite realism | 5 | Minimal writes, mostly reads, cacheable |
| Testability | 5 | Pure logic, no external dependencies |
| Future readiness | 4 | Semantic expansion will require significant changes |

**Overall: 4.8** — Very clean module; semantic expansion is a larger V2 effort.

#### Module 3: Validated Source Cache

| Criterion | Score | Justification |
|-----------|-------|---------------|
| Architectural clarity | 5 | Clear health state machine, scoring formula documented |
| Migration safety | 5 | New tables only, optional integration |
| SQLite realism | 4 | Check logging could cause write amplification; batch strategy mitigates |
| Testability | 4 | HTTP mocking required; state machine has many paths |
| Future readiness | 5 | Extensible for rate limit detection, geo-routing |

**Overall: 4.6** — Batching strategy is critical for SQLite health.

#### Module 4: Canonical Jobs Pipeline

| Criterion | Score | Justification |
|-----------|-------|---------------|
| Architectural clarity | 4 | Two-tier model is sound but merge logic complexity is high |
| Migration safety | 4 | Coexistence period requires careful dual-write |
| SQLite realism | 4 | Moderate write volume; transactions needed for consistency |
| Testability | 4 | Merge logic has many branches; needs extensive fixtures |
| Future readiness | 4 | Job versioning in V2 may require schema changes |

**Overall: 4.0** — Most complex module; merge logic needs careful implementation.

**Justification for scores <4:**
- Merge logic complexity increases bug risk
- Dual-write coexistence requires discipline to avoid drift

#### Module 5: Application Tracker

| Criterion | Score | Justification |
|-----------|-------|---------------|
| Architectural clarity | 5 | Clean separation of concerns, clear ownership model |
| Migration safety | 5 | New tables, graceful degradation to legacy_job_id |
| SQLite realism | 5 | Low write volume, user-driven pace |
| Testability | 5 | Status state machine is well-defined |
| Future readiness | 4 | Auto-apply events will need event log extension |

**Overall: 4.8** — Clean module; auto-apply is V2+ concern.

### Summary Table

| Module | Arch | Migration | SQLite | Test | Future | Average |
|--------|------|-----------|--------|------|--------|---------|
| M1: Company Registry | 5 | 5 | 4 | 5 | 4 | **4.6** |
| M2: Search Expansion | 5 | 5 | 5 | 5 | 4 | **4.8** |
| M3: Source Cache | 5 | 5 | 4 | 4 | 5 | **4.6** |
| M4: Canonical Pipeline | 4 | 4 | 4 | 4 | 4 | **4.0** |
| M5: Application Tracker | 5 | 5 | 5 | 5 | 4 | **4.8** |

### Risk Summary

**Highest Risk Module:** M4 (Canonical Jobs Pipeline)
- Complexity in merge logic
- Dual-write coexistence period
- Most likely to have subtle bugs

**Mitigation:**
- Extensive test fixtures for merge scenarios
- Feature flag for canonical_jobs usage
- Extended coexistence period (6+ weeks)
- Manual merge/split API for corrections

---

## Appendix A: Quick Reference Commands

```bash
# Development
make dev                    # Start backend + frontend
make test                   # Run all tests
make test-unit              # Unit tests only
make test-integration       # Integration tests only
make seed-dev               # Seed development data

# Database
make db-migrate             # Run migrations
make db-backup              # Create backup
make db-restore             # Restore from backup
sqlite3 data/jobradar.db    # Direct DB access

# Maintenance
make maintenance-daily      # Run daily maintenance
make maintenance-weekly     # Run weekly maintenance
make vacuum                 # Reclaim database space

# Debugging
make logs                   # Tail application logs
make metrics                # View current metrics
curl localhost:8000/health  # Health check
```

---

## Appendix B: File Impact Summary

### New Files to Create

```
backend/
├── services/
│   ├── company_service.py      # M1
│   ├── expansion_service.py    # M2
│   ├── source_service.py       # M3
│   ├── canonical_service.py    # M4
│   └── application_service.py  # M5
├── routers/
│   ├── companies.py            # M1
│   ├── expansion.py            # M2 (or extend search.py)
│   ├── sources.py              # M3
│   ├── canonical.py            # M4
│   └── applications.py         # M5
├── models/
│   ├── company.py              # M1
│   ├── expansion.py            # M2
│   ├── source.py               # M3
│   ├── canonical.py            # M4
│   └── application.py          # M5
└── migrations/
    ├── 001_companies.py
    ├── 002_expansion.py
    ├── 003_sources.py
    ├── 004_canonical.py
    └── 005_applications.py

tests/
├── unit/
│   ├── test_company_registry.py
│   ├── test_search_expansion.py
│   ├── test_source_cache.py
│   ├── test_canonical_pipeline.py
│   └── test_application_tracker.py
├── integration/
│   ├── test_company_api.py
│   ├── test_expansion_api.py
│   ├── test_source_api.py
│   ├── test_canonical_api.py
│   └── test_application_api.py
├── e2e/
│   └── test_full_flow.py
└── fixtures/
    ├── golden_dataset.py
    └── factories.py
```

### Files to Modify

```
backend/
├── models.py              # Add imports for new models
├── database.py            # Add table creation
├── main.py                # Register new routers
├── scheduler.py           # Add maintenance jobs
└── scrapers/
    └── base.py            # Integrate source cache

frontend/
└── src/
    ├── api/client.ts      # Add new API methods
    └── pages/
        └── Pipeline.tsx   # Connect to applications API
```

---

*Document Version: 1.0*  
*Last Updated: March 10, 2026*  
*Companion to: JobRadar Phase 7A Core Architecture Package*
