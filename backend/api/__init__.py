"""
FastAPI route modules.
"""

from backend.api.routes_ingest import router as ingest_router
from backend.api.routes_analytics import router as analytics_router
from backend.api.routes_creators import router as creators_router
from backend.api.routes_orchestrator import router as orchestrator_router

__all__ = ["ingest_router", "analytics_router", "creators_router", "orchestrator_router"]
