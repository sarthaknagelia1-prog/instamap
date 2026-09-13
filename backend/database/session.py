"""
backend/database/session.py

Engine, sessionmaker, and database lifecycle utilities.
"""

from __future__ import annotations
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.config import settings
from backend.database.models import Base

# Engine configured from settings
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session_factory(database_url: str | None = None) -> sessionmaker:
    """Returns a sessionmaker bound to the given URL or the default engine."""
    if database_url:
        custom_engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        )
        Base.metadata.create_all(custom_engine)
        return sessionmaker(autocommit=False, autoflush=False, bind=custom_engine)
    return SessionLocal


def init_db() -> None:
    """Creates all database tables defined in models."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
