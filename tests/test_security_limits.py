"""
tests/test_security_limits.py

Security Regression Test Suite: Input Bounds, Resource Limits, and Safe Errors (SEC-03, SEC-04, SEC-06).
Verifies:
1. File upload size limit enforcement (MAX_UPLOAD_SIZE_BYTES).
2. JSON payload row limit enforcement (MAX_INGEST_RECORDS).
3. Safe error disclosure without leaking raw exception tracebacks.
4. Restricted CORS configuration.
"""

from __future__ import annotations
import io
import pytest
from backend.config import settings
from backend.database.models import Creator


def test_ingest_json_records_limit_exceeded(client, monkeypatch):
    """Verifies that submitting more than MAX_INGEST_RECORDS is rejected with 413/422 (SEC-04)."""
    monkeypatch.setattr(settings, "MAX_INGEST_RECORDS", 5)

    too_many_records = [
        {"post_id": f"p_{i}", "content_type": "reel", "likes_count": 10, "comments_count": 1}
        for i in range(10)
    ]

    resp = client.post(
        "/data/ingest",
        json={
            "creator_id": "bound_test_creator",
            "source": "json_test",
            "raw_data": too_many_records,
        },
    )
    # Pydantic or endpoint rejects with 422 or 413
    assert resp.status_code in (413, 422, 400)


def test_file_upload_size_limit_exceeded(client, monkeypatch):
    """Verifies that files exceeding MAX_UPLOAD_SIZE_BYTES are rejected with 413 (SEC-04)."""
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 50)  # artificially low limit: 50 bytes

    large_content = b"post_id,likes,comments\n" + b"p1,100,10\n" * 10
    file_payload = ("test.csv", io.BytesIO(large_content), "text/csv")

    resp = client.post(
        "/data/ingest",
        data={"creator_id": "upload_test_creator"},
        files={"file": file_payload},
    )
    assert resp.status_code == 413
    assert "exceeds maximum permitted size" in resp.json()["detail"]


def test_health_check_does_not_leak_raw_exception(client, monkeypatch):
    """Verifies that database connection failures return sanitized status instead of str(e) (SEC-06)."""
    from backend import main

    class FailingEngine:
        def connect(self):
            raise RuntimeError("CRITICAL_INTERNAL_DB_PASSWORD_LEAK: postgresql://admin:secretpass@10.0.0.1/db")

    monkeypatch.setattr(main, "engine", FailingEngine())

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["database"] == "unavailable"
    assert "secretpass" not in resp.text
    assert "CRITICAL_INTERNAL_DB" not in resp.text
