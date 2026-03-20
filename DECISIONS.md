# Architectural Decisions

Key technical decisions made during the development of JobRadar V2.

## 1. PostgreSQL over SQLite

**Decision**: Use PostgreSQL as the primary database.

**Rationale**: pgvector for embedding similarity search, full-text search with tsvector/tsquery, JSONB columns for flexible schema (skills, rules), and production-ready concurrency. SQLite compatibility is maintained via aiosqlite for testing.

## 2. Domain-Driven Module Structure

**Decision**: Organize backend code into domain modules (jobs/, pipeline/, auto_apply/, etc.) rather than technical layers (models/, services/, routes/).

**Rationale**: Each module is self-contained with its own models, schemas, router, and service. This makes the codebase navigable, reduces cross-module coupling, and allows parallel development across features.

## 3. ScraperPort Abstraction for Rust-Ready Boundary

**Decision**: Define scraper interfaces as abstract ports, keeping the scraping logic behind a clean boundary.

**Rationale**: The scraping layer is the most performance-sensitive part of the system. By defining clear interfaces, the Python implementation can be swapped for a Rust-based scraper in the future without touching the rest of the codebase.

## 4. JWT Authentication from Day One

**Decision**: Implement JWT-based auth with access + refresh tokens from the start.

**Rationale**: Stateless authentication scales horizontally. Refresh tokens enable long-lived sessions without long-lived access tokens. The auth module is isolated and can be extended with OAuth providers later.

## 5. pgvector for Embeddings

**Decision**: Use pgvector (PostgreSQL extension) for storing and querying embeddings rather than a dedicated vector database.

**Rationale**: Keeps the stack simple — one database for everything. pgvector supports cosine similarity, L2, and inner product distances. For our scale (<1M vectors), PostgreSQL performs well and avoids the operational complexity of a separate vector store.

## 6. APScheduler for Background Jobs

**Decision**: Use APScheduler (AsyncIOScheduler) for background tasks instead of Celery or a dedicated task queue.

**Rationale**: Runs in the same process as the FastAPI app, eliminating the need for a separate worker process in development. Supports interval, cron, and one-shot triggers. For production scaling, the architecture allows migration to arq (Redis-backed) workers.

## 7. SSE for Real-Time Updates

**Decision**: Use Server-Sent Events (SSE) instead of WebSockets for real-time notifications.

**Rationale**: SSE is simpler (unidirectional), works through proxies and load balancers without special configuration, auto-reconnects natively in browsers, and suits our use case (server pushes updates to clients). WebSocket's bidirectional capability isn't needed.

## 8. Click-to-Transition over Drag-and-Drop for Pipeline

**Decision**: Use click-based status transitions in the application pipeline instead of drag-and-drop Kanban.

**Rationale**: Simpler to implement correctly across devices (mobile-friendly), better accessibility, and avoids the complexity of drag-and-drop libraries. Status transitions are constrained (e.g., can't go from Offer back to Saved), which click-based UI handles more naturally with validation.

## 9. React.lazy Code Splitting per Route

**Decision**: Every page component uses React.lazy() with a Suspense fallback.

**Rationale**: Keeps the initial bundle small. Users only download the code for the page they're visiting. Combined with Vite's automatic chunk splitting, this gives fast initial loads and reasonable subsequent navigation times.

## 10. Playwright for Auto-Apply

**Decision**: Use Playwright (not Selenium) for browser automation in the auto-apply engine.

**Rationale**: Modern API with native async/await, built-in auto-waiting, better reliability than Selenium, and supports all major browsers. The headless Chromium mode is efficient for server-side operation.
