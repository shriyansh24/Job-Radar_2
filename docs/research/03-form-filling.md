# Auto-Apply & Form Filling — Technical Design

> Full research output from form filling agent.

## How Existing Tools Work

| Tool | Approach | Limitation |
|------|----------|------------|
| Simplify.jobs | Browser extension, DOM injection | Breaks on ATS DOM updates |
| LazyApply | Cloud Selenium, bulk apply | Gets flagged, low quality |
| Sonara.ai | Cloud headless + AI matching | Data leaves user's machine |
| Massive (YC) | API-first + browser fallback | Maintains ATS adapters |
| LinkedIn EasyApply | First-party integration | Simple forms only |

**Key insight**: Most open-source tools only handle LinkedIn Easy Apply. Workday/iCIMS are where the real difficulty and value lies.

## Architecture

```
DETECT ATS → EXTRACT FIELDS → MAP TO PROFILE → FILL FORM → REVIEW → SUBMIT
   (URL/DOM)    (A11y tree)     (KB + LLM)      (Playwright)  (human)   (confirmed)
```

## Form Extraction: Accessibility Tree First

**Why a11y tree over DOM parsing:**
- Pierces Workday's shadow DOM
- Handles iCIMS iframes
- Provides semantic labels (what the field IS, not just HTML)
- Consistent across ATS platforms
- Playwright's `page.accessibility.snapshot()` does this natively

## Three-Tier Field Mapping

| Tier | Method | Speed | When |
|------|--------|-------|------|
| 1 | Static regex patterns (120+ rules) | <1ms | Known field labels |
| 2 | Knowledge base lookup (learned from past forms) | ~5ms | Previously seen fields |
| 3 | Local LLM classification (Qwen3-4B) | ~2s | Unknown/custom fields |

### Static Pattern Examples
```
"first name" → profile.first_name
"authorized to work" → profile.work_authorization
"salary expectation" → profile.salary_expectation
"why do you want to work" → LLM-generated (motivation_letter strategy)
"gender/race/ethnicity" → "Prefer not to answer" (EEOC, always skip)
```

## ATS-Specific Adapters (Build Order)

### Tier 1 — Reliable (build first)
1. **Lever API** — `POST /v0/postings/{id}/apply` — PUBLIC, no browser needed!
2. **Greenhouse** — Predictable DOM, consistent field IDs (#first_name, #last_name)
3. **SmartRecruiters** — Clean HTML, standard elements

### Tier 2 — Feasible
4. **Lever browser** (fallback when API fails)
5. **Jobvite** — Simpler forms, some iframe challenges
6. **Custom HTML forms** — Generic extractor

### Tier 3 — Hard (build last)
7. **Workday** — Shadow DOM (`data-automation-id` selectors), multi-step wizards, account creation
8. **iCIMS** — Nested iframes, inconsistent implementations

## Anti-Detection Strategy

1. **Headed mode** (not headless) — #1 anti-detection strategy
2. Persistent browser profile with real history/cookies
3. Human-like delays (50-200ms randomized between actions)
4. Natural mouse movement (Bezier curves)
5. Type character by character with delays (not instant fill)

## Safety Layer (Non-Negotiable)

- **Never auto-submit** — screenshot + summary → user confirms every time
- Rate limiter: max N applications/day (default 25)
- Company blacklist
- Duplicate application detection (by job ID, URL, and company+title fuzzy match)
- CAPTCHA: pause automation, let user solve manually
- Min match score threshold (default 60%)
- Stale posting filter (>30 days old = skip)

## Wizard Handling (Workday/iCIMS)

- Checkpoint after each successful page (SQLite)
- Resume from last checkpoint on failure
- Max 15 pages safety limit
- "Next"/"Continue" button detection via text + role matching

## Knowledge Base Schema

```
ATSFormTemplate — stored form structures per ATS/company
FieldMappingRule — learned label→profile mappings with confidence
CustomQuestionAnswer — reusable answers to custom questions
ApplicationAttempt — every attempt tracked for learning
```

## Browser Stack

| Tool | Role |
|------|------|
| Playwright (Python async) | Primary — best form filling API |
| Crawlee-Python | Framework layer — fingerprint rotation, crash recovery |
| Camoufox | Maximum stealth fallback (Firefox) |
| nodriver | Chrome anti-detection fallback |
