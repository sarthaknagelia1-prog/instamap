"""
ingest.py

End-to-end ingestion pipeline:

    Adapter (CSV / Graph API) -> Data Readiness Agent -> Postgres

This is the concrete implementation behind the design doc's
Section 15, Step 1-2 ("Data Ingestion" / "Data Validation") and backs
the POST /data-readiness and POST /data/ingest API endpoints.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from data.ingestion.data_readiness_agent import run as run_data_readiness
from database.models import Base, Creator, Post, IngestionLog


def get_session_factory(database_url: str) -> sessionmaker:
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _upsert_creator(session: Session, creator_id: str) -> Creator:
    creator = session.get(Creator, creator_id)
    if creator is None:
        creator = Creator(id=creator_id)
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


def persist_records(session: Session, creator_id: str, source: str, records: list[Dict[str, Any]]) -> int:
    """Upserts normalized post records into the database. Returns rows inserted."""
    _upsert_creator(session, creator_id)
    inserted = 0

    for record in records:
        post_id = record.get("post_id")
        if not post_id:
            continue  # can't safely dedupe/store without an identifier

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
        target.source = source

        if not existing:
            session.add(target)
            inserted += 1

    return inserted


def run_ingestion(
    session_factory: sessionmaker,
    creator_id: str,
    source: str,
    raw_data: list[Dict[str, Any]],
    quality_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Full pipeline: readiness check -> (if ready) persist -> log outcome.
    Mirrors the response shape of POST /data-readiness, with an added
    'inserted_count' once persistence has occurred.
    """
    readiness_result = run_data_readiness(
        {"creator_id": creator_id, "source": source, "raw_data": raw_data},
        quality_threshold=quality_threshold,
    )

    inserted_count = 0
    with session_factory() as session:
        if readiness_result["data_ready"]:
            inserted_count = persist_records(
                session, creator_id, source, readiness_result["processed_data"]
            )

        session.add(IngestionLog(
            creator_id=creator_id,
            source=source,
            data_ready=readiness_result["data_ready"],
            quality_score=readiness_result["quality_score"],
            missing_features=readiness_result["missing_features"],
            available_features=readiness_result["available_features"],
            duplicate_records_removed=readiness_result["duplicate_records_removed"],
            invalid_timestamps=readiness_result["invalid_timestamps"],
            record_count=readiness_result["record_count"],
            inserted_count=inserted_count,
        ))
        session.commit()

    return {**readiness_result, "inserted_count": inserted_count}


if __name__ == "__main__":
    # Example: ingest a CSV export end-to-end against a local SQLite DB
    import sys
    from data.adapters.csv_adapter import CSVAdapter

    if len(sys.argv) < 3:
        print("Usage: python ingest.py <creator_id> <path_to_csv>")
        sys.exit(1)

    creator_id_arg, csv_path = sys.argv[1], sys.argv[2]

    adapter = CSVAdapter()
    payload = adapter.load(file_path=csv_path)

    session_factory = get_session_factory("sqlite:///growth_engine.db")
    result = run_ingestion(
        session_factory,
        creator_id=creator_id_arg,
        source=payload["source"],
        raw_data=payload["raw_data"],
    )

    print(result)
