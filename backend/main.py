"""
backend/main.py

FastAPI entrypoint for Instagram Growth Engine.
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.config import settings
from backend.database.session import init_db, engine
from backend.api.routes_ingest import router as ingest_router
from backend.api.routes_analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    yield


app = FastAPI(
    title="Instagram Growth Engine API",
    description="Agentic Management System API for Instagram Creators",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route routers
app.include_router(ingest_router)
app.include_router(analytics_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Healthcheck endpoint verifying server and database status."""
    db_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
    }
