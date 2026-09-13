"""
backend/api/routes_ingest.py

API endpoints for:
- POST /data-readiness: Evaluates dataset quality and coverage without persisting.
- POST /data/ingest: Full ingestion pipeline (readiness evaluation -> database persistence -> audit log).
Supports both JSON payload and multipart CSV file upload.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.data.adapters.csv_adapter import CSVAdapter
from backend.data.ingestion.data_readiness_agent import run as run_data_readiness
from backend.data.ingestion.ingest import run_ingestion

router = APIRouter(tags=["Ingestion"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class IngestJsonPayload(BaseModel):
    creator_id: str = Field(..., description="Unique identifier for the creator")
    source: str = Field("custom_payload", description="Data source identifier (e.g. csv_upload, graph_api)")
    raw_data: List[Dict[str, Any]] = Field(..., description="List of raw, unmapped record dicts")
    quality_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum quality score threshold")


class ReadinessResponse(BaseModel):
    data_ready: bool
    quality_score: float
    missing_features: List[str]
    available_features: List[str]
    duplicate_records_removed: int
    invalid_timestamps: int
    record_count: int
    processed_data: Optional[List[Dict[str, Any]]] = None


class IngestResponse(ReadinessResponse):
    inserted_count: int


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

async def _parse_upload_file(file: UploadFile) -> List[Dict[str, Any]]:
    """Reads and parses an uploaded CSV file using CSVAdapter."""
    try:
        content_bytes = await file.read()
        text_content = content_bytes.decode("utf-8-sig")
        adapter = CSVAdapter()
        return adapter.fetch(content=text_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse uploaded CSV file: {str(e)}",
        )


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.post("/data-readiness", response_model=ReadinessResponse)
async def check_data_readiness(request: Request):
    """
    Evaluates dataset quality and coverage without persisting to the database.
    Accepts either a JSON body or a multipart CSV file upload.
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            payload = IngestJsonPayload(**body)
            records = payload.raw_data
            threshold = payload.quality_threshold
            creator_id = payload.creator_id
            source = payload.source
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}",
            )
    elif "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if not uploaded_file or not hasattr(uploaded_file, "read"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file must be uploaded under form key 'file'.",
            )
        records = await _parse_upload_file(uploaded_file)
        threshold_val = form.get("quality_threshold", 0.5)
        try:
            threshold = float(threshold_val)
        except (ValueError, TypeError):
            threshold = 0.5
        creator_id = form.get("creator_id", "preview_creator")
        source = "csv_upload"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported Content-Type. Use application/json or multipart/form-data.",
        )

    result = run_data_readiness(
        {"creator_id": creator_id, "source": source, "raw_data": records},
        quality_threshold=threshold,
    )
    return result


@router.post("/data/ingest", response_model=IngestResponse)
async def ingest_data(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Runs full pipeline: schema mapping -> readiness validation -> DB persistence -> IngestionLog.
    Accepts either a JSON body or a multipart CSV file upload.
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            payload = IngestJsonPayload(**body)
            records = payload.raw_data
            threshold = payload.quality_threshold
            creator_id = payload.creator_id
            source = payload.source
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}",
            )
    elif "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if not uploaded_file or not hasattr(uploaded_file, "read"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file must be uploaded under form key 'file'.",
            )
        creator_id = form.get("creator_id")
        if not creator_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="creator_id form field is required when uploading a CSV file.",
            )
        records = await _parse_upload_file(uploaded_file)
        threshold_val = form.get("quality_threshold", 0.5)
        try:
            threshold = float(threshold_val)
        except (ValueError, TypeError):
            threshold = 0.5
        source = "csv_upload"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported Content-Type. Use application/json or multipart/form-data.",
        )

    result = run_ingestion(
        session_or_factory=db,
        creator_id=creator_id,
        source=source,
        raw_data=records,
        quality_threshold=threshold,
    )

    return result
