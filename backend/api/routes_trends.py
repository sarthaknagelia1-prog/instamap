"""
backend/api/routes_trends.py

REST API Endpoints for Trend Sniffing:
- GET  /trends/sniff: Real-time and scored trend opportunities by niche
- POST /trends/sniff/custom: Custom subreddit or topic sniffing
- GET  /trends/cached: View currently active trending signals from PostgreSQL
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.session import get_db
from backend.database.models import TrendingSignal, utcnow
from backend.data.adapters.trend_sniffing_adapter import TrendSniffingAdapter, NICHE_SUBREDDITS

router = APIRouter(prefix="/trends", tags=["Trends"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class CustomSniffRequest(BaseModel):
    niche: Optional[str] = Field("Tech & AI", description="Target creator niche")
    subreddits: Optional[List[str]] = Field(None, description="Custom subreddits to monitor")
    limit: Optional[int] = Field(5, ge=1, le=20)


class TrendingSignalResponse(BaseModel):
    id: Optional[str] = None
    niche: str
    topic: str
    source: str
    velocity_score: float
    suggested_hook: str
    suggested_angle: str
    recommended_format: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.get("/niches")
def list_supported_niches():
    """Lists all natively supported creator niches and their mapped community radars."""
    return {
        "supported_niches": list(NICHE_SUBREDDITS.keys()),
        "default_sources": ["reddit_public_json", "google_trends_rss", "curated_viral_radar"],
    }


@router.get("/sniff", response_model=List[TrendingSignalResponse])
def sniff_trends(
    niche: str = Query("Tech & AI", description="Creator niche (e.g. 'Tech & AI', 'Fitness & Health')"),
    limit: int = Query(5, ge=1, le=20),
    use_network: bool = Query(True, description="Fetch live public network feeds (falls back to radar if offline)"),
    db: Session = Depends(get_db),
):
    """
    Discovers rising topics, debates, and queries for a given niche.
    Computes velocity scores and generates Instagram-native viral hooks.
    Persists signals into PostgreSQL with a 48h expiration window.
    """
    adapter = TrendSniffingAdapter()
    signals = adapter.sniff(niche=niche, limit=limit, use_network=use_network, db=db)

    return [
        {
            "id": None,
            "niche": niche,
            "topic": s["topic"],
            "source": s.get("source", "trend_sniffer"),
            "velocity_score": s.get("velocity_score", 50.0),
            "suggested_hook": s.get("suggested_hook", ""),
            "suggested_angle": s.get("suggested_angle", ""),
            "recommended_format": s.get("recommended_format", "reel"),
            "metadata": s.get("metadata", {}),
            "created_at": utcnow().isoformat(),
        }
        for s in signals
    ]


@router.post("/sniff/custom", response_model=List[TrendingSignalResponse])
def sniff_custom_trends(
    payload: CustomSniffRequest,
    db: Session = Depends(get_db),
):
    """Sniffs trends from custom user-specified subreddits and keywords."""
    adapter = TrendSniffingAdapter()
    results: List[Dict[str, Any]] = []

    if payload.subreddits:
        for sub in payload.subreddits:
            custom_items = adapter.fetch_reddit_trends(niche=sub, limit=payload.limit or 5)
            results.extend(custom_items)

    if not results:
        results = adapter.sniff(niche=payload.niche or "Tech & AI", limit=payload.limit or 5, db=db)

    return [
        {
            "id": None,
            "niche": payload.niche or "Custom",
            "topic": s["topic"],
            "source": s.get("source", "custom_trend_sniffer"),
            "velocity_score": s.get("velocity_score", 50.0),
            "suggested_hook": s.get("suggested_hook", ""),
            "suggested_angle": s.get("suggested_angle", ""),
            "recommended_format": s.get("recommended_format", "reel"),
            "metadata": s.get("metadata", {}),
            "created_at": utcnow().isoformat(),
        }
        for s in results[: payload.limit or 5]
    ]


@router.get("/cached", response_model=List[TrendingSignalResponse])
def get_cached_trending_signals(
    niche: Optional[str] = Query(None, description="Optional filter by niche"),
    db: Session = Depends(get_db),
):
    """Retrieves unexpired trending signals saved in PostgreSQL."""
    now = utcnow()
    query = db.query(TrendingSignal).filter(
        (TrendingSignal.expires_at == None) | (TrendingSignal.expires_at > now)
    )
    if niche:
        query = query.filter(TrendingSignal.niche.ilike(f"%{niche}%"))

    records = query.order_by(desc(TrendingSignal.velocity_score)).limit(20).all()

    return [
        {
            "id": r.id,
            "niche": r.niche,
            "topic": r.topic,
            "source": r.source,
            "velocity_score": r.velocity_score,
            "suggested_hook": r.suggested_hook,
            "suggested_angle": r.suggested_angle,
            "recommended_format": r.recommended_format,
            "metadata": r.metadata_json or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        }
        for r in records
    ]
