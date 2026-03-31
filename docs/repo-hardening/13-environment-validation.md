# Environment Validation Runbook

## Purpose
Provide one canonical operational runbook for the validation work that cannot be reduced to deterministic in-repo tests alone:
- provider-backed ATS submission flows
- seeded-data-heavy PDF fidelity checks
- source-specific parser/render/anti-bot recovery on difficult career pages

This document exists so those concerns are treated as explicit operational validation work, not hand-waved as missing repo implementation.

## Source-Of-Truth Status
- Status: `DOCUMENTED_OPERATIONAL_RUNBOOK`
- Scope: environment-specific validation and classification work that sits on top of the repo-local test suite
- Last validation basis: current runtime/docs alignment, committed parser diagnostics, provider adapter coverage, and local browser validation on `2026-03-31`

## What The Repo Already Owns
- Provider-backed ATS adapters and API/service coverage for Greenhouse, Lever, and Workday
- Review-first auto-apply execution with persisted run diagnostics
- Resume preview/export coverage plus template preview browser checks
- Adaptive parser diagnostics that distinguish selector, JSON-LD, embedded-state, JS-shell, and Cloudflare-challenge outcomes
- Admin runtime visibility for queue state, recent queue samples, queue alerts, and auth audit events

These items are already in repo scope. This runbook covers the validation that still depends on live providers, deployment shape, or operator-owned data.

## When To Use This Runbook
- A real provider-backed submission flow must be exercised against a live ATS tenant or test job
- A resume template or export change must be checked against seeded or unusually long data
- A difficult source fails scraping and you need to determine whether the problem is parser logic, render timing, or anti-bot behavior

## Provider-Backed ATS Validation

### Scope
- Greenhouse
- Lever
- Workday

### Preconditions
- Use non-production or low-risk application targets where possible
- Use explicit operator-owned credentials and never check them into the repo
- Confirm the backend DB is at Alembic `head`
- Confirm scheduler + `worker-ops` are healthy if the run path uses queued execution

### Evidence To Capture
- job or target identifier
- adapter/provider name
- run identifier
- review state or block reason
- screenshots or Playwright recording when UI interaction matters
- exact failure reason if the provider blocks or changes schema

Write screenshots or recordings to `.claude/ui-captures/` when the validation is browser-driven.

### Success Criteria
- detection chooses the intended adapter
- form extraction produces a meaningful schema
- field mapping is explainable
- safety gating does not silently skip required review
- unsupported, CAPTCHA, or unseen-question cases surface explicit human-actionable reasons
- final state is truthful: success, blocked, review-required, or failed

### Failure Classification
- `ADAPTER_REGRESSION`: deterministic adapter behavior changed and should be fixed in repo code
- `PROVIDER_SCHEMA_DRIFT`: live provider page/API changed and adapter follow-through is needed
- `CAPTCHA_OR_BLOCK`: provider-side block or challenge, not a fake application success
- `ENVIRONMENT_ONLY`: local/deployment credentials, browser, or network conditions prevented validation

## PDF Fidelity Validation

### Scope
- HTML preview vs backend PDF export
- long resumes
- dense bullet lists
- multi-section resumes
- template-specific typography/layout regressions

### Preconditions
- validate against at least one short resume and one long seeded resume
- run the existing preview/export browser path first
- use the same template in preview and export comparison

### Evidence To Capture
- template name
- preview screenshot
- exported PDF artifact
- mismatch category
- whether the issue reproduces deterministically

### Failure Classification
- `TEMPLATE_REGRESSION`: CSS/layout bug in repo-owned template code
- `WEASYPRINT_RENDERING_LIMIT`: renderer-specific behavior that may need template adaptation
- `SEEDED_DATA_EDGE_CASE`: unusually long or malformed content that reveals a formatting boundary
- `ENVIRONMENT_ONLY`: local font/package/runtime mismatch

## Parser / Source Recovery

### Start With The Existing Diagnostic Classes
- `selector`
- `json_ld`
- `embedded_state`
- `js_shell`
- `cloudflare_challenge`

Use the existing deterministic parser diagnostics first. Do not start with speculative anti-bot changes.

### Triage Order
1. Confirm the source reproduces in the current fixture or live run.
2. Determine which diagnostic class it belongs to.
3. Only treat it as a parser bug when structured data or selectors should have been usable but failed.
4. Treat JS-shell and Cloudflare-style outcomes as render or anti-bot work unless deterministic parser evidence proves otherwise.

### Failure Classification
- `PARSER_REGRESSION`
- `RENDER_TIMING`
- `ANTI_BOT_BLOCK`
- `SOURCE_MARKUP_DRIFT`
- `PROVIDER_LIMITATION`

### Expected Outputs
- one classification
- one concrete next action
- one evidence artifact: fixture update, log extract, screenshot, or trace

## Related Files
- `backend/app/auto_apply/`
- `backend/app/scraping/`
- `backend/tests/unit/scraping/test_adaptive_parser_diagnostics.py`
- `backend/tests/integration/auto_apply/test_auto_apply_api.py`
- `frontend/e2e/flows/resume-template-preview.spec.ts`
- `docs/current-state/04-data-and-scraping.md`
- `docs/current-state/06-open-items.md`
- `docs/repo-hardening/09-final-gap-report.md`

## What This Runbook Does Not Claim
- It does not make provider-backed ATS behavior deterministic across all live tenants.
- It does not eliminate anti-bot escalation on difficult sites.
- It does not guarantee pixel-perfect PDF output for every possible seed dataset.

It turns those concerns into explicit, evidence-capturing operational work instead of undocumented ambiguity.
