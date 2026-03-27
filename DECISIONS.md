# Architectural Decisions

Key technical decisions made during the development of JobRadar V2.

## 1. PostgreSQL Over SQLite

**Decision**: Use PostgreSQL as the primary database.

**Rationale**: pgvector for embedding similarity search, full-text search with tsvector/tsquery, JSONB columns for flexible schema, and production-ready concurrency. SQLite compatibility is still used for tests and isolated tooling.

## 2. Domain-Driven Module Structure

**Decision**: Organize backend code into domain modules (`jobs/`, `pipeline/`, `auto_apply/`, and so on) rather than technical layers.

**Rationale**: Each module remains self-contained with its own models, schemas, router, and service. This keeps the codebase navigable and lowers cross-module coupling.

## 3. ScraperPort Abstraction For A Rust-Ready Boundary

**Decision**: Define scraper interfaces as abstract ports.

**Rationale**: The scraping layer is the most performance-sensitive part of the system. A clean interface lets the Python implementation be replaced later without rewriting the rest of the app.

## 4. Cookie-Based JWT Authentication

**Decision**: Implement cookie-based JWT auth with access + refresh tokens.

**Rationale**: HTTP-only cookies reduce XSS token theft risk. Refresh tokens enable long-lived sessions without long-lived access tokens. Token revocation is supported via `token_version`.

## 5. pgvector For Embeddings

**Decision**: Use pgvector inside PostgreSQL instead of a separate vector database.

**Rationale**: It keeps the stack simpler while still supporting similarity search at the scale this project targets.

## 6. APScheduler For Background Jobs

**Decision**: Use APScheduler (`AsyncIOScheduler`) for background tasks instead of Celery.

**Rationale**: It keeps development and local deployment simpler than introducing a queue-first architecture while still allowing a dedicated scheduler process today and a later migration to a dedicated worker queue if the job mix outgrows in-process scheduled execution.

## 7. SSE For Real-Time Updates

**Decision**: Use Server-Sent Events instead of WebSockets for live updates.

**Rationale**: SSE matches the current one-way server-to-client notification model and is operationally simpler through proxies and local development setups.

## 8. Click-To-Transition Over Drag-And-Drop For Pipeline

**Decision**: Use click-based status transitions in the pipeline instead of drag-and-drop.

**Rationale**: It is simpler to implement correctly across desktop and mobile, improves accessibility, and better fits constrained stage transitions.

## 9. Route-Level Code Splitting

**Decision**: Load major page surfaces lazily by route.

**Rationale**: It keeps the initial bundle smaller while preserving fast navigation for already-opened parts of the workspace.

## 10. Playwright For Auto-Apply

**Decision**: Use Playwright rather than Selenium for browser automation in the auto-apply engine.

**Rationale**: Playwright provides a more modern async API, stronger auto-waiting, and better reliability for this workflow.

## 11. Reference-First Frontend Migration

**Decision**: Use the reference repo's visual system as the frontend authority for typography, colors, shell posture, and page framing while keeping this repo authoritative for routes, auth, data flow, and backend semantics.

**Rationale**: The reference implementation produced a stronger shell, clearer hierarchy, and better visual rhythm. Porting its visual language without inheriting its mock-data architecture preserves the current product behavior while materially improving the shipped UI.

## 12. Shadowless Buttons

**Decision**: Keep interactive buttons visually flat and shadowless across the frontend.

**Rationale**: The current UI direction favors sharper surfaces and clearer separation between controls and containers. Buttons should read as controls, while structural elevation is reserved for cards, panels, and shell regions.

## 13. Theme Families In Runtime

**Decision**: Support `theme family + mode` in the frontend runtime instead of a simple light/dark toggle.

**Rationale**: The current visual direction now includes `default`, `terminal`, `blueprint`, and `phosphor` families. Modeling the theme as a family plus mode keeps the implementation extensible without changing route or data contracts.

## 14. Purpose-Driven Test Taxonomy

**Decision**: Organize frontend and backend tests by protection goal and system boundary rather than historical accident.

**Rationale**: Frontend tests are now grouped under `frontend/src/tests/{app,api,components,hooks,pages,support}` and backend tests increasingly live under role-based directories such as `infra/`, `migrations/`, `security/`, and `workers/`. This makes the suite easier to navigate and reduces drift between what a test protects and where it lives.
