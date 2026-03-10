# Quality Gate

Final evaluation gate applied before delivering a result. Aggregates checks
from specialized quality capabilities and produces a pass/fail verdict.

---

## Referenced Capabilities

| Capability | Canonical path | id | When to invoke |
|------------|----------------|----|----------------|
| Agent Evaluation | `quality/agent-evaluation` | `quality.agent-evaluation` | When output is an agent or agent config |
| Code Review | `quality/code-review` | `quality.code-review` | When output includes code changes |
| Security Audit | `quality/security-audit` | `quality.security-audit` | When changes touch auth, secrets, user data, or network |

## Required Checks (MUST)

These checks must pass for the gate to pass:

| # | Check | How |
|---|-------|-----|
| 1 | **Tests pass** | Run the project test suite; zero failures |
| 2 | **No regressions** | Existing tests still pass after changes |
| 3 | **Lint / type-check clean** | No new errors introduced |
| 4 | **Review performed** | At least one review pass (self-review minimum) |

## Recommended Checks (SHOULD)

These checks are strongly recommended but not blocking:

| # | Check | How |
|---|-------|-----|
| 5 | **Security scan** | Invoke `quality/security-audit` for sensitive changes |
| 6 | **Coverage delta** | New code has test coverage; net coverage does not decrease |
| 7 | **Documentation updated** | README / API docs reflect changes |
| 8 | **Performance check** | No obvious O(n^2) or unbounded memory patterns introduced |

## Output Format

```
## Quality Gate Result

**Verdict:** PASS | FAIL
**Timestamp:** <iso-8601>

### Checks
- [x] Tests pass
- [x] No regressions
- [x] Lint clean
- [x] Review performed
- [ ] Security scan (skipped: no sensitive changes)
- [x] Coverage delta OK

### Issues Found
(none)

### Remediation Required
(none)
```

## When to Run

- **Default:** Before the final deliverable in `plan-implement-review` (after Step 4: Test)
- **Required:** For security-sensitive changes, incident fixes, and production deployments
- **Optional:** For documentation-only changes and exploratory spikes

## Failure Handling

If the gate fails:

1. Identify which checks failed from the output
2. Return to the appropriate workflow step (usually Implement or Test)
3. Fix the issues
4. Re-run the gate
5. Do not deliver until the gate passes
