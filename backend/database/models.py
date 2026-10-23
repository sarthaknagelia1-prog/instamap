"""
backend/database/models.py

SQLAlchemy ORM models for the core relational schema:
creators, posts (normalized engagement data), and ingestion logs.
"""

from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Creator(Base):
    __tablename__ = "creators"

    id = Column(String, primary_key=True)
    niche = Column(String, nullable=True)
    audience = Column(String, nullable=True)
    content_preferences = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)

    posts = relationship("Post", back_populates="creator", cascade="all, delete-orphan")
    ingestion_logs = relationship("IngestionLog", back_populates="creator", cascade="all, delete-orphan")
    orchestrator_runs = relationship("OrchestratorRun", back_populates="creator", cascade="all, delete-orphan")



class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint("creator_id", "post_id", name="uq_creator_post"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(String, ForeignKey("creators.id"), nullable=False)
    post_id = Column(String, nullable=False)

    content_type = Column(String, nullable=True)      # reel | carousel | image | story
    timestamp = Column(DateTime, nullable=True)

    likes_count = Column(Integer, nullable=True)
    comments_count = Column(Integer, nullable=True)
    shares_count = Column(Integer, nullable=True)
    saves_count = Column(Integer, nullable=True)
    reach = Column(Integer, nullable=True)
    impressions = Column(Integer, nullable=True)
    watch_time_avg = Column(Float, nullable=True)

    caption_text = Column(String, nullable=True)
    hashtags = Column(JSON, default=list)

    engagement_rate = Column(Float, nullable=True)     # computed downstream by analytics layer
    source = Column(String, nullable=True)             # csv_upload | instagram_graph_api | ...

    ingested_at = Column(DateTime, default=utcnow)

    creator = relationship("Creator", back_populates="posts")


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(String, ForeignKey("creators.id"), nullable=False)
    source = Column(String, nullable=False)

    data_ready = Column(Boolean, nullable=False)
    quality_score = Column(Float, nullable=False)
    missing_features = Column(JSON, default=list)
    available_features = Column(JSON, default=list)
    duplicate_records_removed = Column(Integer, default=0)
    invalid_timestamps = Column(Integer, default=0)
    record_count = Column(Integer, default=0)
    inserted_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=utcnow)

    creator = relationship("Creator", back_populates="ingestion_logs")


class OrchestratorRun(Base):
    __tablename__ = "orchestrator_runs"

    id = Column(String, primary_key=True)  # UUID string
    creator_id = Column(String, ForeignKey("creators.id"), nullable=False)
    status = Column(String, nullable=False, default="running")  # running | completed | failed
    trigger = Column(String, nullable=False, default="manual")  # manual | data_uploaded | scheduled
    decision = Column(String, nullable=True)  # generate_full_plan | report_only | request_more_data
    trace = Column(JSON, default=list)  # hop-by-hop audit trail
    result = Column(JSON, default=dict)  # final generated bundle / report

    created_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)

    creator = relationship("Creator", back_populates="orchestrator_runs")

