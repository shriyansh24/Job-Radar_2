# AGENT_OVERRIDES.md
# Ground Truths — Read This First. Takes Precedence Over ALL Research Docs and CLAUDE.md.

This file contains facts verified AFTER the three research documents were written.
When anything here conflicts with research-claude.md, research-perplexity.md,
research-openai.md, or CLAUDE.md — this file wins, no exceptions.

---

## ❌ Dead Services — Do NOT Build Adapters For These

### ProxyCurl (nubela.co/proxycurl) — SHUT DOWN July 4, 2025

LinkedIn filed a federal lawsuit in January 2025. ProxyCurl shut down rather than
fight a $10B company. The website now redirects to NinjaPear. Every API key ever
issued returns errors.

**What this means for the build:**
- Do NOT create `proxycurl_scraper.py`
- Do NOT add `PROXYCURL_KEY` to `.env.example` or `config.py`
- Do NOT reference ProxyCurl in any comments, docstrings, or README
- For LinkedIn coverage: use SerpApi results where `via` contains "LinkedIn",
  and use JobSpy as the free multi-board fallback (see below)

All three research docs recommend ProxyCurl for LinkedIn data. All three are wrong
on this point. Ignore those sections entirely.

---

## ✅ Critical Library — Not In Any Research Doc, USE THIS

### JobSpy (`python-jobspy`, GitHub: speedyapply/JobSpy)

- Install: `pip install python-jobspy`
- Version as of Feb 2026: v1.1.82, actively maintained, ~2,800 GitHub stars
- Scrapes LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter **concurrently**
- Returns structured pandas DataFrames — no parsing needed
- **Free. No API key. No rate limit fees.**

Use as the primary free fallback scraper when:
- User has no SerpApi key configured
- SerpApi monthly quota is exhausted
- Need LinkedIn/Indeed/Glassdoor coverage without paying per-call

```python
from jobspy import scrape_jobs

jobs_df = scrape_jobs(
    site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
    search_term=query,
    location=location,
    results_wanted=limit,
    hours_old=72,
    country_indeed="USA"
)
# Convert DataFrame rows to normalized JobRawDict and proceed as normal
```

Add `python-jobspy==1.1.82` to `requirements.txt`.
Create `jobspy_scraper.py` in the scrapers directory (not `proxycurl_scraper.py`).

---

## 🤖 LLM — No Local Inference, Use OpenRouter API

The research docs recommended Ollama + qwen2.5:7b for "zero cost." The user does
not want local inference and is happy to pay for API access.

**Use OpenRouter (openrouter.ai) for all LLM enrichment.**

OpenRouter is OpenAI-SDK-compatible — it is literally just a `base_url` swap.
No new SDK needed. Use the `openai` Python package as-is.

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "JobRadar"
    }
)
```

**Primary model:** `anthropic/claude-3-5-haiku`
- Best JSON schema adherence of any small/fast model
- Low latency — good for batch enrichment
- ~$0.80/1M input + $4/1M output ≈ $0.004 per job enriched

**Fallback model:** `openai/gpt-4o-mini`
- Use if primary fails or rate limited
- ~$0.15/1M input + $0.60/1M output ≈ $0.0006 per job enriched

**Cost at scale:**
- 10,000 jobs enriched with Haiku ≈ $40
- 10,000 jobs enriched with gpt-4o-mini ≈ $6
- User is aware of and accepts this cost

**What this means for the build:**
- Remove `ollama` from `requirements.txt` entirely
- Remove `OLLAMA_BASE_URL` and `OLLAMA_MODEL` from `.env.example` and `config.py`
- Remove any `import ollama` or `ollama.chat()` calls
- The `openai` SDK stays — it handles OpenRouter via base_url
- Add these to `.env.example`:
  ```
  OPENROUTER_API_KEY=
  OPENROUTER_PRIMARY_MODEL=anthropic/claude-3-5-haiku
  OPENROUTER_FALLBACK_MODEL=openai/gpt-4o-mini
  ```

---

## 💰 Corrected Pricing (Use These — Research Docs Have Stale Numbers)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Cost per job (~2K in / ~500 out) |
|---|---|---|---|
| claude-3-5-haiku (via OpenRouter) | $0.80 | $4.00 | ~$0.004 |
| gpt-4o-mini (via OpenRouter) | $0.15 | $0.60 | ~$0.0006 |

Perplexity's doc states GPT-4o-mini is $0.60/$2.40 per 1M — this is old pricing.
Claude's doc states $0.42/1K jobs — also based on old pricing.
Use the table above.

---

## 🎨 Design System — Source of Truth

CLAUDE.md defines a "Void Terminal" palette with purple accent and Inter/JetBrains Mono.
**Discard that entirely.** The user has chosen a different aesthetic.

The `ui-prototype.jsx` `StyleSystem` component is the source of truth for all
visual tokens. Copy it verbatim into `index.css`. The confirmed palette is:

```css
--bg-base:        #000000;
--bg-surface:     #0a0a0a;
--bg-elevated:    #111111;
--border:         #333333;
--text-primary:   #EDEDED;
--text-secondary: #888888;
--accent:         #0070F3;   /* Vercel blue — NOT purple */
--accent-green:   #10B981;
--accent-amber:   #F5A623;
--accent-red:     #E00000;
--accent-cyan:    #3291FF;
--font-ui:        'Geist', -apple-system, sans-serif;
--font-mono:      'Geist Mono', monospace;
```

Load fonts via Google Fonts `<link>` in `index.html`:
```html
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

