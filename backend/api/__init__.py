"""
FastAPI route modules.
"""

from backend.api.routes_ingest import router as ingest_router
from backend.api.routes_analytics import router as analytics_router
from backend.api.routes_creators import router as creators_router
from backend.api.routes_orchestrator import router as orchestrator_router
from backend.api.routes_content import router as content_router
from backend.api.routes_experiments import router as experiments_router
from backend.api.routes_trends import router as trends_router
from backend.api.routes_approvals import router as approvals_router
from backend.api.routes_reports import router as reports_router

__all__ = [
    "ingest_router",
    "analytics_router",
    "creators_router",
    "orchestrator_router",
    "content_router",
    "experiments_router",
    "trends_router",
    "approvals_router",
    "reports_router",
]
