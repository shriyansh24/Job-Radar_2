# Entrypoint: Quick Fix Workflow

> Canonical skill: `workflows/quick-fix`
> Canonical id: `workflows.quick-fix`

## What this workflow does

- Fast-path for single-file bug fixes and trivial changes
- Light planning (3 bullets), implement, quick review, optional smoke test
- Minimal overhead for changes with obvious root cause

## When to use

- Bug fix confined to 1-2 files with clear root cause
- Typo fixes, config changes, small refactors
- Changes where the fix is obvious from the error message

## When NOT to use

- Multi-file features (use `plan-implement-review`)
- Unclear root cause (use `research-summarize-decide` first)

## Handoff

Provide: task description, file path(s), and any constraints.

## Full definition

See **workflows/quick-fix/SKILL.md** for the complete workflow.
