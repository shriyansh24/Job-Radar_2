# Playbook: Repo Refactor

Chain of personas and capabilities for a structured codebase refactoring.

## Steps

| # | Phase | Persona / Capability | Canonical path | What to do |
|---|-------|---------------------|----------------|------------|
| 1 | Plan | Planner | `core/personas/planner` | Scope the refactor: identify affected files, define constraints, estimate risk |
| 2 | Implement | Coder | `core/personas/coder` | Execute the refactoring plan; run lint/type-check after each batch |
| 3 | Review | Reviewer | `core/personas/reviewer` | Verify behavior preservation, check for regressions, review naming |
| 4 | Test | Tester | `core/personas/tester` | Run existing tests; add regression tests for changed code paths |
| 5 | Wrap-up | Wrap-up | `utilities/wrap-up` | Summarize changes, capture learnings, draft commit message |

## When to use

- Renaming, restructuring, or reorganizing modules
- Extracting shared code into libraries or utilities
- Migrating from one pattern to another (e.g., callbacks to async/await)

## When NOT to use

- Adding new features (use `plan-implement-review` workflow instead)
- Exploratory investigation (use `research-summarize-decide`)

## Handoff

Provide to Step 1: scope description, files/modules in play, constraints (backward compat, etc).
