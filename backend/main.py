import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import init_db
from backend.routers import jobs, scraper, search, stats, copilot, settings
from backend.scheduler import create_scheduler
from backend.enrichment.embedding import load_resume_embedding

# Configure logging
logging.basicConfig(
    level=getattr(logging, get_settings().LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Initialize database
    logger.info("Initializing database...")
    await init_db()

    # Load resume embedding if available
    try:
        await load_resume_embedding()
    except Exception as e:
        logger.warning(f"Could not load resume embedding: {e}")

    # Start scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    logger.info("JobRadar backend ready")
    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


app = FastAPI(
    title="JobRadar",
    description="Personal Job Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(jobs.router)
app.include_router(scraper.router)
app.include_router(search.router)
app.include_router(stats.router)
app.include_router(copilot.router)
app.include_router(settings.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
