"""
backend/api/routes_experiments.py

Phase 5 API Endpoints for Experiment Engine:
- POST /experiments/propose: Proposes a structured hypothesis experiment based on creator metrics.
- POST /experiments: Manually creates an experiment.
- GET /experiments: Lists experiments with filtering by creator and status.
- GET /experiments/{experiment_id}: Inspects a single experiment.
- POST /experiments/{experiment_id}/assign-posts: Assigns post IDs to Variant A and Variant B.
- POST /experiments/{experiment_id}/evaluate: Evaluates statistical significance and triggers strategy feedback loop.
"""

from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.session import get_db
from backend.database.models import Creator, Experiment, Post, Strategy, utcnow
from backend.analytics.metrics import calculate_aggregate_metrics, calculate_post_engagement_rate
from backend.analytics.trends import detect_trends
from backend.experiments.evaluator import evaluate_experiment_metrics
from backend.agents.experiment_agent import run_experiment_agent

router = APIRouter(prefix="/experiments", tags=["Experiments"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class ProposeExperimentRequest(BaseModel):
    creator_id: str
    niche: Optional[str] = None
    use_llm: bool = False


class CreateExperimentRequest(BaseModel):
    creator_id: str
    title: str
    hypothesis: str
    metric_target: Optional[str] = Field("engagement_rate", description="engagement_rate | reach")
    controlled_variables: Optional[Dict[str, Any]] = None
    variant_a: Dict[str, Any] = Field(..., description="Control variant definition")
    variant_b: Dict[str, Any] = Field(..., description="Treatment variant definition")


class AssignPostsRequest(BaseModel):
    variant_a_post_ids: List[str] = Field(..., description="List of post_ids assigned to Variant A")
    variant_b_post_ids: List[str] = Field(..., description="List of post_ids assigned to Variant B")


class ExperimentResponse(BaseModel):
    id: str
    creator_id: str
    title: str
    hypothesis: str
    metric_target: str
    status: str
    controlled_variables: Dict[str, Any]
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    evaluation_result: Dict[str, Any]
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.post("/propose", response_model=ExperimentResponse)
def propose_experiment(
    payload: ProposeExperimentRequest,
    db: Session = Depends(get_db),
):
    """
    Analyzes creator performance gaps to propose a structured A/B hypothesis test.
    Persists the proposed experiment in the database.
    """
    creator = db.get(Creator, payload.creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{payload.creator_id}' not found.",
        )

    posts = db.query(Post).filter_by(creator_id=payload.creator_id).all()
    post_dicts = [
        {
            "content_type": p.content_type,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "reach": p.reach,
            "engagement_rate": p.engagement_rate,
        }
        for p in posts
    ]

    metrics = calculate_aggregate_metrics(post_dicts)
    trends = detect_trends(post_dicts)

    exp_data = run_experiment_agent(
        creator_id=payload.creator_id,
        metrics=metrics,
        trends=trends,
        niche=payload.niche or creator.niche,
        use_llm=payload.use_llm,
        db=db,
    )

    return {
        "id": exp_data["id"],
        "creator_id": exp_data["creator_id"],
        "title": exp_data["title"],
        "hypothesis": exp_data["hypothesis"],
        "metric_target": exp_data["metric_target"],
        "status": exp_data["status"],
        "controlled_variables": exp_data["controlled_variables"],
        "variant_a": exp_data["variant_a"],
        "variant_b": exp_data["variant_b"],
        "evaluation_result": exp_data["evaluation_result"],
        "created_at": None,
        "completed_at": None,
    }


@router.post("", response_model=ExperimentResponse)
def create_custom_experiment(
    payload: CreateExperimentRequest,
    db: Session = Depends(get_db),
):
    """Manually registers an A/B experiment with custom hypothesis and variants."""
    creator = db.get(Creator, payload.creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{payload.creator_id}' not found.",
        )

    exp_id = str(uuid.uuid4())
    record = Experiment(
        id=exp_id,
        creator_id=payload.creator_id,
        title=payload.title,
        hypothesis=payload.hypothesis,
        metric_target=payload.metric_target or "engagement_rate",
        status="active",
        controlled_variables=payload.controlled_variables or {},
        variant_a=payload.variant_a,
        variant_b=payload.variant_b,
        evaluation_result={},
    )
    db.add(record)
    db.commit()

    return {
        "id": record.id,
        "creator_id": record.creator_id,
        "title": record.title,
        "hypothesis": record.hypothesis,
        "metric_target": record.metric_target,
        "status": record.status,
        "controlled_variables": record.controlled_variables or {},
        "variant_a": record.variant_a or {},
        "variant_b": record.variant_b or {},
        "evaluation_result": {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "completed_at": None,
    }


@router.get("", response_model=List[ExperimentResponse])
def list_experiments(
    creator_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists experiments with optional filtering by creator and status."""
    query = db.query(Experiment)
    if creator_id:
        query = query.filter_by(creator_id=creator_id)
    if status_filter:
        query = query.filter_by(status=status_filter.lower())

    records = query.order_by(desc(Experiment.created_at)).limit(limit).all()

    return [
        {
            "id": r.id,
            "creator_id": r.creator_id,
            "title": r.title,
            "hypothesis": r.hypothesis,
            "metric_target": r.metric_target,
            "status": r.status,
            "controlled_variables": r.controlled_variables or {},
            "variant_a": r.variant_a or {},
            "variant_b": r.variant_b or {},
            "evaluation_result": r.evaluation_result or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in records
    ]


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves full details of a specific experiment."""
    record = db.get(Experiment, experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    return {
        "id": record.id,
        "creator_id": record.creator_id,
        "title": record.title,
        "hypothesis": record.hypothesis,
        "metric_target": record.metric_target,
        "status": record.status,
        "controlled_variables": record.controlled_variables or {},
        "variant_a": record.variant_a or {},
        "variant_b": record.variant_b or {},
        "evaluation_result": record.evaluation_result or {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
    }


@router.post("/{experiment_id}/assign-posts", response_model=ExperimentResponse)
def assign_experiment_posts(
    experiment_id: str,
    payload: AssignPostsRequest,
    db: Session = Depends(get_db),
):
    """Assigns post IDs from ingested history to Variant A and Variant B."""
    record = db.get(Experiment, experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    va = dict(record.variant_a or {})
    vb = dict(record.variant_b or {})

    va["post_ids"] = payload.variant_a_post_ids
    vb["post_ids"] = payload.variant_b_post_ids

    record.variant_a = va
    record.variant_b = vb
    record.status = "active"
    db.commit()

    return {
        "id": record.id,
        "creator_id": record.creator_id,
        "title": record.title,
        "hypothesis": record.hypothesis,
        "metric_target": record.metric_target,
        "status": record.status,
        "controlled_variables": record.controlled_variables or {},
        "variant_a": record.variant_a or {},
        "variant_b": record.variant_b or {},
        "evaluation_result": record.evaluation_result or {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
    }


@router.post("/{experiment_id}/evaluate", response_model=ExperimentResponse)
def evaluate_experiment(
    experiment_id: str,
    alpha: float = Query(0.05, ge=0.01, le=0.10, description="Significance threshold (0.05 = 95% confidence)"),
    db: Session = Depends(get_db),
):
    """
    Evaluates statistical significance (Welch's t-test) across assigned posts.
    If conclusive, writes outcome back to creator Strategy memory (feedback loop).
    """
    record = db.get(Experiment, experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    va = record.variant_a or {}
    vb = record.variant_b or {}

    post_ids_a = va.get("post_ids", [])
    post_ids_b = vb.get("post_ids", [])

    if not post_ids_a or not post_ids_b:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot evaluate experiment without assigned posts. Call /assign-posts first.",
        )

    # Fetch metric values for each variant
    target_metric = record.metric_target or "engagement_rate"

    posts_a = db.query(Post).filter(Post.creator_id == record.creator_id, Post.post_id.in_(post_ids_a)).all()
    posts_b = db.query(Post).filter(Post.creator_id == record.creator_id, Post.post_id.in_(post_ids_b)).all()

    def _extract_metric(p: Post) -> float:
        if target_metric == "reach":
            return float(p.reach or 0)
        if p.engagement_rate is not None and p.engagement_rate > 0.0:
            return float(p.engagement_rate)
        calc = calculate_post_engagement_rate({
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "shares_count": p.shares_count,
            "saves_count": p.saves_count,
            "reach": p.reach,
            "impressions": p.impressions,
        })
        return float(calc or 0.0)

    values_a = [_extract_metric(p) for p in posts_a]
    values_b = [_extract_metric(p) for p in posts_b]

    eval_result = evaluate_experiment_metrics(values_a, values_b, alpha=alpha)

    record.evaluation_result = eval_result
    record.status = eval_result["status"]
    record.completed_at = utcnow()

    # Feedback Loop: If conclusive, update creator's active strategy memory
    if eval_result.get("is_significant") and eval_result.get("winner"):
        winner_name = vb.get("name", "Variant B") if eval_result["winner"] == "variant_b" else va.get("name", "Variant A")
        winning_insight = f"Validated via Experiment ({record.title}): '{winner_name}' outperformed with {eval_result['confidence_pct']:.1f}% confidence."

        latest_strat = (
            db.query(Strategy)
            .filter_by(creator_id=record.creator_id)
            .order_by(Strategy.created_at.desc())
            .first()
        )
        if latest_strat:
            priorities = list(latest_strat.strategic_priorities or [])
            priorities.insert(0, winning_insight)
            latest_strat.strategic_priorities = priorities

    db.commit()

    return {
        "id": record.id,
        "creator_id": record.creator_id,
        "title": record.title,
        "hypothesis": record.hypothesis,
        "metric_target": record.metric_target,
        "status": record.status,
        "controlled_variables": record.controlled_variables or {},
        "variant_a": record.variant_a or {},
        "variant_b": record.variant_b or {},
        "evaluation_result": record.evaluation_result or {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
    }
