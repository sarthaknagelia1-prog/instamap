"""
FastAPI route modules.
"""

from backend.api.routes_ingest import router as ingest_router
from backend.api.routes_analytics import router as analytics_router

__all__ = ["ingest_router", "analytics_router"]
