# Workflow: Quick Fix

Fast path for small, low-risk changes where the root cause is obvious and
the fix is confined to one or two files.

---

## Purpose

Skip full planning overhead for trivial patches. Get from bug report to
committed fix in the fewest steps that still maintain quality.

## When to Use

- Single-file bug fix with obvious root cause
- Typo, config change, or small refactor
- Fix is clear from the error message or stack trace
- Change does not cross module boundaries

## When NOT to Use

- Root cause is unclear (use `research-summarize-decide` first)
- Fix touches 3+ files (escalate to `plan-implement-review`)
- Security-sensitive change (use `plan-implement-review` with quality gate)
- New feature work of any size

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Task description | yes | What is broken and expected behavior |
| File path(s) | yes | Where the problem lives (1-2 files) |
| Constraints | no | Backward compat, performance, etc. |

## Outputs

| Output | Description |
|--------|-------------|
| Patch | The minimal code change |
| Rationale | 1-2 sentences on why this fix is correct |
| Verification | Test result or reasoning if no test exists |

## Steps

### Step 1: Mini-Plan (light)

**Persona:** Planner (`core/personas/planner`, id: `core.persona.planner`)

Produce a micro-plan -- 3 bullets maximum:
1. What is the root cause
2. What is the fix
3. What could go wrong

No formal approval gate. If the plan reveals complexity, **escalate** to
`plan-implement-review` immediately.

### Step 2: Implement

**Persona:** Coder (`core/personas/coder`, id: `core.persona.coder`)

1. Apply the minimal change
2. Run lint / type-check
3. Keep the diff small -- resist scope creep

### Step 3: Quick Review (light)

**Persona:** Reviewer (`core/personas/reviewer`, id: `core.persona.reviewer`)

Light-touch review. Focus only on:
- Does the fix address the root cause?
- Are there obvious regressions?
- Is error handling adequate?

Skip style nits and broader refactoring suggestions.

### Step 4: Smoke Test (optional)

**Persona:** Tester (`core/personas/tester`, id: `core.persona.tester`)

If a test suite exists:
- Run the relevant tests
- Add a regression test if the bug was not previously covered

If no test suite:
- Document the manual verification performed
- Note "no automated test" in wrap-up

### Step 5: Wrap-up (short)

**Utility:** Wrap-up (`utilities/wrap-up`, id: `utilities.wrap-up`)

- One-line summary
- Commit message
- Flag any follow-up work discovered

## Handoff Format (mini)

```
## Quick Fix Handoff

**Root cause:** <1 sentence>
**Fix applied:** <file:line — what changed>
**Verified:** yes/no — <how>
**Follow-up:** <none | description>
```

## Failure Modes

| Failure | Response |
|---------|----------|
| Scope expands beyond 2 files | Stop. Escalate to `plan-implement-review`. |
| Root cause is unclear after Step 1 | Stop. Switch to `research-summarize-decide`. |
| Fix introduces a test failure | Fix the regression in Step 2, re-run Step 3-4. |
| No test infrastructure exists | Document manual verification; note tech debt. |

## Example Run

```
Task: "TypeError in /api/jobs when salary_min is None"

Step 1 — Mini-Plan (Planner):
  1. Root cause: salary_min compared with > without None check
  2. Fix: add `if salary_min is not None` guard in jobs.py:142
  3. Risk: low; only affects display filtering

Step 2 — Implement (Coder):
  - Added None guard at backend/routers/jobs.py:142
  - Lint passes

Step 3 — Quick Review (Reviewer):
  - Fix is correct; guard covers both salary_min and salary_max
  - No regressions

Step 4 — Smoke Test (Tester):
  - Existing test_jobs_filter passes
  - Added test_jobs_filter_null_salary — passes

Step 5 — Wrap-up:
  - Commit: "fix: guard against None salary in job filter comparison"
  - No follow-up needed
```
