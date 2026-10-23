"""
backend/api/routes_reports.py

REST API Endpoints for Reporting & Onboarding:
- GET  /reports/weekly/{creator_id}: Structured JSON weekly growth briefing with Markdown
- GET  /reports/weekly/{creator_id}/html: Printable HTML report
- POST /onboarding/initiate: Single-session onboarding pipeline
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Creator
from backend.reporting.weekly_report import generate_weekly_report
from backend.data.ingestion.ingest import run_ingestion
from backend.orchestrator.state_machine import run_orchestrator

router = APIRouter(tags=["Reporting & Onboarding"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class OnboardingRequest(BaseModel):
    creator_id: str = Field(..., description="Unique creator identifier")
    niche: Optional[str] = Field("Tech & AI", description="Creator niche")
    raw_data: List[Dict[str, Any]] = Field(..., description="Historical post records")


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.get("/reports/weekly/{creator_id}")
def get_weekly_report(
    creator_id: str,
    db: Session = Depends(get_db),
):
    """Generates an executive weekly growth report for a creator."""
    creator = db.get(Creator, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found.")

    report = generate_weekly_report(creator_id, db=db)
    return report


@router.get("/reports/weekly/{creator_id}/html", response_class=HTMLResponse)
def get_weekly_report_html(
    creator_id: str,
    db: Session = Depends(get_db),
):
    """Returns a standalone, styled, printable HTML weekly report."""
    creator = db.get(Creator, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found.")

    report = generate_weekly_report(creator_id, db=db)
    return HTMLResponse(content=report["html_report"], status_code=200)


@router.post("/onboarding/initiate")
def initiate_creator_onboarding(
    payload: OnboardingRequest,
    db: Session = Depends(get_db),
):
    """
    Single-session onboarding flow:
    1. Ingests and validates historical post metrics
    2. Runs orchestrator (intelligence -> decision -> strategy + 7-day plan + drafts)
    3. Auto-enqueues drafts for human review
    4. Generates the creator's first executive growth report
    """
    creator_id = payload.creator_id.strip()
    niche = payload.niche or "Tech & AI"

    # Step 1: Ingest
    ingest_res = run_ingestion(
        session_or_factory=db,
        creator_id=creator_id,
        source="onboarding_flow",
        raw_data=payload.raw_data,
        quality_threshold=0.4,
    )

    # Step 2: Ensure Creator record has niche set
    creator = db.get(Creator, creator_id)
    if creator:
        creator.niche = niche
        db.commit()

    # Step 3: Run Orchestrator Workflow
    workflow_state = run_orchestrator(
        creator_id=creator_id,
        db=db,
        trigger_event="onboarding",
    )

    # Step 4: Generate first Executive Report
    report = generate_weekly_report(creator_id, db=db)

    return {
        "status": "onboarding_completed",
        "creator_id": creator_id,
        "niche": niche,
        "posts_ingested": ingest_res.get("inserted_count", 0),
        "data_readiness": {
            "score": ingest_res.get("quality_score"),
            "data_ready": ingest_res.get("data_ready"),
        },
        "orchestrator_decision": workflow_state.get("decision", {}),
        "initial_strategy": (workflow_state.get("strategy_output") or {}).get("strategy"),
        "initial_content_plan": (workflow_state.get("strategy_output") or {}).get("content_plan"),
        "weekly_report_summary": {
            "average_engagement_rate": report["metrics"].get("average_engagement_rate"),
            "optimal_window": report["best_posting_window"],
            "markdown_report": report["markdown_report"],
        },
    }
