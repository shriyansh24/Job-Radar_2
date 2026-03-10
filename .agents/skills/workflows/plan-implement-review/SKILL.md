# Workflow: Plan → Implement → Review

The default engineering workflow for structured feature development.

---

## A. Purpose

Ensure every non-trivial change goes through planning, implementation, review,
testing, and wrap-up -- with explicit handoffs and quality gates between phases.

## B. Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Task description | yes | What needs to be built or fixed |
| Repo context | yes | Codebase structure, relevant files, existing patterns |
| Constraints | no | Deadlines, tech restrictions, scope limits |
| Acceptance criteria | no | Specific conditions that define "done" |

## C. Outputs

| Phase | Output |
|-------|--------|
| Plan | Ordered step list, files to touch, risks, open questions |
| Implement | Code changes, inline comments on non-obvious decisions |
| Review | Review notes: issues found, suggestions, approval/rejection |
| Test | Test results: pass/fail, coverage delta, edge cases verified |
| Wrap-up | Session summary, learnings captured, commit message |

## D. Steps

### Step 1: Plan

**Persona:** Planner (`core/personas/planner`, id: `core.persona.planner`)

1. Read the task description and gather repo context
2. Identify all files that need changes
3. Produce an ordered step plan with dependencies
4. Flag risks, unknowns, and open questions
5. Present the plan for approval -- do not proceed without explicit "go"

**Gate:** Plan must be approved before moving to Step 2.

### Step 2: Implement

**Persona:** Coder (`core/personas/coder`, id: `core.persona.coder`)

1. Execute the plan step by step
2. Follow existing codebase patterns and conventions
3. Run lint / type-check after each batch of 5 edits
4. Leave comments on non-obvious decisions
5. Stop and re-plan if the plan proves infeasible

**Gate:** All planned changes complete. Lint and type-check pass.

### Step 3: Review

**Persona:** Reviewer (`core/personas/reviewer`, id: `core.persona.reviewer`)

1. Review all changes for correctness and security
2. Check for missing error handling and edge cases
3. Verify architectural consistency
4. Produce a review summary with line-specific feedback
5. Approve, request changes, or reject

**Gate:** Reviewer approval. If changes requested, return to Step 2.

**Optional quality capabilities:**
- Code review: `quality/code-review`
- Security audit: `quality/security-audit`

### Step 4: Test

**Persona:** Tester (`core/personas/tester`, id: `core.persona.tester`)

1. Write or update tests covering all changed code paths
2. Run the full test suite
3. Verify edge cases identified during review
4. Report pass/fail with coverage summary

**Gate:** Tests pass. No regressions.

### Step 5: Wrap-up

**Utility:** Wrap-up (`utilities/wrap-up`, id: `utilities.wrap-up`)

1. Summarize what was done and why
2. Capture any learnings or patterns discovered
3. Draft a commit message
4. Note any follow-up tasks

## E. Handoff Format

Between each step, the outgoing phase produces a structured handoff:

```
## Handoff: <Phase> → <Next Phase>

**Status:** complete | blocked | needs-revision
**Summary:** 1-2 sentences on what was done
**Artifacts:** list of files changed / created
**Open items:** anything the next phase needs to address
**Blockers:** anything preventing progress (empty if none)
```

## F. Failure Modes

| Failure | Response |
|---------|----------|
| Unclear requirements | Return to Step 1. Ask clarifying questions before re-planning. |
| Plan proves infeasible during implementation | Pause Step 2. Revise plan in Step 1 with new constraints. |
| Reviewer rejects changes | Return to Step 2 with review feedback. Do not skip review. |
| Tests fail | Fix in Step 2, then re-run Step 3 (review) and Step 4 (test). |
| Missing test infrastructure | Note as a blocker in handoff. Implement test setup first. |

## G. Example Run

```
Task: "Add rate limiting to the /api/jobs endpoint"

Step 1 — Plan (Planner):
  - Add rate limit middleware to backend/routers/jobs.py
  - Add config for rate limit window + max requests to backend/config.py
  - Add tests in tests/test_rate_limit.py
  - Risk: need to decide between in-memory vs Redis backend
  → Approved

Step 2 — Implement (Coder):
  - Created rate_limit.py middleware (token bucket, in-memory)
  - Wired into jobs router
  - Added RATE_LIMIT_WINDOW and RATE_LIMIT_MAX to config
  - Lint + type-check pass
  → Handoff to review

Step 3 — Review (Reviewer):
  - Approved with one suggestion: add X-RateLimit-Remaining header
  → Minor revision requested

Step 2b — Implement revision (Coder):
  - Added rate limit headers to response
  → Handoff to review

Step 3b — Review (Reviewer):
  - Approved

Step 4 — Test (Tester):
  - 4 tests written: under limit, at limit, over limit, window reset
  - All pass
  → Handoff to wrap-up

Step 5 — Wrap-up:
  - Commit: "feat: add token-bucket rate limiting to /api/jobs"
  - Learning: in-memory rate limiting is sufficient for single-process localhost
  - Follow-up: consider Redis adapter if multi-process deployment needed
```
