from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings, validate_runtime_settings
from app.database import engine
from app.shared.logging import setup_logging
from app.shared.middleware import (
    ApiRateLimitMiddleware,
    CsrfProtectionMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
)

logger = structlog.get_logger()


def create_app() -> FastAPI:
    setup_logging(debug=settings.debug)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa: ARG001
        validate_runtime_settings(settings)
        logger.info("starting_up", app=settings.app_name)

        yield

        await engine.dispose()
        logger.info("shutting_down")

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware (order matters — outermost first)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    app.add_middleware(ApiRateLimitMiddleware)
    app.add_middleware(CsrfProtectionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Routers
    from app.admin.router import router as admin_router
    from app.analytics.router import router as analytics_router
    from app.auth.router import router as auth_router
    from app.auto_apply.router import router as auto_apply_router
    from app.canonical_jobs.router import router as canonical_jobs_router
    from app.companies.router import router as companies_router
    from app.copilot.router import router as copilot_router
    from app.email.router import router as email_router
    from app.enrichment.router import router as enrichment_router
    from app.interview.router import router as interview_router
    from app.jobs.router import router as jobs_router
    from app.networking.router import router as networking_router
    from app.notifications.router import router as notifications_router
    from app.outcomes.router import router as outcomes_router
    from app.pipeline.router import router as pipeline_router
    from app.profile.router import router as profile_router
    from app.resume.router import router as resume_router
    from app.salary.router import router as salary_router
    from app.scraping.router import router as scraping_router
    from app.search_expansion.router import router as search_expansion_router
    from app.settings.router import router as settings_router
    from app.source_health.router import router as source_health_router
    from app.vault.router import router as vault_router

    prefix = settings.api_prefix
    app.include_router(auth_router, prefix=prefix)
    app.include_router(jobs_router, prefix=prefix)
    app.include_router(scraping_router, prefix=prefix)
    app.include_router(enrichment_router, prefix=prefix)
    app.include_router(pipeline_router, prefix=prefix)
    app.include_router(resume_router, prefix=prefix)
    app.include_router(copilot_router, prefix=prefix)
    app.include_router(auto_apply_router, prefix=prefix)
    app.include_router(interview_router, prefix=prefix)
    app.include_router(salary_router, prefix=prefix)
    app.include_router(vault_router, prefix=prefix)
    app.include_router(profile_router, prefix=prefix)
    app.include_router(settings_router, prefix=prefix)
    app.include_router(analytics_router, prefix=prefix)
    app.include_router(companies_router, prefix=prefix)
    app.include_router(source_health_router, prefix=prefix)
    app.include_router(admin_router, prefix=prefix)
    app.include_router(search_expansion_router, prefix=prefix)
    app.include_router(notifications_router, prefix=prefix)
    app.include_router(networking_router, prefix=prefix)
    app.include_router(canonical_jobs_router, prefix=prefix)
    app.include_router(email_router, prefix=prefix)
    app.include_router(outcomes_router, prefix=prefix)

    return app


app = create_app()
