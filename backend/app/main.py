"""DarkTrace Backend - FastAPI Application Entry Point.

Dark Web Surveillance and Threat Intelligence Tool for law enforcement
and cybercrime investigators. Provides automated crawling, NLP analysis,
threat scoring, alerting, actor profiling, and reporting capabilities.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_databases, close_databases

# Import all routers
from app.auth.router import router as auth_router
from app.crawler.router import router as crawler_router
from app.alerts.router import router as alerts_router
from app.alerts.router import alert_rules_router
from app.watchlists.router import router as watchlists_router
from app.actors.router import router as actors_router
from app.reports.router import router as reports_router
from app.dashboard.router import router as dashboard_router
from app.search.router import router as search_router
from app.search.saved import router as saved_search_router
from app.admin.router import router as admin_router
from app.export import export_router
from app.nlp.router import router as nlp_router
from app.threat_scoring.router import router as threat_scoring_router
from app.intel.router import router as intel_router
from app.ws import router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize and cleanup resources."""
    settings = get_settings()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    if settings.TESTING:
        logger.info("Running in TESTING mode — skipping database initialization")
        yield
        logger.info("Shutdown complete (testing mode)")
        return

    # Initialize database connections
    await init_databases()
    logger.info("All database connections initialized")

    # Seed default configuration (rules, watchlists) only if empty
    await _seed_default_admin()
    try:
        from app.seed import seed_database
        await seed_database()
    except Exception as e:
        logger.warning("Database seeding failed: %s", e)

    # Start event poll recorder for fallback polling
    try:
        from app.ws import start_poll_recorder
        start_poll_recorder()
        logger.info("Event poll recorder started")
    except Exception as e:
        logger.warning("Poll recorder start failed: %s", e)

    # Start crawler scheduler
    try:
        from app.crawler.scheduler import get_scheduler
        from app.crawler.engine import get_crawl_engine
        scheduler = await get_scheduler()
        crawl_engine = await get_crawl_engine()

        # Set up callback to execute crawl jobs
        async def on_job_callback(job: dict):
            logger.info("Scheduler triggered job %s for %s", job["id"], job["target_url"])
            await crawl_engine.execute_job(job)

        scheduler.set_job_callback(on_job_callback)
        await scheduler.start()
    except Exception as e:
        logger.warning("Crawler scheduler init failed: %s", e)

    yield

    # Shutdown
    logger.info("Shutting down...")
    try:
        from app.crawler.scheduler import get_scheduler
        scheduler = await get_scheduler()
        await scheduler.stop()
    except Exception:
        pass
    await close_databases()
    logger.info("Shutdown complete")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Dark Web Surveillance and Threat Intelligence Tool Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Middleware: Request Logging ──────────────────────────────────────────────


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ─── Exception Handlers ───────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler — returns structured JSON error response."""
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request.headers.get("x-request-id", ""),
                "timestamp": time.time(),
            }
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "request_id": request.headers.get("x-request-id", ""),
                "timestamp": time.time(),
            }
        },
    )


# ─── Router Registration ─────────────────────────────────────────────────────


api_prefix = settings.API_PREFIX

app.include_router(auth_router, prefix=api_prefix)
app.include_router(crawler_router, prefix=api_prefix)
app.include_router(alerts_router, prefix=api_prefix)
app.include_router(alert_rules_router, prefix=api_prefix)
app.include_router(watchlists_router, prefix=api_prefix)
app.include_router(actors_router, prefix=api_prefix)
app.include_router(reports_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(search_router, prefix=api_prefix)
app.include_router(saved_search_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(export_router, prefix=api_prefix)
app.include_router(nlp_router, prefix=api_prefix)
app.include_router(threat_scoring_router, prefix=api_prefix)
app.include_router(intel_router, prefix=api_prefix)
app.include_router(ws_router)  # WebSocket at /ws/events, /ws/alerts, /ws/content


# ─── Health Check Endpoint (unauthenticated) ────────────────────────────────


@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# ─── Seed Default Admin ───────────────────────────────────────────────────────


async def _seed_default_admin():
    """Create default admin user if no users exist."""
    try:
        from app.database import get_mongodb
        db = await get_mongodb()
        existing = await db.users.find_one()
        if existing:
            return

        from app.auth.models import new_user_document
        settings = get_settings()
        admin_doc = new_user_document(
            email=settings.DEFAULT_ADMIN_EMAIL,
            name="System Administrator",
            password=settings.DEFAULT_ADMIN_PASSWORD,
            role="admin",
        )
        await db.users.insert_one(admin_doc)
        logger.info(
            "Default admin created: %s (password set, not logged)",
            settings.DEFAULT_ADMIN_EMAIL,
        )
    except Exception as e:
        logger.warning("Failed to seed default admin: %s", e)


# ─── Run (for development) ────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
