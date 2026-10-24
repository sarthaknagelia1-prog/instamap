"""
backend/data/ingestion/ingest.py

End-to-end ingestion pipeline:
    Adapter (CSV / Graph API) -> Data Readiness Agent -> Database (Postgres / SQLite)

Backs the POST /data-readiness and POST /data/ingest API endpoints.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, sessionmaker

from backend.data.ingestion.data_readiness_agent import run as run_data_readiness
from backend.analytics.metrics import calculate_post_engagement_rate
from backend.database.models import Creator, Post, IngestionLog
from backend.database.session import get_session_factory, SessionLocal


def _upsert_creator(session: Session, creator_id: str, workspace_id: Optional[str] = None) -> Creator:
    creator = session.get(Creator, creator_id)
    if creator is None:
        creator = Creator(id=creator_id, workspace_id=workspace_id or "default")
        session.add(creator)
        session.flush()
    return creator


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def persist_records(
    session: Session,
    creator_id: str,
    source: str,
    records: List[Dict[str, Any]],
    workspace_id: Optional[str] = None,
) -> int:
    """Upserts normalized post records into the database. Returns rows inserted/updated."""
    _upsert_creator(session, creator_id, workspace_id=workspace_id)
    inserted = 0

    for record in records:
        post_id = record.get("post_id")
        if not post_id:
            continue

        existing = (
            session.query(Post)
            .filter_by(creator_id=creator_id, post_id=post_id)
            .one_or_none()
        )
        target = existing or Post(creator_id=creator_id, post_id=post_id)

        target.content_type = record.get("content_type")
        target.timestamp = _parse_dt(record.get("timestamp"))
        target.likes_count = record.get("likes_count")
        target.comments_count = record.get("comments_count")
        target.shares_count = record.get("shares_count")
        target.saves_count = record.get("saves_count")
        target.reach = record.get("reach")
        target.impressions = record.get("impressions")
        target.watch_time_avg = record.get("watch_time_avg")
        target.caption_text = record.get("caption_text")
        target.hashtags = record.get("hashtags") or []
        target.engagement_rate = calculate_post_engagement_rate(record)
        target.source = source

        if not existing:
            session.add(target)
            inserted += 1

    return inserted


def run_ingestion(
    session_or_factory: Session | sessionmaker | None,
    creator_id: str,
    source: str,
    raw_data: List[Dict[str, Any]],
    quality_threshold: float = 0.5,
    workspace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full pipeline: readiness check -> (if ready) persist -> log outcome.
    Works with either a live Session or a sessionmaker factory.
    """
    readiness_result = run_data_readiness(
        {"creator_id": creator_id, "source": source, "raw_data": raw_data},
        quality_threshold=quality_threshold,
    )

    def _execute(session: Session) -> int:
        inserted = 0
        if readiness_result["data_ready"]:
            inserted = persist_records(
                session, creator_id, source, readiness_result["processed_data"], workspace_id=workspace_id
            )

        log = IngestionLog(
            creator_id=creator_id,
            source=source,
            data_ready=readiness_result["data_ready"],
            quality_score=readiness_result["quality_score"],
            missing_features=readiness_result["missing_features"],
            available_features=readiness_result["available_features"],
            duplicate_records_removed=readiness_result["duplicate_records_removed"],
            invalid_timestamps=readiness_result["invalid_timestamps"],
            record_count=readiness_result["record_count"],
            inserted_count=inserted,
        )
        session.add(log)
        session.commit()
        return inserted

    if isinstance(session_or_factory, Session):
        inserted_count = _execute(session_or_factory)
    elif session_or_factory is not None:
        with session_or_factory() as session:
            inserted_count = _execute(session)
    else:
        with SessionLocal() as session:
            inserted_count = _execute(session)

    return {**readiness_result, "inserted_count": inserted_count}
