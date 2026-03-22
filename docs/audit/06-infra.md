# Infrastructure Audit - JobRadar V2

## INF-01 - HIGH: No `.dockerignore`
- **Files:** `backend/.dockerignore`, `frontend/.dockerignore`
- **Detail:** Fixed. Both Docker build contexts now exclude local secrets, tests, caches, and other non-runtime files.
- **Evidence:** `backend/.dockerignore`, `frontend/.dockerignore`
- **Status:** FIXED

## INF-02 - MEDIUM: No Docker Health Checks
- **File:** `docker-compose.yml`
- **Detail:** Fixed. Backend, frontend, and Redis now all expose health checks, and startup dependencies wait for healthy upstream services.
- **Evidence:** `docker compose config`
- **Status:** FIXED

## INF-03 - MEDIUM: No Redis Auth or TLS
- **Files:** `docker-compose.yml`, `backend/app/config.py`
- **Detail:** Fixed. Redis now runs with `--requirepass`, backend defaults no longer point at unauthenticated Redis, and the compose service supports TLS automatically when certs are mounted under `infra/redis/tls`.
- **Evidence:** `docker compose config`, `backend/app/config.py`
- **Status:** FIXED

## INF-04 - LOW: No CI Security Scanning
- **Files:** `.github/workflows/codeql.yml`, `.github/workflows/dependency-review.yml`, `.github/dependabot.yml`
- **Detail:** Fixed. The repo now includes SAST and dependency review workflows plus Dependabot configuration.
- **Evidence:** `.github/workflows/codeql.yml`, `.github/workflows/dependency-review.yml`, `.github/dependabot.yml`
- **Status:** FIXED

## INF-05 - LOW: Orphaned Config Keys
- **File:** `backend/app/config.py`
- **Detail:** Fixed. The truly unused ScrapingBee and Scrapling flags were removed from `Settings`, and legacy local env files are tolerated through `extra="ignore"` during cleanup.
- **Evidence:** `backend/tests/unit/test_config.py`, `backend/app/config.py`
- **Status:** FIXED

## Verified Fixes Since Initial Audit

## INF-F01 - FIXED: Backend Test Environment Was Not Reproducible via `uv run pytest`
- **Files:** `backend/pyproject.toml`, `backend/uv.lock`
- **Detail:** Test tooling now lives in uv's `dev` dependency group and incompatible optional scraper integrations are declared as conflicts, so `uv run pytest` resolves and runs cleanly.
- **Evidence:** `uv run pytest`
- **Status:** FIXED
