"""
backend/api/routes_creators.py

Creator Management Endpoints:
- GET /creators: List all creators with post counts and high-level health.
- GET /creators/{creator_id}: Get detailed profile for a single creator.
- GET /creators/{creator_id}/posts: Paginated post browser with filtering and sorting.
- GET /creators/{creator_id}/ingestion-logs: Full history of data uploads and quality scores.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func

from backend.database.session import get_db
from backend.database.models import Creator, Post, IngestionLog
from backend.security import get_current_user, verify_creator_access, User

router = APIRouter(prefix="/creators", tags=["Creators"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class CreatorListItem(BaseModel):
    id: str
    niche: Optional[str] = None
    audience: Optional[str] = None
    total_posts: int
    last_post_date: Optional[str] = None
    created_at: Optional[str] = None


class PostItemResponse(BaseModel):
    id: int
    post_id: str
    content_type: Optional[str] = None
    timestamp: Optional[str] = None
    likes_count: Optional[int] = None
    comments_count: Optional[int] = None
    shares_count: Optional[int] = None
    saves_count: Optional[int] = None
    reach: Optional[int] = None
    impressions: Optional[int] = None
    engagement_rate: Optional[float] = None
    caption_text: Optional[str] = None
    source: Optional[str] = None


class PaginatedPostsResponse(BaseModel):
    creator_id: str
    total_count: int
    page: int
    page_size: int
    posts: List[PostItemResponse]


class IngestionLogItem(BaseModel):
    id: int
    source: str
    data_ready: bool
    quality_score: float
    record_count: int
    inserted_count: int
    duplicate_records_removed: int
    invalid_timestamps: int
    created_at: Optional[str] = None


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.get("", response_model=List[CreatorListItem])
def list_creators(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists creators registered in the system scoped to the authenticated workspace."""
    query = db.query(Creator)
    if current_user.role != "admin":
        query = query.filter(Creator.workspace_id == current_user.workspace_id)
    if current_user.allowed_creators:
        query = query.filter(Creator.id.in_(current_user.allowed_creators))

    creators = query.all()
    result = []
    for c in creators:
        count = db.query(Post).filter_by(creator_id=c.id).count()
        latest_post = (
            db.query(Post)
            .filter_by(creator_id=c.id)
            .order_by(Post.timestamp.desc())
            .first()
        )
        result.append({
            "id": c.id,
            "niche": c.niche,
            "audience": c.audience,
            "total_posts": count,
            "last_post_date": latest_post.timestamp.isoformat() if latest_post and latest_post.timestamp else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return result


@router.get("/{creator_id}", response_model=CreatorListItem)
def get_creator(
    creator_id: str,
    creator: Creator = Depends(verify_creator_access),
    db: Session = Depends(get_db),
):
    """Returns details for a single creator if authorized."""
    count = db.query(Post).filter_by(creator_id=creator.id).count()
    latest_post = (
        db.query(Post)
        .filter_by(creator_id=creator.id)
        .order_by(Post.timestamp.desc())
        .first()
    )
    return {
        "id": creator.id,
        "niche": creator.niche,
        "audience": creator.audience,
        "total_posts": count,
        "last_post_date": latest_post.timestamp.isoformat() if latest_post and latest_post.timestamp else None,
        "created_at": creator.created_at.isoformat() if creator.created_at else None,
    }


@router.get("/{creator_id}/posts", response_model=PaginatedPostsResponse)
def get_creator_posts(
    creator_id: str,
    content_type: Optional[str] = Query(None, description="Filter by reel, carousel, image"),
    sort_by: str = Query("timestamp", description="Sort by timestamp, engagement_rate, likes, reach"),
    order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    creator: Creator = Depends(verify_creator_access),
    db: Session = Depends(get_db),
):
    """Returns a paginated list of posts for an authorized creator."""
    query = db.query(Post).filter_by(creator_id=creator.id)

    if content_type:
        query = query.filter(Post.content_type == content_type.lower())

    # Map sort column
    sort_col_map = {
        "timestamp": Post.timestamp,
        "engagement_rate": Post.engagement_rate,
        "likes": Post.likes_count,
        "reach": Post.reach,
        "comments": Post.comments_count,
    }
    sort_column = sort_col_map.get(sort_by, Post.timestamp)
    query = query.order_by(desc(sort_column) if order.lower() == "desc" else asc(sort_column))

    total_count = query.count()
    offset = (page - 1) * page_size
    posts = query.offset(offset).limit(page_size).all()

    items = [
        {
            "id": p.id,
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
            "caption_text": p.caption_text,
            "source": p.source,
        }
        for p in posts
    ]

    return {
        "creator_id": creator.id,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "posts": items,
    }


@router.get("/{creator_id}/ingestion-logs", response_model=List[IngestionLogItem])
def get_creator_ingestion_logs(
    creator_id: str,
    creator: Creator = Depends(verify_creator_access),
    db: Session = Depends(get_db),
):
    """Returns audit logs of past data upload and ingestion runs for an authorized creator."""
    logs = (
        db.query(IngestionLog)
        .filter_by(creator_id=creator.id)
        .order_by(IngestionLog.created_at.desc())
        .all()
    )

    return [
        {
            "id": log.id,
            "source": log.source,
            "data_ready": log.data_ready,
            "quality_score": log.quality_score,
            "record_count": log.record_count,
            "inserted_count": log.inserted_count,
            "duplicate_records_removed": log.duplicate_records_removed,
            "invalid_timestamps": log.invalid_timestamps,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
