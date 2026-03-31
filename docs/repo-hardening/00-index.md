# Repository Hardening Hub

## Purpose
This directory is the working audit trail for the repository hardening and state-alignment program.

It is not the live product-state source of truth. Live repo truth still lives in:
- `docs/current-state/`
- `docs/audit/`
- `docs/research/` for exploratory roadmap material

## Source-Of-Truth Status
- Status: `DOCUMENTED_WORKING_SET`
- Scope: repository normalization, runtime truth reconciliation, branch/phase traceability, test/CI hardening, and final gap disclosure
- Last validation basis: manual repo inspection plus local `git`, GitHub PR metadata via `gh`, frontend validation, and direct reads of runtime/config/docs files on `2026-03-27`

## Read Order
1. `01-evidence-ledger.md`
2. `02-execution-plan.md`
3. `03-runtime-truth-matrix.md`
4. `04-branch-disposition.md`
5. `05-implementation-traceability-matrix.md`
6. `06-test-taxonomy.md`
7. `07-observability-and-failure-map.md`
8. `08-change-rationale-log.md`
9. `09-final-gap-report.md`
10. `10-migration-ops.md`
11. `11-completion-gap-analysis.md`
12. `12-deployment-ops-runbook.md`
13. `13-environment-validation.md`

## What This Hub Must Produce
- A durable evidence ledger for repo contradictions and drift
- A concrete execution plan before structural edits
- A runtime truth crosswalk
- A branch and phase disposition trail
- Follow-on artifacts for test taxonomy, observability, implementation traceability, migration operations, and final gap reporting

## Ownership Convention
- Live behavior claims belong in `docs/current-state/`
- Bug claims belong in `docs/audit/`
- Exploratory roadmap claims belong in `docs/research/`
- Hardening-program artifacts belong here until promoted into the correct source-of-truth layer

## Current Status
- Phase 0 is complete: evidence collection and contradiction capture are on disk
- Phase 1 is complete: runtime/doc truth reconciliation, compose-first runtime alignment, and the first GitHub guardrail changes are landed
- Phase 2 is materially complete: the first test-taxonomy normalization batch, committed browser lane, and branch-protection-facing workflow names are now implemented in the filesystem, runners, and docs
- Phase 3 is active: selective capability recovery is proceeding in bounded slices rather than branch-wide merges, and the remaining runtime closure is now documented around the ARQ queue target (`scraping`, `analysis`, `ops`) instead of the older inline/subprocess-only story
- The merge-prep working set now also includes `10-migration-ops.md` for operator-facing schema guidance, `11-completion-gap-analysis.md` for the evidence-based closure delta that accompanies the final broad integration PR, `12-deployment-ops-runbook.md` for runtime history, alert routing, and restore guidance, and `13-environment-validation.md` for provider/PDF/source validation that cannot be reduced to deterministic repo-only tests