---

## 🖼️ UI Reference — Gemini Prototype (`ui-prototype.jsx`)

A working UI prototype exists. Use it as a **structural and component reference**.

**DO carry these patterns forward verbatim:**
- `ScoreRing` SVG donut component — well implemented, copy it exactly
- Job detail panel layout (header, status selector, flags, match score, description)
- `AI Copilot Tools` section in job detail (cover letter, interview prep, gap analysis)
  — this was not in the original spec but is a good addition, keep it
- Scraper log drawer expand/collapse behavior and log line formatting
- Kanban column structure and card layout
- Clearbit logo with initials fallback pattern (`onError` → show initials div)
- Custom scrollbar CSS (6px, thin, styled to match palette)
- `glass-panel` utility class

**Do NOT carry these forward:**
- Any hardcoded `MOCK_JOBS` array or mock chart data — replace with real API calls
- The `callGeminiAPI()` function — the frontend should never hold API keys.
  Replace with a call to your own backend endpoint `POST /api/copilot` which
  uses OpenRouter internally
- Settings page Ollama fields — replace with OpenRouter fields (see LLM section above)
- The incomplete Analytics page — implement all 4 chart rows using Recharts as
  specified in CLAUDE.md

---

## ⚖️ Conflict Resolution — Priority Order

1. **This file (AGENT_OVERRIDES.md)** — always wins
2. **research-claude.md** — architecture, stack, phased roadmap, open-source libraries
3. **research-perplexity.md** — API pricing tables, per-domain rate limits
4. **research-openai.md** — ATS endpoint specifics (Greenhouse/Lever/Ashby schemas)
5. **CLAUDE.md** — full build specification (except where overridden above)
6. **ui-prototype.jsx** — component patterns and design tokens (except mock data)

---

## 🔒 Confirmed Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + FastAPI 0.115+ + SQLAlchemy 2.0 async |
| Database | SQLite WAL mode + FTS5 virtual table |
| Scheduler | APScheduler 3.10+ AsyncIOScheduler + SQLAlchemy job store |
| Frontend | React 19 + TypeScript 5 + Vite 6 + TailwindCSS v3.4 |
| Fonts | Geist + Geist Mono (Google Fonts) |
| Vector search | sentence-transformers all-MiniLM-L6-v2 + sqlite-vec |
| LLM | OpenRouter — claude-3-5-haiku primary, gpt-4o-mini fallback |
| Primary data | SerpApi Google Jobs + Greenhouse/Lever/Ashby ATS APIs (free) |
| Free fallback | JobSpy (no API key required) |
| Package mgmt | uv (Python) + pnpm (frontend) + Makefile |

---

## 🚫 Do Not Build These

- ProxyCurl integration (dead service)
- Ollama or any local LLM inference
- Celery + Redis (APScheduler is sufficient)
- Docker in Phase 1–5 (Phase 6 only, optional)
- Direct Glassdoor DOM scraping (use Google Jobs SERP `via: Glassdoor` instead)
- Direct LinkedIn scraping with cookies (use SerpApi + JobSpy instead)
- Any hardcoded mock data, lorem ipsum, or placeholder charts in production code