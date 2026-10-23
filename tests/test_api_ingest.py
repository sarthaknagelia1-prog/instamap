"""
tests/test_api_ingest.py

Integration tests for FastAPI endpoints:
- GET /health
- POST /data-readiness (JSON and CSV upload)
- POST /data/ingest (JSON and CSV upload)
"""

from pathlib import Path
from backend.database.models import Creator, Post, IngestionLog

SAMPLE_CSV_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "creator_export.csv"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_data_readiness_json(client):
    payload = {
        "creator_id": "creator_test",
        "source": "manual_input",
        "raw_data": [
            {
                "id": "p_001",
                "type": "reel",
                "timestamp": "2026-08-01T12:00:00Z",
                "like_count": 50,
                "comments": 5,
            }
        ],
        "quality_threshold": 0.3,
    }
    response = client.post("/data-readiness", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data_ready"] is True
    assert data["record_count"] == 1
    assert data["duplicate_records_removed"] == 0


def test_data_ingest_json(client, db_session):
    payload = {
        "creator_id": "creator_test_ingest",
        "source": "api_test",
        "raw_data": [
            {
                "id": "post_a",
                "type": "reel",
                "timestamp": "2026-08-01T12:00:00Z",
                "like_count": 100,
                "comments": 10,
                "reach": 800,
            },
            {
                "id": "post_b",
                "type": "carousel",
                "timestamp": "2026-08-02T15:00:00Z",
                "like_count": 200,
                "comments": 20,
                "reach": 1500,
            },
        ],
        "quality_threshold": 0.4,
    }
    response = client.post("/data/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data_ready"] is True
    assert data["inserted_count"] == 2

    # Verify DB persistence
    creator = db_session.get(Creator, "creator_test_ingest")
    assert creator is not None
    posts = db_session.query(Post).filter_by(creator_id="creator_test_ingest").all()
    assert len(posts) == 2

    log = db_session.query(IngestionLog).filter_by(creator_id="creator_test_ingest").first()
    assert log is not None
    assert log.inserted_count == 2
    assert log.data_ready is True


def test_data_readiness_csv_upload(client):
    assert SAMPLE_CSV_PATH.exists(), f"Sample CSV not found at {SAMPLE_CSV_PATH}"
    with open(SAMPLE_CSV_PATH, "rb") as f:
        response = client.post(
            "/data-readiness",
            files={"file": ("creator_export.csv", f, "text/csv")},
            data={"quality_threshold": "0.3"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["data_ready"] is True
    # sample CSV has 1 duplicate (p1) and 1 invalid timestamp (p4)
    assert data["duplicate_records_removed"] == 1
    assert data["invalid_timestamps"] == 1


def test_data_ingest_csv_upload(client, db_session):
    with open(SAMPLE_CSV_PATH, "rb") as f:
        response = client.post(
            "/data/ingest",
            files={"file": ("creator_export.csv", f, "text/csv")},
            data={"creator_id": "creator_csv_user", "quality_threshold": "0.3"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["data_ready"] is True
    assert data["inserted_count"] > 0

    # Verify DB persistence
    posts = db_session.query(Post).filter_by(creator_id="creator_csv_user").all()
    assert len(posts) == data["inserted_count"]
