"""User feedback and internal UX quality dashboard endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.models import UXFeedback, UXRubricEvaluation
from backend.database.session import get_db
from backend.security.auth import User
from backend.security.dependencies import get_current_user, require_admin, require_system_admin

router = APIRouter(prefix="/ux", tags=["UX Quality"])
FEEDBACK_WINDOW_DAYS = 90
MIN_FEEDBACK_FOR_COMBINED_SCORE = 5
WORKFLOW_LABELS = {
    "overview": "Overview Dashboard", "creators": "Creator Profile", "import": "Import Data",
    "analytics": "Analytics", "virality": "Content Scoring", "simulation": "Growth Planning",
    "strategy": "Growth Strategy", "calendar": "Content Calendar", "drafts": "Draft Studio",
    "experiments": "Experiments", "trends": "Trend Radar", "approvals": "Review Queue",
}
WORKFLOW_ALIASES = {key.casefold(): key for key in WORKFLOW_LABELS}
WORKFLOW_ALIASES.update({label.casefold(): key for key, label in WORKFLOW_LABELS.items()})
WORKFLOW_ALIASES.update({"calendar": "calendar", "drafts": "drafts", "overview": "overview"})


def normalize_workflow(value: str, allow_other: bool = False) -> str:
    normalized = value.strip().casefold()
    key = WORKFLOW_ALIASES.get(normalized)
    if key:
        return key
    if allow_other:
        return "other"
    raise ValueError("Choose a supported management workflow.")


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    rating: int = Field(..., ge=1, le=5)
    workflow: str = Field(..., min_length=1, max_length=80)
    comment: str | None = Field(None, max_length=1000)

    @field_validator("workflow", mode="before")
    @classmethod
    def validate_workflow(cls, value):
        if not isinstance(value, str):
            raise ValueError("Workflow must be a supported management workflow.")
        return normalize_workflow(value)


class RubricCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    task_completion: int = Field(..., ge=0, le=100)
    workflow_efficiency: int = Field(..., ge=0, le=100)
    learnability: int = Field(..., ge=0, le=100)
    accessibility: int = Field(..., ge=0, le=100)
    interface_clarity: int = Field(..., ge=0, le=100)
    notes: str | None = Field(None, max_length=1000)


@router.post("/feedback", status_code=201)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    feedback = UXFeedback(
        id=str(uuid.uuid4()), user_id=user.user_id, workspace_id=user.workspace_id,
        rating=payload.rating, workflow=payload.workflow.strip(),
        comment=payload.comment.strip() if payload.comment else None,
    )
    db.add(feedback)
    db.commit()
    return {"id": feedback.id, "status": "recorded"}


@router.post("/rubric", status_code=201)
def submit_rubric(
    payload: RubricCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_system_admin),
):
    evaluation = UXRubricEvaluation(id=str(uuid.uuid4()), evaluator_id=user.user_id, **payload.model_dump())
    db.add(evaluation)
    db.commit()
    return {"id": evaluation.id, "rubric_score": round(sum([
        payload.task_completion, payload.workflow_efficiency, payload.learnability,
        payload.accessibility, payload.interface_clarity,
    ]) / 5, 1)}


@router.get("/dashboard")
def get_ux_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    feedback_query = db.query(UXFeedback)
    if user.role != "system_admin":
        feedback_query = feedback_query.filter(UXFeedback.workspace_id == user.workspace_id)
    feedback_count = feedback_query.with_entities(func.count(UXFeedback.id)).scalar() or 0
    cutoff = (datetime.now(timezone.utc) - timedelta(days=FEEDBACK_WINDOW_DAYS)).replace(tzinfo=None)
    window_query = feedback_query.filter(UXFeedback.created_at >= cutoff)
    window_count = window_query.with_entities(func.count(UXFeedback.id)).scalar() or 0
    unique_respondents = window_query.with_entities(func.count(func.distinct(UXFeedback.user_id))).scalar() or 0
    feedback_avg = window_query.with_entities(func.avg(UXFeedback.rating)).scalar()
    feedback_rows = feedback_query.order_by(UXFeedback.created_at.desc()).limit(100).all()
    trend_rows = (
        window_query.with_entities(
            func.date(UXFeedback.created_at).label("day"),
            func.avg(UXFeedback.rating).label("average_rating"),
            func.count(UXFeedback.id).label("count"),
            func.count(func.distinct(UXFeedback.user_id)).label("respondents"),
        )
        .group_by(func.date(UXFeedback.created_at))
        .order_by(func.date(UXFeedback.created_at))
        .all()
    )
    raw_workflow_rows = (
        window_query.with_entities(
            UXFeedback.workflow,
            func.avg(UXFeedback.rating).label("average_rating"),
            func.count(UXFeedback.id).label("count"),
            func.count(func.distinct(UXFeedback.user_id)).label("respondents"),
        )
        .group_by(UXFeedback.workflow)
        .order_by(func.count(UXFeedback.id).desc(), UXFeedback.workflow.asc())
        .all()
    )
    workflow_totals: dict[str, dict[str, float]] = {}
    for workflow, average, count, respondents in raw_workflow_rows:
        workflow_key = normalize_workflow(workflow, allow_other=True)
        total = workflow_totals.setdefault(workflow_key, {"weighted_rating": 0.0, "count": 0, "respondents": 0})
        total["weighted_rating"] += float(average) * count
        total["count"] += count
        total["respondents"] += respondents
    workflow_breakdown = sorted(
        [{"workflow": WORKFLOW_LABELS.get(key, "Other / legacy"),
          "average_rating": round(total["weighted_rating"] / total["count"], 2),
          "count": int(total["count"]), "respondents": int(total["respondents"])} for key, total in workflow_totals.items()],
        key=lambda item: (-item["count"], item["workflow"].casefold()),
    )
    evaluations = db.query(UXRubricEvaluation).order_by(UXRubricEvaluation.created_at.desc()).limit(100).all()

    rubric_fields = ["task_completion", "workflow_efficiency", "learnability", "accessibility", "interface_clarity"]
    latest_rubric = None
    rubric_is_current = False
    if evaluations:
        latest = evaluations[0]
        rubric = {field: getattr(latest, field) for field in rubric_fields}
        rubric_score = round(sum(rubric.values()) / len(rubric), 1)
        latest_rubric = {"dimensions": rubric, "score": rubric_score, "evaluator_id": latest.evaluator_id,
                         "notes": latest.notes,
                         "created_at": latest.created_at.isoformat()}
        rubric_created = latest.created_at.replace(tzinfo=None)
        rubric_is_current = rubric_created >= cutoff
        latest_rubric["current_for_window"] = rubric_is_current

    # Combined score is available only once both a rubric and user feedback exist.
    user_score = round(((float(feedback_avg) - 1) / 4) * 100, 1) if feedback_avg is not None else None
    enough_feedback = unique_respondents >= MIN_FEEDBACK_FOR_COMBINED_SCORE
    combined = round(latest_rubric["score"] * 0.7 + user_score * 0.3, 1) if latest_rubric and rubric_is_current and user_score is not None and enough_feedback else None
    if latest_rubric is None:
        score_status = "missing_rubric"
    elif not rubric_is_current:
        score_status = "stale_rubric"
    elif not enough_feedback:
        score_status = "insufficient_feedback"
    else:
        score_status = "ready"
    return {
        "combined_score": combined,
        "score_formula": "70% latest five-dimension rubric + 30% average rating mapped from 1–5 to 0–100; both sources must be current within the last 90 days and ratings require at least 5 distinct respondents",
        "score_status": score_status,
        "minimum_feedback_for_combined_score": MIN_FEEDBACK_FOR_COMBINED_SCORE,
        "minimum_unique_respondents_for_combined_score": MIN_FEEDBACK_FOR_COMBINED_SCORE,
        "feedback_window_days": FEEDBACK_WINDOW_DAYS,
        "can_edit_rubric": user.role == "system_admin",
        "feedback_scope": "all_workspaces" if user.role == "system_admin" else user.workspace_id,
        "feedback": {"count": feedback_count, "window_count": window_count, "unique_respondents": unique_respondents,
                     "average_rating": round(float(feedback_avg), 2) if feedback_avg is not None else None,
                     "workflow_breakdown": workflow_breakdown,
                     "trend": [{"date": str(day), "average_rating": round(float(avg), 2), "count": count, "respondents": respondents}
                               for day, avg, count, respondents in trend_rows],
                     "rows": [{"id": f.id, "user_id": f.user_id, "workspace_id": f.workspace_id,
                               "rating": f.rating, "workflow": WORKFLOW_LABELS.get(f.workflow, f.workflow), "comment": f.comment,
                               "created_at": f.created_at.isoformat()} for f in feedback_rows]},
        "rubric": latest_rubric,
        "rubric_history": [{"score": round(sum(getattr(e, field) for field in rubric_fields) / 5, 1),
                             "created_at": e.created_at.isoformat(), "evaluator_id": e.evaluator_id}
                            for e in evaluations],
    }
