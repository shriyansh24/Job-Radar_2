# JobRadar V2

AI-powered job hunting assistant with intelligent scraping, enrichment, and auto-apply.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 22+ (for frontend dev)
- Python 3.12+ (for backend dev)

### Development

```bash
# Start infrastructure
docker-compose up -d postgres redis

# Backend
cd backend
uv sync
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Docker (full stack)

```bash
docker-compose up
```

Open http://localhost:5173 (dev) or http://localhost:3000 (docker)

## Architecture

- **Backend**: Python/FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Redis
- **Frontend**: React 19 + Vite 6 + TypeScript 5.6 strict + Tailwind CSS v4
- **AI**: OpenRouter (LLM), sentence-transformers (embeddings), pgvector
- **Auto-apply**: Playwright browser automation with ATS detection
- **Background jobs**: APScheduler (scraping, enrichment, auto-apply)
- **Real-time**: SSE (Server-Sent Events) for live updates

## Project Structure

```
jobradar-v2/
├── backend/                  # FastAPI application
│   ├── app/                  # Source code
│   │   ├── admin/            # Admin dashboard API
│   │   ├── analytics/        # Usage analytics
│   │   ├── auth/             # JWT authentication
│   │   ├── auto_apply/       # Auto-apply engine (Playwright)
│   │   ├── companies/        # Company enrichment
│   │   ├── copilot/          # AI copilot chat
│   │   ├── enrichment/       # Job enrichment + LLM client
│   │   ├── interview/        # Interview prep AI
│   │   ├── jobs/             # Job CRUD + search
│   │   ├── pipeline/         # Application pipeline
│   │   ├── profile/          # User profiles
│   │   ├── resume/           # Resume builder
│   │   ├── salary/           # Salary insights
│   │   ├── scraping/         # Job scraper (multi-source)
│   │   ├── search_expansion/ # Query expansion
│   │   ├── settings/         # User settings
│   │   ├── shared/           # Middleware, logging, utils
│   │   ├── source_health/    # Scraper health monitoring
│   │   ├── vault/            # Document vault
│   │   └── workers/          # Background job workers
│   └── tests/                # pytest tests
├── frontend/                 # React application
│   ├── src/
│   │   ├── api/              # API client modules (13)
│   │   ├── components/       # UI components (15+)
│   │   ├── hooks/            # Custom React hooks
│   │   ├── pages/            # Page components (13)
│   │   └── stores/           # Zustand state stores
│   └── dist/                 # Production build
├── docker-compose.yml
├── Makefile
├── DECISIONS.md              # Architectural decisions
└── THIRD_PARTY_CODE.md       # Third-party licenses
```

## Features

- **Smart Job Scraping**: Multi-source scraping with deduplication (SimHash + exact hash)
- **AI Enrichment**: LLM-powered summaries, skill extraction, red/green flag detection
- **Semantic Search**: pgvector embeddings + TF-IDF scoring for job matching
- **Application Pipeline**: Kanban-style tracking (Saved → Applied → Interview → Offer)
- **Auto-Apply Engine**: Playwright-powered form filling with ATS detection (Greenhouse, Lever, Workday, etc.)
- **Interview Prep**: AI-generated questions with answer evaluation
- **Salary Insights**: Market data comparison and negotiation tips
- **Resume Builder**: Multiple templates with AI-assisted content
- **Document Vault**: Centralized storage for resumes, cover letters, references
- **Analytics Dashboard**: Application trends, response rates, pipeline metrics
- **Real-time Updates**: SSE-powered live notifications

## Development Commands

```bash
make dev      # Start dev environment with hot reload
make test     # Run all tests
make lint     # Lint backend + frontend
make migrate  # Run database migrations
```

## Testing

```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && npm test -- --run

# Build check
cd frontend && npm run build
```
