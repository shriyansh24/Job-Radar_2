# Routers Module Context

## Purpose
FastAPI route handlers for all API endpoints — job CRUD, scraper control, search, analytics, AI copilot, settings management.

## Current Status
- jobs.py: GET (list + filters + FTS5), GET (single), PATCH (update)
- scraper.py: POST (run), GET (status), GET (SSE stream)
- search.py: GET (semantic search via embeddings)
- stats.py: GET (aggregated dashboard statistics)
- copilot.py: POST (streaming AI tools via OpenRouter)
- settings.py: GET/POST settings, POST resume upload, saved searches CRUD

## All Routes

### jobs.py
```
GET  /api/jobs
  Params: page, limit, q, location, source, status, experience_level,
          remote_type, posted_within_days, min_match_score, min_salary,
          tech_stack, company, is_starred, sort_by, sort_dir
  Returns: JobListResponse {jobs[], total, page, limit, has_more}

GET  /api/jobs/{job_id}
  Returns: JobBase

PATCH /api/jobs/{job_id}
  Body: {status?, notes?, tags?, is_starred?}
  Side effect: Sets applied_at when status="applied"
  Returns: JobBase
```

### scraper.py
```
POST /api/scraper/run
  Body: {source: "all"|"serpapi"|"greenhouse"|"lever"|"ashby"|"jobspy"}
  Side effect: Launches async scraper task
  Returns: ScraperRun[] (last 10 runs)

GET  /api/scraper/status
  Returns: {runs: ScraperRun[], is_running: bool}

GET  /api/scraper/stream
  Returns: SSE stream (text/event-stream)
  Events: scraper_started, job_found, scraper_progress,
          scraper_completed, scraper_error, keepalive (30s)
```

### search.py
```
GET  /api/search/semantic?q=...&limit=20
  Requires: Resume embedding loaded
  Returns: SemanticSearchResult[] {job_id, title, company_name, score}
```

### stats.py
```
GET  /api/stats
  Returns: {total_jobs, new_today, by_source{}, by_status{},
            by_experience_level{}, top_companies[], top_skills[],
            jobs_over_time[], avg_match_score}
```

### copilot.py
```
POST /api/copilot
  Body: {tool: "coverLetter"|"interviewPrep"|"gapAnalysis", job_id: str}
  Returns: SSE stream (streamed LLM response)
  Note: Proxies to OpenRouter, keeps API key server-side
```

### settings.py
```
GET  /api/settings        -> SettingsResponse
POST /api/settings        -> SettingsResponse (updates .env file)
POST /api/resume/upload   -> {filename, text_length, uploaded_at}
GET  /api/saved-searches  -> SavedSearch[]
POST /api/saved-searches  -> SavedSearch
DELETE /api/saved-searches/{id} -> {status: "deleted"}
GET  /api/health          -> {status: "ok", version: "0.1.0"}
```

## Dependencies
- fastapi (routers, Query, Depends, HTTPException)
- sqlalchemy (select, func, update, and_, or_, text)
- backend.database (get_db session dependency)
- backend.models (Job, SavedSearch, ScraperRun, UserProfile)
- backend.schemas (all Pydantic request/response models)

## Error Handling
- All errors return `{"error": "message", "detail": "..."}` format
- CORS: `http://localhost:5173`, `http://127.0.0.1:5173`
- Sort validation: regex pattern on sort_by parameter
- File upload: 5MB max, PDF/TXT only
