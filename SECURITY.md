# Security Policy

## Reporting A Vulnerability

- Do not open a public GitHub issue for a suspected security vulnerability.
- Prefer GitHub's private vulnerability reporting flow for this repository.
- If private reporting is unavailable, contact the repository maintainer directly through GitHub and include:
  - affected component or endpoint
  - reproduction steps
  - impact assessment
  - any suggested mitigation

## What To Include

- repository version, branch, or commit SHA
- environment details needed to reproduce
- whether the issue requires authentication or special configuration
- proof-of-concept requests, payloads, or logs with secrets redacted

## Response Expectations

- Reports will be triaged privately.
- Sensitive fixes should remain non-public until a patch is ready.
- Once resolved, public documentation can be updated without publishing exploit details.

## Repository Security Controls
- GitHub Actions run backend dependency audit, Bandit, Ruff, targeted mypy, pytest, frontend `npm audit`, frontend lint, frontend tests/build, CodeQL, dependency review, docs validation, and migration replay checks.
- Dependabot is enabled for GitHub Actions, `frontend/package.json`, and `backend/pyproject.toml` dependencies.
- Secrets and machine-local files are excluded through `.gitignore`; do not commit `.env`, browser session artifacts, or machine-local `.claude` files.

## Current Security Boundaries And Known Gaps
- Backend auth is cookie-capable and also accepts bearer tokens; cookies are `HttpOnly`, `SameSite=Lax`, and `secure` is environment-driven through backend settings.
- The backend sets security headers in middleware, including CSP, `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`.
- Current hardening gap: the repo does not yet implement a dedicated CSRF token flow for cookie-authenticated state-changing requests. Track this as a hardening item rather than assuming SameSite alone is sufficient.
- Current hardening gap: trusted-host enforcement is not yet explicit in the FastAPI middleware stack.

## Scope Limits
- This repository does not assume GitHub Advanced Security features beyond the workflows and settings visible in the repo itself.
- If GitHub secret scanning or push protection are available on the plan, treat them as helpful extra controls, not as a substitute for local secret hygiene and review discipline.
