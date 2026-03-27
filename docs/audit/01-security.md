# Security Audit - JobRadar V2

## SEC-01 - CRITICAL: Live API Keys in `.env`
- **File:** `backend/.env`
- **Detail:** Verified clean. The repository does not track `.env` secrets in this clone; only `.env.example` is present in Git.
- **Fix:** Keep secrets out of Git and build contexts, and use placeholders or secret managers for shared environments.
- **Status:** VERIFIED_CLEAN

## SEC-02 - CRITICAL: JWT Tokens in localStorage
- **Files:** `frontend/src/api/client.ts`, `frontend/src/store/useAuthStore.ts`, `backend/app/auth/router.py`, `backend/app/dependencies.py`
- **Detail:** Fixed. The frontend no longer stores access or refresh tokens in `localStorage`. Login/refresh now set httpOnly cookies, authenticated requests use cookies, and 401 recovery refreshes through the cookie flow.
- **Evidence:** `backend/tests/integration/test_auth_api.py`
- **Status:** FIXED

## SEC-03 - CRITICAL: Default Secret Key Not Blocked
- **Files:** `backend/app/config.py`, `backend/app/main.py`
- **Detail:** Fixed. The backend now aborts startup when `JR_SECRET_KEY` is still the default and `JR_DEBUG` is false.
- **Evidence:** `backend/tests/infra/test_runtime_config.py`
- **Status:** FIXED

## SEC-04 - HIGH: Overpermissive CORS
- **File:** `backend/app/main.py`
- **Detail:** Fixed. CORS methods and headers are now explicitly scoped through `settings.cors_methods` and `settings.cors_headers` instead of using `["*"]`.
- **Evidence:** `backend/app/main.py`
- **Status:** FIXED

## SEC-05 - HIGH: Missing Security Headers
- **Files:** `backend/app/shared/middleware.py`, `frontend/Dockerfile`
- **Detail:** Fixed. API responses now include security headers through middleware, and the frontend nginx config now emits matching headers for static assets.
- **Evidence:** `backend/tests/integration/test_auth_api.py`, `frontend/Dockerfile`
- **Status:** FIXED

## SEC-06 - MEDIUM: No Token Revocation
- **Files:** `backend/app/auth/models.py`, `backend/app/auth/service.py`, `backend/app/auth/router.py`, `backend/app/dependencies.py`
- **Detail:** Fixed. Tokens now carry a version claim, users store `token_version`, logout increments that version, and auth checks reject revoked bearer or cookie tokens.
- **Evidence:** `backend/tests/integration/test_auth_api.py`, `backend/tests/unit/auth/test_auth_service.py`
- **Status:** FIXED

## SEC-07 - MEDIUM: No API Rate Limiting
- **Files:** `backend/app/shared/middleware.py`, `backend/app/main.py`
- **Detail:** Fixed. API routes now pass through a rate-limiting middleware, with a tighter bucket for login attempts and standard rate-limit headers on successful requests.
- **Evidence:** `backend/tests/integration/test_auth_api.py`
- **Status:** FIXED
