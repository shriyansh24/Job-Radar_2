# Frontend Audit - JobRadar V2

## FE-01 - HIGH: SSE Token in URL Parameter
- **File:** `frontend/src/hooks/useSSE.ts`
- **Detail:** Fixed. The SSE hook no longer appends the token to the URL and now relies on credentialed transport instead.
- **Evidence:** `frontend/src/hooks/useSSE.ts`
- **Status:** FIXED

## FE-02 - HIGH: Rebuild Embeddings Calls Wrong API
- **File:** `frontend/src/pages/Admin.tsx`
- **Detail:** Fixed. The misleading embeddings action was removed, so the admin page no longer claims to perform an embeddings rebuild through the unrelated reindex endpoint.
- **Evidence:** `frontend/src/tests/pages/Admin.page.test.tsx`
- **Status:** FIXED

## FE-03 - MEDIUM: Vault API Client is Still Partial
- **Files:** `frontend/src/api/vault.ts`, `frontend/src/pages/DocumentVault.tsx`
- **Detail:** Fixed. Resume and cover-letter PATCH flows now exist in the client and the document vault UI wires them through editable metadata forms.
- **Evidence:** `frontend/src/tests/pages/DocumentVault.page.test.tsx`
- **Status:** FIXED

## Verified Fixes Since Initial Audit

## FE-F01 - FIXED: TypeScript Nullability Regressions Broke Frontend Build
- **Files:** `frontend/src/pages/AutoApply.tsx`, `frontend/src/pages/InterviewPrep.tsx`, `frontend/src/pages/DocumentVault.tsx`, `frontend/src/pages/ResumeBuilder.tsx`, `frontend/src/api/interview.ts`, `frontend/src/api/auto-apply.ts`
- **Detail:** Several pages passed `null` values into props or types that required strings, and the interview page assumed a narrower payload shape than the backend returned.
- **Evidence:** `npm run build`
- **Status:** FIXED

## FE-F02 - FIXED: Login Test Was Brittle Against Current Heading Markup
- **File:** `frontend/src/tests/pages/Login.page.test.tsx`
- **Detail:** The test now queries the heading by accessible name instead of relying on raw concatenated text.
- **Evidence:** `npm run test -- --run`
- **Status:** FIXED
