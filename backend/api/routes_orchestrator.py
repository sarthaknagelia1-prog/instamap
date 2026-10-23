"""
backend/api/routes_orchestrator.py

API Endpoints for Phase 3 Orchestrator Core:
- POST /creator-plan: Executes full orchestrator workflow (fetch -> analyze -> decide -> plan/report).
- GET /creator-plan/{job_id}: Retrieves status, execution trace, and results of a plan run.
- GET /creator-plan/history/{creator_id}: Retrieves historical runs for a creator.
"""

from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Creator, OrchestratorRun
from backend.agents.schemas import DecisionThresholds, utcnow
from backend.orchestrator.state_machine import run_orchestrator

router = APIRouter(prefix="/creator-plan", tags=["Orchestrator"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class CreatorPlanRequest(BaseModel):
    creator_id: str = Field(..., description="Target creator ID to generate plan for")
    trigger_event: Optional[str] = Field("manual", description="Trigger source (manual, data_upload, scheduled)")
    thresholds: Optional[DecisionThresholds] = Field(None, description="Optional custom threshold overrides")


class CreatorPlanResponse(BaseModel):
    job_id: str
    creator_id: str
    status: str
    decision: Dict[str, Any]
    output: Dict[str, Any]
    execution_trace: List[Dict[str, Any]]
    created_at: str
    completed_at: Optional[str] = None


class OrchestratorRunListItem(BaseModel):
    job_id: str
    creator_id: str
    status: str
    trigger: str
    decision: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.post("", response_model=CreatorPlanResponse)
def create_creator_plan(
    payload: CreatorPlanRequest,
    db: Session = Depends(get_db),
):
    """
    Executes the Orchestrator State Machine:
    1. Fetches creator posts from PostgreSQL.
    2. Runs quantitative & qualitative performance analytics.
    3. Evaluates decision rules (drop % / staleness / momentum).
    4. Routes to Strategy Planning, Executive Report, or Data Request.
    5. Saves full execution audit trace in OrchestratorRun table.
    """
    creator = db.get(Creator, payload.creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{payload.creator_id}' not found. Ingest creator data first.",
        )

    job_id = str(uuid.uuid4())
    run_record = OrchestratorRun(
        id=job_id,
        creator_id=payload.creator_id,
        status="running",
        trigger=payload.trigger_event or "manual",
        created_at=utcnow(),
    )
    db.add(run_record)
    db.commit()

    try:
        final_state = run_orchestrator(
            creator_id=payload.creator_id,
            db=db,
            trigger_event=payload.trigger_event or "manual",
            thresholds=payload.thresholds,
        )

        decision_dict = final_state.get("decision", {})
        action_name = decision_dict.get("action", "unknown")

        # Determine main output based on route taken
        output = final_state.get("strategy_output") or final_state.get("report_output") or {}

        run_record.status = "completed"
        run_record.decision = action_name
        run_record.trace = final_state.get("execution_trace", [])
        run_record.result = output
        run_record.completed_at = utcnow()
        db.commit()

        return {
            "job_id": job_id,
            "creator_id": payload.creator_id,
            "status": "completed",
            "decision": decision_dict,
            "output": output,
            "execution_trace": final_state.get("execution_trace", []),
            "created_at": run_record.created_at.isoformat(),
            "completed_at": run_record.completed_at.isoformat() if run_record.completed_at else None,
        }
    except Exception as e:
        run_record.status = "failed"
        run_record.result = {"error": str(e)}
        run_record.completed_at = utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestrator run failed: {str(e)}",
        )


@router.get("/{job_id}", response_model=CreatorPlanResponse)
def get_plan_by_id(job_id: str, db: Session = Depends(get_db)):
    """Retrieves an existing orchestrator plan by its unique job ID."""
    run = db.get(OrchestratorRun, job_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orchestrator job '{job_id}' not found.",
        )

    return {
        "job_id": run.id,
        "creator_id": run.creator_id,
        "status": run.status,
        "decision": {"action": run.decision},
        "output": run.result or {},
        "execution_trace": run.trace or [],
        "created_at": run.created_at.isoformat() if run.created_at else "",
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get("/history/{creator_id}", response_model=List[OrchestratorRunListItem])
def get_creator_plan_history(
    creator_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists historical plan and strategy runs for a creator."""
    creator = db.get(Creator, creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{creator_id}' not found.",
        )

    runs = (
        db.query(OrchestratorRun)
        .filter_by(creator_id=creator_id)
        .order_by(OrchestratorRun.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "job_id": r.id,
            "creator_id": r.creator_id,
            "status": r.status,
            "trigger": r.trigger,
            "decision": r.decision,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in runs
    ]
