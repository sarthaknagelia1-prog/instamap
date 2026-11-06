"""
tests/conftest.py

Shared pytest fixtures: in-memory test database, FastAPI TestClient, and sample records.
"""

from __future__ import annotations
import os
import tempfile
import uuid

# Keep tests independent from credentials and availability of a developer's configured database.
_test_db_path = os.path.join(tempfile.gettempdir(), f"instagram-growth-engine-{uuid.uuid4().hex}.sqlite3")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path.replace(os.sep, '/')}"
os.environ["ENVIRONMENT"] = "development"
os.environ["REQUIRE_AUTH"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base
from backend.database.session import get_db
from backend.main import app


@pytest.fixture(scope="session")
def test_engine():
    """Provides an in-memory SQLite engine shared across connections."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provides a fresh, isolated database session per test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionTest = sessionmaker(bind=connection)
    session = SessionTest()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a FastAPI TestClient wired to the test database session."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, headers={"Origin": "http://localhost:5173"}) as test_client:
        yield test_client
    app.dependency_overrides.clear()
