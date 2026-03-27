# Change Rationale Log

## Purpose
Record why major repo-hardening decisions were made, what alternatives were rejected, and what risk remains.

## Source-Of-Truth Status
- Status: `DOCUMENTED_WORKING_SET`
- Scope: rationale for hardening-program changes
- Last validation basis: direct repo edits and evidence artifacts on `2026-03-27`

## Entries

### Compose-first runtime baseline
- Status: `FIXED`
- Changed because:
  - `.env.example`, `docker-compose.yml`, and backend config already agreed on the compose DB/Redis baseline
  - `CLAUDE.md` and older README text still described a manual-local `5433` path as if it were canonical
- Alternatives considered:
  - make the manual-local `5433` path canonical
- Why rejected:
  - it conflicts with the checked-in compose stack and backend defaults
- Files touched:
  - `.env.example`
  - `backend/app/config.py`
  - `README.md`
  - `CLAUDE.md`
  - `docs/current-state/05-ops-and-ci.md`
- Remaining risk:
  - developers who still use the legacy manual container path need it documented as an override, not removed from their heads

### Historical inventory demotion
- Status: `FIXED`
- Changed because:
  - `docs/system-inventory/13-open-questions.txt` and `14-implementation-readiness.txt` were being read as live truth even when `docs/current-state/*` contradicted them
- Alternatives considered:
  - rewrite the entire inventory set immediately
- Why rejected:
  - too large for the first truth-reconciliation batch; the urgent need was to stop stale inventory from masquerading as live truth
- Files touched:
  - `docs/system-inventory/13-open-questions.txt`
  - `docs/system-inventory/14-implementation-readiness.txt`
- Remaining risk:
  - the historical inventory still contains stale detail until it is either refreshed or explicitly archived

### Docs/path validation automation
- Status: `IMPLEMENTING`
- Changed because:
  - the repo already shipped real doc drift around missing paths and stale artifact references
- Alternatives considered:
  - rely on manual doc review
- Why rejected:
  - drift already happened repeatedly under manual review
- Files touched:
  - `scripts/check_docs_truth.py`
  - `.github/workflows/docs-validation.yml`
- Remaining risk:
  - the validator only checks repo-local path references and obvious links; it does not prove commands are executable

### Migration replay workflow
- Status: `IMPLEMENTING`
- Changed because:
  - the repo explicitly carries migration replay uncertainty in the docs, but CI had no clean-replay gate
- Alternatives considered:
  - leave replay safety to pytest only
- Why rejected:
  - unit tests do not replace a clean Alembic replay on Postgres
- Files touched:
  - `.github/workflows/migration-safety.yml`
- Remaining risk:
  - replay still needs broader rollback/backfill documentation beyond the basic upgrade check

### Purpose-driven test taxonomy
- Status: `IMPLEMENTING`
- Changed because:
  - frontend tests were split across `__tests__` pockets with little ownership signal
  - backend migration, infra, security, and worker suites were still living under generic `unit/` buckets
- Alternatives considered:
  - leave file placement alone and only document the intended taxonomy
- Why rejected:
  - the repo already had enough historical sprawl that a doc-only taxonomy would immediately drift from the filesystem
- Files touched:
  - `frontend/src/tests/**`
  - `backend/tests/{contracts,infra,migrations,security,workers}/**`
  - `frontend/vitest.config.ts`
  - `.github/workflows/migration-safety.yml`
  - `frontend/src/tests/README.md`
  - `backend/tests/README.md`
  - `docs/repo-hardening/06-test-taxonomy.md`
- Remaining risk:
  - several backend `unit/` and frontend page/component suites still need a second-pass split by behavior rather than route or historical grouping
