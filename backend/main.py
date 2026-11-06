"""
backend/main.py

FastAPI entrypoint for Instagram Growth Engine.
"""

from __future__ import annotations
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text

from backend.config import settings
from backend.database.session import init_db, engine
from backend.api.routes_ingest import router as ingest_router
from backend.api.routes_analytics import router as analytics_router
from backend.api.routes_creators import router as creators_router
from backend.api.routes_orchestrator import router as orchestrator_router
from backend.api.routes_content import router as content_router
from backend.api.routes_experiments import router as experiments_router
from backend.api.routes_trends import router as trends_router
from backend.api.routes_approvals import router as approvals_router
from backend.api.routes_reports import router as reports_router
from backend.api.routes_advisory import router as advisory_router
from backend.api.routes_auth import router as auth_router
from backend.api.routes_ux import router as ux_router


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


@app.middleware("http")
async def enforce_request_size_and_cookie_csrf(request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > settings.MAX_REQUEST_SIZE_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large."})
    unsafe = request.method in {"POST", "PUT", "PATCH", "DELETE"}
    cookie_auth = request.cookies.get("instamap_session") and not (
        request.headers.get("x-api-key") or request.headers.get("authorization")
    )
    if unsafe and cookie_auth:
        origin = request.headers.get("origin")
        if not origin or origin.rstrip("/") not in {item.rstrip("/") for item in settings.cors_origins_list}:
            return JSONResponse(status_code=403, content={"detail": "Untrusted request origin."})
    return await call_next(request)

# CORS middleware with explicit trusted origins (SEC-03)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "Accept"],
)

# Include route routers
app.include_router(ingest_router)
app.include_router(analytics_router)
app.include_router(creators_router)
app.include_router(orchestrator_router)
app.include_router(content_router)
app.include_router(experiments_router)
app.include_router(trends_router)
app.include_router(approvals_router)
app.include_router(reports_router)
app.include_router(advisory_router)
app.include_router(auth_router)
app.include_router(ux_router)

# Serve React only. The legacy inline-script dashboard is retired because it
# interpolates API-controlled data into HTML and has no session support.
frontend_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

react_assets_dir = os.path.join(frontend_dist_dir, "assets")
if os.path.isdir(react_assets_dir):
    app.mount("/assets", StaticFiles(directory=react_assets_dir), name="react_assets")


@app.get("/", tags=["Dashboard UI"], include_in_schema=False)
@app.get("/dashboard", tags=["Dashboard UI"])
def get_dashboard_ui():
    """Serves the creator command center React application."""
    react_index = os.path.join(frontend_dist_dir, "index.html")
    if os.path.isfile(react_index):
        return FileResponse(react_index)
    raise HTTPException(status_code=503, detail="Frontend build is unavailable.")


@app.get("/legacy", tags=["Legacy UI"])
def get_legacy_dashboard_ui():
    """The legacy UI is retired; it used unsafe inline HTML rendering."""
    raise HTTPException(status_code=410, detail="The legacy dashboard has been retired.")

@app.get("/health", tags=["Health"])
def health_check():
    """Healthcheck endpoint verifying server and database status."""
    db_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unavailable"

    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
    }
