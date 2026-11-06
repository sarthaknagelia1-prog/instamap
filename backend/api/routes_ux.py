"""User feedback and internal UX quality dashboard endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.models import UXFeedback, UXRubricEvaluation
from backend.database.session import get_db
from backend.security.auth import User
from backend.security.dependencies import get_current_user, require_admin, require_system_admin

router = APIRouter(prefix="/ux", tags=["UX Quality"])


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    rating: int = Field(..., ge=1, le=5)
    workflow: str = Field(..., min_length=1, max_length=80)
    comment: str | None = Field(None, max_length=1000)


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
    evaluation_query = db.query(UXRubricEvaluation)
    if user.role != "system_admin":
        feedback_query = feedback_query.filter(UXFeedback.workspace_id == user.workspace_id)
        evaluation_query = evaluation_query.filter(UXRubricEvaluation.evaluator_id == user.user_id)
    feedback_rows = feedback_query.order_by(UXFeedback.created_at.desc()).limit(100).all()
    evaluations = evaluation_query.order_by(UXRubricEvaluation.created_at.desc()).limit(100).all()
    feedback_avg = feedback_query.with_entities(func.avg(UXFeedback.rating)).scalar()
    feedback_count = feedback_query.with_entities(func.count(UXFeedback.id)).scalar() or 0
    recent_feedback = feedback_query.order_by(UXFeedback.created_at.desc()).limit(500).all()
    trend_by_day: dict[str, list[int]] = {}
    for item in recent_feedback:
        day = item.created_at.date().isoformat()
        trend_by_day.setdefault(day, []).append(item.rating)

    rubric_fields = ["task_completion", "workflow_efficiency", "learnability", "accessibility", "interface_clarity"]
    latest_rubric = None
    if evaluations:
        latest = evaluations[0]
        rubric = {field: getattr(latest, field) for field in rubric_fields}
        rubric_score = round(sum(rubric.values()) / len(rubric), 1)
        latest_rubric = {"dimensions": rubric, "score": rubric_score, "evaluator_id": latest.evaluator_id,
                         "created_at": latest.created_at.isoformat()}

    # Combined score is available only once both a rubric and user feedback exist.
    user_score = round(((float(feedback_avg) - 1) / 4) * 100, 1) if feedback_avg is not None else None
    combined = round(latest_rubric["score"] * 0.7 + user_score * 0.3, 1) if latest_rubric and user_score is not None else None
    return {
        "combined_score": combined,
        "score_formula": "70% latest five-dimension rubric + 30% average user rating mapped from 1–5 to 0–100",
        "feedback": {"count": feedback_count, "average_rating": round(float(feedback_avg), 2) if feedback_avg is not None else None,
                     "trend": [{"date": day, "average_rating": round(sum(ratings) / len(ratings), 2), "count": len(ratings)}
                               for day, ratings in sorted(trend_by_day.items())],
                     "rows": [{"id": f.id, "user_id": f.user_id, "workspace_id": f.workspace_id,
                               "rating": f.rating, "workflow": f.workflow, "comment": f.comment,
                               "created_at": f.created_at.isoformat()} for f in feedback_rows]},
        "rubric": latest_rubric,
        "rubric_history": [{"score": round(sum(getattr(e, field) for field in rubric_fields) / 5, 1),
                             "created_at": e.created_at.isoformat(), "evaluator_id": e.evaluator_id}
                            for e in evaluations],
    }
