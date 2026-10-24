"""
backend/api/routes_content.py

Phase 4 API Endpoints for Strategy & Content:
- POST /strategy/generate: Formulate growth strategy for a creator.
- GET /strategy/{creator_id}: Retrieve the latest strategy for a creator.
- POST /content/plan: Generate a weekly content calendar.
- POST /content/generate: Generate ready-to-post drafts for planned items.
- GET /content/drafts: List all drafts with status/format filtering.
- GET /content/drafts/{draft_id}: Inspect a single content draft.
- PATCH /content/drafts/{draft_id}/status: Update status (draft -> approved / published).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.session import get_db
from backend.database.models import Creator, Strategy, ContentPlan, ContentDraft, Post
from backend.security import get_current_user, verify_creator_access, User
from backend.analytics.metrics import calculate_aggregate_metrics
from backend.analytics.trends import detect_trends, find_best_posting_window
from backend.agents.strategy_agent import run_strategy_agent
from backend.agents.content_planning_agent import run_content_planning_agent
from backend.agents.content_generation_agent import run_content_generation_agent

router = APIRouter(tags=["Strategy & Content"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class GenerateStrategyRequest(BaseModel):
    creator_id: str
    niche: Optional[str] = None
    audience: Optional[str] = None
    use_llm: bool = False


class StrategyResponse(BaseModel):
    strategy_id: str
    creator_id: str
    primary_content_type: str
    format_allocation: Dict[str, int]
    core_pillars: List[str]
    target_cadence: str
    target_audience: Optional[str] = None
    tone_of_voice: Optional[str] = None
    strategic_priorities: List[str]


class GeneratePlanRequest(BaseModel):
    creator_id: str
    strategy_id: Optional[str] = None
    week_number: int = 1


class ContentPlanResponse(BaseModel):
    plan_id: str
    creator_id: str
    strategy_id: Optional[str] = None
    week_number: int
    planned_post_count: int
    scheduled_items: List[Dict[str, Any]]


class GenerateDraftsRequest(BaseModel):
    creator_id: str
    plan_id: Optional[str] = None
    use_llm: bool = False
    custom_item: Optional[Dict[str, Any]] = None


class DraftResponse(BaseModel):
    id: str
    creator_id: str
    plan_id: Optional[str] = None
    content_type: str
    title: str
    hook: str
    body: str
    call_to_action: str
    hashtags: List[str]
    visual_direction: Optional[str] = None
    audio_suggestion: Optional[str] = None
    recommended_time: Optional[str] = None
    status: str
    published_at: Optional[str] = None
    published_post_id: Optional[str] = None
    created_at: Optional[str] = None


class UpdateDraftStatusRequest(BaseModel):
    status: str = Field(..., description="approved | published | archived | draft")


class MarkPublishedRequest(BaseModel):
    published_post_id: str = Field(..., description="Instagram post ID or permalink URL")


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.post("/strategy/generate", response_model=StrategyResponse)
def generate_strategy(
    payload: GenerateStrategyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates and persists a customized growth strategy based on creator performance."""
    creator = verify_creator_access(payload.creator_id, db=db, current_user=current_user)

    posts = db.query(Post).filter_by(creator_id=payload.creator_id).all()
    post_dicts = [
        {
            "post_id": p.post_id,
            "content_type": p.content_type,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "shares_count": p.shares_count,
            "saves_count": p.saves_count,
            "reach": p.reach,
            "impressions": p.impressions,
            "engagement_rate": p.engagement_rate,
        }
        for p in posts
    ]

    metrics = calculate_aggregate_metrics(post_dicts)
    trends = detect_trends(post_dicts)

    strategy_res = run_strategy_agent(
        creator_id=payload.creator_id,
        metrics=metrics,
        trends=trends,
        niche=payload.niche or creator.niche,
        audience=payload.audience or creator.audience,
        use_llm=payload.use_llm,
        db=db,
    )

    return strategy_res


