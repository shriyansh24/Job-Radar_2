# Playbook: Incident Debug

Chain of personas and capabilities for structured incident investigation.

## Steps

| # | Phase | Persona / Capability | Canonical path | What to do |
|---|-------|---------------------|----------------|------------|
| 1 | Scope | Planner | `core/personas/planner` | Define the symptom, affected area, and investigation plan |
| 2 | Investigate | Researcher | `core/personas/researcher` | Trace the root cause through logs, code, and state |
| 3 | Fix | Coder | `core/personas/coder` | Implement the fix following the investigation findings |
| 4 | Review | Reviewer | `core/personas/reviewer` | Verify fix correctness and check for related issues |
| 5 | Gate | Quality Gate | `quality/gate` | Run quality checks: tests pass, no regressions, security OK |

## When to use

- Production incidents or critical bugs
- Failures with unclear root cause
- Issues that span multiple modules or services

## When NOT to use

- Obvious single-line bugs (use `quick-fix` workflow)
- Feature requests (use `plan-implement-review` workflow)

## Handoff

Provide to Step 1: error message/stack trace, reproduction steps, affected environment.
