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
- The Secret Scan workflow runs Gitleaks against full fetched Git history on pushes and pull requests. Provider-specific rules cover ScrapingBee and SerpAPI configuration assignments alongside the default detectors. Its exceptions match only reviewed synthetic values in specific fixture paths.

## Credential Hygiene And History Cleanup

- Keep real provider keys in ignored local environment files or a deployment secret store. Example environment files must contain empty credentials or obvious placeholders.
- Revoke or rotate every exposed credential at its provider before reusing the integration; deleting a file or rewriting Git history cannot revoke a key.
- On 2026-10-06, exposed ScrapingBee, SerpAPI, and OpenRouter values were removed from repository history. Clones made before the cleanup must be cleaned or replaced before pushing. Do not merge old history into the rewritten branches.
- GitHub pull-request references and cached commit views can retain old objects after a force push. Follow GitHub's sensitive-data-removal process and contact GitHub Support when those objects require purging.
- Run `gitleaks git . --log-opts="--all" --config=.gitleaks.toml --redact=100` before publishing changes. Never include raw secrets in scan reports or support requests.

## Current Security Boundaries And Known Gaps
- Backend auth is cookie-capable and also accepts bearer tokens; cookies are `HttpOnly`, `SameSite=Lax`, and `secure` is environment-driven through backend settings.
- The backend sets security headers in middleware, including CSP, `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`.
- Cookie-authenticated unsafe requests now use a readable `jr_csrf_token` cookie and require the `X-CSRF-Token` header on the backend.
- Trusted-host enforcement is now explicit through FastAPI `TrustedHostMiddleware` and the validated `JR_TRUSTED_HOSTS` setting.

## Scope Limits
- This repository does not assume GitHub Advanced Security features beyond the workflows and settings visible in the repo itself.
- If GitHub secret scanning or push protection are available on the plan, treat them as helpful extra controls, not as a substitute for local secret hygiene and review discipline.
