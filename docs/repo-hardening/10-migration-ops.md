# Migration Operations

## Purpose
This file is the canonical migration operations runbook for the repository hardening program.

Use it for:
- migration authoring expectations
- clean replay procedure
- rollback stance
- backfill guidance
- validation expectations for migration-bearing changes

Do not use this file as the live product-state source of truth. Runtime behavior and CI lane names still live in:
- `docs/current-state/05-ops-and-ci.md`
- `docs/repo-hardening/00-index.md`

## Current Migration Shape
The active Alembic tree lives under:
- `backend/app/migrations/versions`

The revision set currently includes:
- base schema setup: `001`, `002`, `003`
- scrape-target and lifecycle lineage: `aaba1d3f957f`, `503ca7a300d9`, `45613a5a2f78`, `e5d40ea7c9db`
- repo-hardening and consolidation lineage:
  - `20260321_db_audit_fixes`
  - `004`
  - `20260323_networking`
  - `20260323_archetypes`
  - `20260323_create_dedup_feedback`
  - `20260323_form_learning`
  - `7021f28ab5e0`
  - `005`
  - `20260323_integration_secrets`

Important operational characteristics:
- `7021f28ab5e0` is a merge-head revision and carries no schema body.
- `005` is a consolidation migration that creates multiple branch-era tables idempotently.
- `20260321_db_audit_fixes` rewires foreign keys and indexes and should be treated as structurally sensitive.
- `002` has the only explicitly targeted downgrade test in the current test suite.
- The ATS identity lineage in this repo is currently represented by the `scrape_targets` contract rather than a dedicated identity table:
  - `aaba1d3f957f` introduces `scrape_targets.ats_vendor` and `scrape_targets.ats_board_token`
  - `45613a5a2f78` links `jobs.source_target_id` back to `scrape_targets`
  - this means ATS identity integrity depends on both the target table migration and the later job-link migration remaining aligned

## Replay Procedure
Replay is the primary safety contract for this repo.

Required expectation:
- every migration-bearing change must replay cleanly from an empty Postgres database to `head`

Local replay:

```powershell
cd D:\jobradar-v2\backend
uv sync --frozen
uv run alembic upgrade head
```

To inspect current state after replay:

```powershell
cd D:\jobradar-v2\backend
uv run alembic heads
uv run alembic current
```

CI replay lane:
- `.github/workflows/migration-safety.yml`
- required emitted check name remains `Migration Safety / Alembic replay on clean Postgres`

## Rollback Stance
This repo does not assume that every migration is operationally safe to downgrade in production.

Default stance:
- prefer forward fixes over ad hoc downgrades
- use clean replay as the merge gate
- treat rollback as a deliberate operator action, not an automatic recovery path

What that means in practice:
- simple schema additions can carry reversible downgrades when cheap and obvious
- merge-head revisions like `7021f28ab5e0` are metadata-only and not rollback-sensitive by themselves
- consolidation and data-shaping revisions like `005` should be treated as non-routine to downgrade
- foreign-key and integrity rewrites like `20260321_db_audit_fixes` should only be downgraded with explicit review

If a migration cannot be safely downgraded:
- say so in the revision docstring or PR description
- provide the forward-fix path
- document the restore expectation if rollback would require database restore instead of Alembic downgrade

## Backfill Guidance
Separate schema creation from large or risky data movement whenever practical.

When a revision performs data movement:
- make the data transformation explicit in the file docstring
- state whether it is idempotent
- state whether it is online-safe
- state whether it is expected to run inside normal deploy time

For this tree:
- `backend/app/migrations/versions/e5d40ea7c9db_migrate_career_pages_to_scrape_targets_.py` is a data migration and should be treated as a model for explicit column mapping notes
- `backend/app/migrations/versions/005_create_p2_tables.py` is a consolidation migration and should remain idempotent-aware
- `backend/app/migrations/versions/aaba1d3f957f_create_scrape_targets_and_scrape_.py` carries the ATS identity surface for scrape targets and should not lose `ats_vendor`, `ats_board_token`, or the `idx_targets_ats` index without an explicit contract change
- `backend/app/migrations/versions/45613a5a2f78_add_job_lifecycle_columns_and_tier_.py` is part of the same identity story because it wires jobs back to scrape targets through `source_target_id`

Preferred backfill pattern:
1. add schema
2. deploy code that tolerates empty/new columns or tables
3. run bounded backfill or idempotent migration data step
4. only then add stricter constraints if needed

Avoid:
- hidden backfills with no runtime-cost note
- irreversible destructive drops bundled with first-pass schema creation
- migration files that depend on a developer's already-mutated local database state

## Validation Guidance
Minimum validation for migration-bearing changes:

```powershell
cd D:\jobradar-v2\backend
uv run alembic upgrade head
uv run pytest tests/migrations/
```

Recommended validation when the migration touches runtime-coupled areas:

```powershell
cd D:\jobradar-v2\backend
uv run pytest tests/infra/test_runtime_config.py
uv run pytest tests/workers/test_scheduler_runtime.py
```

Use broader backend tests when the migration changes tables consumed by auth, scraping, pipeline, or queue-backed worker flows.

For ATS identity changes specifically, expect the migration test package to cover:
- the target table columns `ats_vendor` and `ats_board_token`
- the `idx_targets_ats` index
- the `jobs.source_target_id` foreign-key linkage back to `scrape_targets`

## CI And Failure Handling
When the migration safety lane fails:
- inspect the uploaded `migration-safety-diagnostics` artifact
- check `alembic-heads.txt` for unexpected multi-head state
- check `alembic-current.txt` to see where replay stopped
- check `alembic-history.txt` to confirm the exact branch/merge ordering that led to failure

Do not treat CI failure as permission to stamp or skip revisions locally.

The expected recovery sequence is:
1. fix the migration chain or migration body
2. replay from clean Postgres again
3. rerun the targeted migration tests
4. only then merge

## Operator Rules
- Never rely on an already-upgraded local database as proof that a migration is valid.
- Never delete or rewrite committed revisions casually once other revisions depend on them.
- Prefer a merge-head revision or a follow-up corrective revision over history surgery.
- Keep required check names stable so branch protection does not drift.
