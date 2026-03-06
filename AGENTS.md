# AGENTS.md

## Cursor Cloud specific instructions

### Project overview
JobRadar is a two-service monorepo: Python/FastAPI backend + React/TypeScript/Vite frontend. No Docker, no external database (SQLite embedded), no authentication.

### Services

| Service | Port | Start command |
|---------|------|---------------|
| Backend | 8000 | `uvicorn backend.main:app --reload --port 8000` (run from repo root) |
| Frontend | 5173 | `cd frontend && pnpm dev` |

Both can be started together with `make dev` from the repo root.

### Lint / type-check / build
- **TypeScript check**: `cd frontend && npx tsc --noEmit`
- **Frontend build**: `cd frontend && pnpm build`
- No ESLint config or Python linter is configured. No automated test suite exists.

### Non-obvious caveats
- `~/.local/bin` must be on `PATH` for `uvicorn` and other pip-installed CLI tools to be found. The update script handles this.
- pnpm v10 blocks esbuild build scripts by default. After `pnpm install`, run `pnpm rebuild esbuild` in `frontend/` so Vite can find the esbuild binary. The update script handles this.
- The backend auto-creates `data/jobradar.db` on startup; no manual DB setup needed.
- The `.env` file (copied from `.env.example`) contains API keys for scraping and LLM enrichment. The app runs without them but scrapers/enrichment won't function.
- The Greenhouse, Lever, and Ashby scrapers work without API keys but need a configured `company_watchlist` via `POST /api/settings`.
- The `sentence-transformers` model (~80 MB) auto-downloads from HuggingFace on first resume upload.
- The Vite dev server proxies `/api` requests to the backend on port 8000 (see `frontend/vite.config.ts`).