@router.get("/strategy/{creator_id}", response_model=StrategyResponse)
def get_latest_strategy(
    creator_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves the latest active strategy for an authorized creator."""
    verify_creator_access(creator_id, db=db, current_user=current_user)
    strat = (
        db.query(Strategy)
        .filter_by(creator_id=creator_id)
        .order_by(Strategy.created_at.desc())
        .first()
    )
    if not strat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No strategy found for creator '{creator_id}'. Generate one via POST /strategy/generate first.",
        )

    return {
        "strategy_id": strat.id,
        "creator_id": strat.creator_id,
        "primary_content_type": strat.primary_content_type,
        "format_allocation": strat.format_allocation or {},
        "core_pillars": strat.core_pillars or [],
        "target_cadence": strat.target_cadence or "4 posts/week",
        "target_audience": strat.target_audience,
        "tone_of_voice": strat.tone_of_voice,
        "strategic_priorities": strat.strategic_priorities or [],
    }


@router.post("/content/plan", response_model=ContentPlanResponse)
def create_content_plan(
    payload: GeneratePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates a 7-day content schedule matching the creator's active strategy."""
    creator = verify_creator_access(payload.creator_id, db=db, current_user=current_user)

    # Fetch strategy
    strat = None
    if payload.strategy_id:
        strat = db.get(Strategy, payload.strategy_id)
    if not strat:
        strat = (
            db.query(Strategy)
            .filter_by(creator_id=payload.creator_id)
            .order_by(Strategy.created_at.desc())
            .first()
        )

    strat_dict = {}
    if strat:
        strat_dict = {
            "strategy_id": strat.id,
            "primary_content_type": strat.primary_content_type,
            "core_pillars": strat.core_pillars,
        }

    # Best posting window
    posts = db.query(Post).filter_by(creator_id=payload.creator_id).all()
    post_dicts = [{"timestamp": p.timestamp.isoformat() if p.timestamp else None, "likes_count": p.likes_count, "comments_count": p.comments_count, "reach": p.reach} for p in posts]
    best_window = find_best_posting_window(post_dicts)

    plan_res = run_content_planning_agent(
        creator_id=payload.creator_id,
        strategy=strat_dict,
        best_posting_window=best_window,
        week_number=payload.week_number,
        db=db,
    )

    return plan_res


@router.post("/content/plans/generate")
def generate_content_plan_alias(
    payload: GeneratePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alias for POST /content/plan to generate a weekly plan."""
    return create_content_plan(payload, db=db, current_user=current_user)


@router.get("/content/plans/{creator_id}")
@router.get("/content/plan/{creator_id}")
def get_latest_content_plan(
    creator_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves the latest 7-day content schedule for an authorized creator, or auto-generates one if posts exist."""
    creator = verify_creator_access(creator_id, db=db, current_user=current_user)

    plan = (
        db.query(ContentPlan)
        .filter_by(creator_id=creator_id)
        .order_by(ContentPlan.created_at.desc())
        .first()
    )
    if not plan:
        # If creator has posts, generate a plan automatically
        posts = db.query(Post).filter_by(creator_id=creator_id).all()
        if posts:
            strat = (
                db.query(Strategy)
                .filter_by(creator_id=creator_id)
                .order_by(Strategy.created_at.desc())
                .first()
            )
            strat_dict = {
                "strategy_id": strat.id,
                "primary_content_type": strat.primary_content_type,
                "core_pillars": strat.core_pillars,
            } if strat else {}

            post_dicts = [{"timestamp": p.timestamp.isoformat() if p.timestamp else None, "likes_count": p.likes_count, "comments_count": p.comments_count, "reach": p.reach} for p in posts]
            best_window = find_best_posting_window(post_dicts)

            return run_content_planning_agent(
                creator_id=creator_id,
                strategy=strat_dict,
                best_posting_window=best_window,
                week_number=1,
                db=db,
            )
        raise HTTPException(status_code=404, detail="No content plan found. Ingest posts or generate a plan.")

    return {
        "plan_id": plan.id,
        "creator_id": plan.creator_id,
        "week_number": plan.week_number,
        "scheduled_items": plan.scheduled_items or [],
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }


@router.post("/content/generate", response_model=List[DraftResponse])
def generate_content_drafts(
    payload: GenerateDraftsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates ready-to-post content drafts for all items in a content plan
    or for a single custom item. Persists items to the ContentDraft table.
    """
    creator = verify_creator_access(payload.creator_id, db=db, current_user=current_user)

    items_to_generate: List[Dict[str, Any]] = []

    if payload.custom_item:
        items_to_generate.append(payload.custom_item)
    elif payload.plan_id:
        plan = db.get(ContentPlan, payload.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        items_to_generate = plan.scheduled_items or []
    else:
        # Fall back to latest plan
        plan = (
            db.query(ContentPlan)
            .filter_by(creator_id=payload.creator_id)
            .order_by(ContentPlan.created_at.desc())
            .first()
        )
        if plan and plan.scheduled_items:
            items_to_generate = plan.scheduled_items
        else:
            # Fallback default items
            items_to_generate = [
                {"content_type": "reel", "theme": "Growth Breakdown", "concept_angle": "Step by step framework"},
                {"content_type": "carousel", "theme": "Case Study", "concept_angle": "Data comparison and action steps"},
            ]

    created_drafts = []
    for item in items_to_generate:
        draft = run_content_generation_agent(
            creator_id=payload.creator_id,
            plan_item=item,
            plan_id=payload.plan_id,
            niche=creator.niche,
            use_llm=payload.use_llm,
            db=db,
        )
        from backend.api.routes_approvals import enqueue_approval_item
        enqueue_approval_item(
            creator_id=payload.creator_id,
            item_type="content_draft",
            item_id=draft["draft_id"],
            action_type="draft_approval",
            summary=f"Draft ({draft['content_type'].upper()}): {draft['title']}",
            payload_snapshot=draft,
            risk_level="high",
            db=db,
        )
        created_drafts.append({
            "id": draft["draft_id"],
            "creator_id": draft["creator_id"],
            "plan_id": draft["plan_id"],
            "content_type": draft["content_type"],
            "title": draft["title"],
            "hook": draft["hook"],
            "body": draft["body"],
            "call_to_action": draft["call_to_action"],
            "hashtags": draft["hashtags"],
            "visual_direction": draft["visual_direction"],
            "audio_suggestion": draft["audio_suggestion"],
            "recommended_time": draft["recommended_time"],
            "status": draft["status"],
            "created_at": None,
        })

    return created_drafts


@router.get("/content/drafts", response_model=List[DraftResponse])
def list_content_drafts(
    creator_id: Optional[str] = Query(None, description="Filter by creator"),
    status_filter: Optional[str] = Query(None, alias="status", description="draft | approved | published | archived"),
    content_type: Optional[str] = Query(None, description="reel | carousel | image | story"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists drafted content packages with tenant isolation and optional filtering."""
    query = db.query(ContentDraft)
    if creator_id:
        verify_creator_access(creator_id, db=db, current_user=current_user)
        query = query.filter_by(creator_id=creator_id)
    else:
        # Scope drafts to creators in the user's workspace unless admin
        if current_user.role != "admin":
            from sqlalchemy import select
            workspace_creators = select(Creator.id).filter(Creator.workspace_id == current_user.workspace_id)
            query = query.filter(ContentDraft.creator_id.in_(workspace_creators))

    if status_filter:
        query = query.filter_by(status=status_filter.lower())
    if content_type:
        query = query.filter_by(content_type=content_type.lower())

    drafts = query.order_by(desc(ContentDraft.created_at)).limit(limit).all()

    return [
        {
            "id": d.id,
            "creator_id": d.creator_id,
            "plan_id": d.plan_id,
            "content_type": d.content_type,
            "title": d.title,
            "hook": d.hook,
            "body": d.body,
            "call_to_action": d.call_to_action,
            "hashtags": d.hashtags or [],
            "visual_direction": d.visual_direction,
            "audio_suggestion": d.audio_suggestion,
            "recommended_time": d.recommended_time,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in drafts
    ]


@router.get("/content/drafts/{draft_id}", response_model=DraftResponse)
def get_content_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves full details for a single content draft with tenant authorization."""
    draft = db.get(ContentDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    verify_creator_access(draft.creator_id, db=db, current_user=current_user)

    return {
        "id": draft.id,
        "creator_id": draft.creator_id,
        "plan_id": draft.plan_id,
        "content_type": draft.content_type,
        "title": draft.title,
        "hook": draft.hook,
        "body": draft.body,
        "call_to_action": draft.call_to_action,
        "hashtags": draft.hashtags or [],
        "visual_direction": draft.visual_direction,
        "audio_suggestion": draft.audio_suggestion,
        "recommended_time": draft.recommended_time,
        "status": draft.status,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }


@router.patch("/content/drafts/{draft_id}/status", response_model=DraftResponse)
def update_draft_status(
    draft_id: str,
    payload: UpdateDraftStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates status of a draft with authorization."""
    draft = db.get(ContentDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    verify_creator_access(draft.creator_id, db=db, current_user=current_user)

    draft.status = payload.status.lower()
    db.commit()

    return {
        "id": draft.id,
        "creator_id": draft.creator_id,
        "plan_id": draft.plan_id,
        "content_type": draft.content_type,
        "title": draft.title,
        "hook": draft.hook,
        "body": draft.body,
        "call_to_action": draft.call_to_action,
        "hashtags": draft.hashtags or [],
        "visual_direction": draft.visual_direction,
        "audio_suggestion": draft.audio_suggestion,
        "recommended_time": draft.recommended_time,
        "status": draft.status,
        "published_at": draft.published_at.isoformat() if draft.published_at else None,
        "published_post_id": draft.published_post_id,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }


@router.post("/content/drafts/{draft_id}/mark-published", response_model=DraftResponse)
def mark_draft_published(
    draft_id: str,
    payload: MarkPublishedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Marks an approved draft as manually published by an authorized creator.
    Records the actual Instagram post ID or permalink URL and timestamps publication.
    """
    draft = db.get(ContentDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    verify_creator_access(draft.creator_id, db=db, current_user=current_user)

    from backend.database.models import utcnow
    now = utcnow()
    draft.status = "published"
    draft.published_at = now
    draft.published_post_id = payload.published_post_id.strip()
    db.commit()

    return {
        "id": draft.id,
        "creator_id": draft.creator_id,
        "plan_id": draft.plan_id,
        "content_type": draft.content_type,
        "title": draft.title,
        "hook": draft.hook,
        "body": draft.body,
        "call_to_action": draft.call_to_action,
        "hashtags": draft.hashtags or [],
        "visual_direction": draft.visual_direction,
        "audio_suggestion": draft.audio_suggestion,
        "recommended_time": draft.recommended_time,
        "status": draft.status,
        "published_at": draft.published_at.isoformat(),
        "published_post_id": draft.published_post_id,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }

