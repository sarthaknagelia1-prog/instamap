"""
backend/api/routes_analytics.py

Analytics and Performance endpoints:
- POST /analyze-performance: Full performance analysis for a creator.
- GET /analytics/summary: Lightweight dashboard summary.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Post, Creator
from backend.analytics.metrics import calculate_aggregate_metrics, calculate_post_engagement_rate
from backend.analytics.trends import detect_trends, find_best_posting_window
from backend.analytics.anomalies import detect_anomalies
from backend.agents.analyst_agent import run_analyst_agent

router = APIRouter(tags=["Analytics"])


class AnalyzePerformanceRequest(BaseModel):
    creator_id: str = Field(..., description="The creator ID to analyze")
    limit: Optional[int] = Field(100, description="Max number of recent posts to analyze")


class PerformanceAnalysisResponse(BaseModel):
    creator_id: str
    top_content_type: str
    average_engagement_rate: float
    best_posting_window: str
    recent_trend: str
    week_over_week_delta_pct: float
    recommended_action: str
    analysis_summary: str
    content_type_breakdown: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    top_performing_posts: List[Dict[str, Any]]


class AnalyticsSummaryResponse(BaseModel):
    creator_id: str
    total_posts: int
    average_engagement_rate: float
    top_content_type: str
    recent_trend: str
    best_posting_window: str


@router.post("/analyze-performance", response_model=PerformanceAnalysisResponse)
def analyze_performance(
    payload: AnalyzePerformanceRequest,
    db: Session = Depends(get_db),
):
    """
    Executes full performance analysis on a creator's ingested posts:
    1. Computes engagement metrics and per-content-type breakdown.
    2. Identifies rolling trends and week-over-week deltas.
    3. Finds optimal posting window.
    4. Detects sudden anomalies (spikes/drops).
    5. Updates post engagement rates in the database.
    6. Calls Analyst Agent for recommended actions.
    """
    creator = db.get(Creator, payload.creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{payload.creator_id}' not found.",
        )

    posts_query = (
        db.query(Post)
        .filter_by(creator_id=payload.creator_id)
        .order_by(Post.timestamp.desc())
        .limit(payload.limit)
    )
    posts = posts_query.all()

    if not posts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No post data found for creator '{payload.creator_id}'. Ingest data first.",
        )

    # Convert to dicts for analytics processing
    post_dicts = []
    for p in posts:
        er = calculate_post_engagement_rate({
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "shares_count": p.shares_count,
            "saves_count": p.saves_count,
            "reach": p.reach,
            "impressions": p.impressions,
        })
        # Persist updated computed engagement_rate to DB
        p.engagement_rate = er

        post_dicts.append({
            "post_id": p.post_id,
            "content_type": p.content_type,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "shares_count": p.shares_count,
            "saves_count": p.saves_count,
            "reach": p.reach,
            "impressions": p.impressions,
            "engagement_rate": er,
            "caption_text": p.caption_text,
        })

    db.commit()

    # Compute analytics
    metrics = calculate_aggregate_metrics(post_dicts)
    trends = detect_trends(post_dicts)
    best_window = find_best_posting_window(post_dicts)
    anomalies = detect_anomalies(post_dicts)

    # Run Performance Analyst Agent
    result = run_analyst_agent(
        creator_id=payload.creator_id,
        metrics=metrics,
        trends=trends,
        best_posting_window=best_window,
        anomalies=anomalies,
    )

    return result


import time

# Thread-safe in-memory cache for dashboard summary: creator_id -> (timestamp, data)
_SUMMARY_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes cache


def invalidate_analytics_cache(creator_id: Optional[str] = None) -> None:
    """Invalidates the summary cache for a specific creator or completely."""
    if creator_id:
        _SUMMARY_CACHE.pop(creator_id, None)
    else:
        _SUMMARY_CACHE.clear()


class TimeSeriesPoint(BaseModel):
    post_id: str
    timestamp: Optional[str] = None
    content_type: Optional[str] = None
    engagement_rate: Optional[float] = None
    likes_count: Optional[int] = None
    comments_count: Optional[int] = None
    saves_count: Optional[int] = None
    reach: Optional[int] = None


class TimeSeriesResponse(BaseModel):
    creator_id: str
    total_data_points: int
    series: List[TimeSeriesPoint]


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    creator_id: str = Query(..., description="Creator identifier"),
    db: Session = Depends(get_db),
):
    """Returns quick overview summary metrics for dashboard display (cached)."""
    now = time.time()
    cached = _SUMMARY_CACHE.get(creator_id)
    if cached and (now - cached[0] < CACHE_TTL_SECONDS):
        return cached[1]

    creator = db.get(Creator, creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{creator_id}' not found.",
        )

    posts = db.query(Post).filter_by(creator_id=creator_id).all()
    if not posts:
        empty_summary = {
            "creator_id": creator_id,
            "total_posts": 0,
            "average_engagement_rate": 0.0,
            "top_content_type": "none",
            "recent_trend": "stable",
            "best_posting_window": "Insufficient data",
        }
        _SUMMARY_CACHE[creator_id] = (now, empty_summary)
        return empty_summary

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
    best_window = find_best_posting_window(post_dicts)

    summary = {
        "creator_id": creator_id,
        "total_posts": len(posts),
        "average_engagement_rate": metrics.get("average_engagement_rate", 0.0),
        "top_content_type": metrics.get("top_content_type", "unknown"),
        "recent_trend": trends.get("recent_trend", "stable"),
        "best_posting_window": best_window,
    }
    _SUMMARY_CACHE[creator_id] = (now, summary)
    return summary


@router.get("/analytics/performance/{creator_id}")
def get_creator_performance_analytics(
    creator_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns full overview performance analytics for a creator matching
    both frontend React client and the dashboard SPA requirements.
    """
    creator = db.get(Creator, creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{creator_id}' not found.",
        )

    posts = (
        db.query(Post)
        .filter_by(creator_id=creator_id)
        .order_by(Post.timestamp.desc())
        .all()
    )
    if not posts:
        return {
            "creator_id": creator_id,
            "metrics": {
                "total_posts": 0,
                "average_engagement_rate": 0.0,
                "top_content_type": "reel",
                "total_reach": 0,
            },
            "trends": {
                "recent_trend": "stable",
                "week_over_week_delta_pct": 0.0,
            },
            "best_posting_window": "Insufficient data",
            "average_engagement_rate": 0.0,
            "total_reach": 0,
            "top_content_type": "reel",
            "recent_trend": "stable",
            "week_over_week_delta_pct": 0.0,
        }

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
    best_window = find_best_posting_window(post_dicts)

    total_reach = sum(p.reach or 0 for p in posts)
    avg_er = metrics.get("average_engagement_rate", 0.0)
    top_format = metrics.get("top_content_type", "reel")
    wow = trends.get("week_over_week_delta_pct", 0.0)
    recent_trend = trends.get("recent_trend", "stable")

    return {
        "creator_id": creator_id,
        "metrics": {
            "total_posts": len(posts),
            "average_engagement_rate": avg_er,
            "top_content_type": top_format,
            "total_reach": total_reach,
            "content_type_breakdown": metrics.get("content_type_breakdown", {}),
        },
        "trends": {
            "recent_trend": recent_trend,
            "week_over_week_delta_pct": wow,
        },
        "best_posting_window": best_window,
        "average_engagement_rate": avg_er,
        "total_reach": total_reach,
        "top_content_type": top_format,
        "recent_trend": recent_trend,
        "week_over_week_delta_pct": wow,
    }



@router.get("/analytics/time-series", response_model=TimeSeriesResponse)
def get_analytics_time_series(
    creator_id: str = Query(..., description="Creator identifier"),
    limit: int = Query(50, ge=5, le=500, description="Number of recent posts to plot"),
    db: Session = Depends(get_db),
):
    """
    Returns chronologically ordered metrics (date, engagement rate, reach, likes)
    designed directly for rendering frontend line/bar charts.
    """
    creator = db.get(Creator, creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{creator_id}' not found.",
        )

    posts = (
        db.query(Post)
        .filter_by(creator_id=creator_id)
        .order_by(Post.timestamp.asc())
        .limit(limit)
        .all()
    )

    series_data = [
        {
            "post_id": p.post_id,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "content_type": p.content_type,
            "engagement_rate": p.engagement_rate,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "saves_count": p.saves_count,
            "reach": p.reach,
        }
        for p in posts
    ]

    return {
        "creator_id": creator_id,
        "total_data_points": len(series_data),
        "series": series_data,
    }

