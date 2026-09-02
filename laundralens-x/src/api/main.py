"""
LaundraLens X — FastAPI application entry point.
All routes registered here. CORS enabled for Streamlit dashboard.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from src.db.database import create_all_tables

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger("laundralens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup."""
    logger.info("🚀 LaundraLens X starting up...")
    create_all_tables()
    logger.info("✅ Database tables ready.")
    yield
    logger.info("🛑 LaundraLens X shutting down.")


app = FastAPI(
    title="LaundraLens X",
    description="Agentic Temporal-Graph Intelligence for Financial Crime Investigation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS for Streamlit dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Import and register routes ---
from src.api.routes.health import router as health_router
from src.api.routes.alerts import router as alerts_router
from src.api.routes.accounts import router as accounts_router
from src.api.routes.graph import router as graph_router
from src.api.routes.investigations import router as investigations_router
from src.api.routes.cases import router as cases_router

app.include_router(health_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(accounts_router, prefix="/api/v1")
app.include_router(graph_router, prefix="/api/v1")
app.include_router(investigations_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )
