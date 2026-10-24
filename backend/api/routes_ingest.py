"""
backend/api/routes_ingest.py

API endpoints for Data Ingestion:
- POST /data-readiness: Evaluates dataset quality and coverage without persisting.
- POST /data/ingest: Full ingestion pipeline (supports JSON, CSV, TSV, and JSON file uploads).
- POST /data/ingest/paste: Ingests raw tabular text pasted from Google Sheets, Excel, or Markdown.
- GET /data/csv-template: Downloads a pre-formatted CSV template for creators.
- GET /data/sources: Returns supported export platforms and field mapping guidance.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.session import get_db
from backend.database.models import Creator
from backend.security import get_current_user, User
from backend.data.adapters.csv_adapter import CSVAdapter
from backend.data.adapters.json_adapter import JSONAdapter
from backend.data.adapters.paste_adapter import PasteAdapter
from backend.data.adapters.meta_adapter import MetaAdapter
from backend.data.schema_mapper import detect_source_platform
from backend.data.ingestion.data_readiness_agent import run as run_data_readiness
from backend.data.ingestion.ingest import run_ingestion
from backend.api.routes_analytics import invalidate_analytics_cache

router = APIRouter(tags=["Ingestion"])



# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class IngestJsonPayload(BaseModel):
    creator_id: str = Field(..., description="Unique identifier for the creator")
    source: Optional[str] = Field("custom_payload", description="Data source identifier (e.g. json_upload, metricool, later)")
    raw_data: List[Dict[str, Any]] = Field(..., description="List of raw, unmapped record dicts")
    quality_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum quality score threshold")

    @field_validator("raw_data")
    @classmethod
    def validate_records_bound(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(v) > settings.MAX_INGEST_RECORDS:
            raise ValueError(f"Payload contains {len(v)} records, exceeding maximum allowed {settings.MAX_INGEST_RECORDS}.")
        return v


class IngestPastePayload(BaseModel):
    creator_id: str = Field(..., description="Unique identifier for the creator")
    text_data: str = Field(..., description="Pasted table text (tab-separated from Sheets/Excel, or Markdown table)")
    source: Optional[str] = Field("bulk_paste", description="Source description")
    quality_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum quality score threshold")

    @field_validator("text_data")
    @classmethod
    def validate_paste_bound(cls, v: str) -> str:
        if len(v.encode("utf-8")) > settings.MAX_PASTE_SIZE_BYTES:
            raise ValueError("Pasted text exceeds maximum permitted size.")
        return v


class MetaAccountIngestPayload(BaseModel):
    creator_id: str = Field(..., description="Unique identifier for the creator")
    access_token: str = Field(..., description="Meta Graph User/Page Access Token")
    ig_user_id: Optional[str] = Field(None, description="Instagram Business/Creator Account ID (auto-discovered if omitted)")
    limit: int = Field(50, ge=1, le=500, description="Max posts to retrieve from Meta Graph API")
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


HTTP_413 = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

async def _parse_upload_file(file: UploadFile) -> List[Dict[str, Any]]:
    """Reads and parses an uploaded file with bounded streaming (SEC-04)."""
    max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
    total_bytes = bytearray()
    while chunk := await file.read(64 * 1024):
        total_bytes.extend(chunk)
        if len(total_bytes) > max_bytes:
            raise HTTPException(
                status_code=HTTP_413,
                detail=f"Uploaded file exceeds maximum permitted size of {max_bytes // (1024 * 1024)}MB.",
            )
    try:
        text_content = total_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not valid UTF-8 text.",
        )

    filename = (file.filename or "").lower()
    try:
        if "meta" in filename or "instagram" in filename or "posts_" in filename:
            records = MetaAdapter.parse_meta_export_archive(text_content, filename=filename)
        elif filename.endswith(".json"):
            adapter = JSONAdapter()
            records = adapter.fetch(content=text_content)
        else:
            adapter = CSVAdapter()
            records = adapter.fetch(content=text_content)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to parse uploaded file. Please verify delimiter and file structure.",
        )

    if len(records) > settings.MAX_INGEST_RECORDS:
        raise HTTPException(
            status_code=HTTP_413,
            detail=f"Dataset contains {len(records)} records, exceeding the limit of {settings.MAX_INGEST_RECORDS}.",
        )
    return records


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.get("/data/csv-template")
def get_csv_template():
    """
    Returns a downloadable CSV template with standard headers and sample data
    that creators can fill in and upload directly.
    """
    csv_content = (
        "post_id,date,type,likes,comments,shares,saves,reach,impressions,caption,hashtags\n"
        "post_001,2026-10-01T18:00:00Z,reel,240,25,30,45,3500,5200,How to scale your audience on Instagram,#growth #marketing\n"
        "post_002,2026-10-03T12:30:00Z,carousel,180,18,12,38,2800,4100,5 mistakes creators make with video copy,#creator #contenttips\n"
        "post_003,2026-10-05T19:00:00Z,image,110,14,8,15,1900,2400,Behind the scenes of our creative studio,#buildinpublic\n"
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=instagram_growth_template.csv"},
    )


@router.get("/data/sources")
def get_supported_sources():
    """Returns documentation on supported export tools and formats."""
    return {
        "supported_input_methods": [
            "Meta Account Direct Sync (POST /data/ingest/meta-account with user token)",
            "CSV / TSV file upload (POST /data/ingest with form key 'file')",
            "Meta Data Download Archive (POST /data/ingest with official posts_1.json or Meta Business Suite CSV)",
            "JSON file upload (POST /data/ingest with .json file)",
            "Direct JSON API payload (POST /data/ingest with application/json)",
            "Spreadsheet copy-paste (POST /data/ingest/paste with tab-separated or markdown text)",
        ],
        "compatible_platforms": [
            {"name": "Meta Graph API (Direct Account Sync)", "formats": ["User Access Token / Page Token"]},
            {"name": "Instagram Data Download Archive", "formats": ["posts_1.json", "content.json"]},
            {"name": "Meta Business Suite / Creator Studio", "formats": ["CSV", "XLSX export"]},
            {"name": "Metricool", "formats": ["CSV export"]},
            {"name": "Later", "formats": ["CSV export"]},
            {"name": "Hootsuite", "formats": ["CSV", "Excel export"]},
            {"name": "Sprout Social", "formats": ["CSV export"]},
            {"name": "Google Sheets / Excel", "formats": ["Copy-paste directly or Save as CSV"]},
        ],
        "required_fields": ["post_id", "timestamp (or date)", "content_type (or type)", "likes_count", "comments_count"],
        "optional_enrichment_fields": ["shares_count", "saves_count", "reach", "impressions", "caption_text", "hashtags", "watch_time_avg"],
    }


@router.post("/data-readiness", response_model=ReadinessResponse)
async def check_data_readiness(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluates dataset quality and coverage without persisting to the database.
    Accepts either a JSON body or a multipart CSV/JSON file upload.
    Enforces tenant boundaries and input limits.
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            payload = IngestJsonPayload(**body)
            records = payload.raw_data
            threshold = payload.quality_threshold
            creator_id = payload.creator_id
            source = payload.source or "custom_payload"
        except ValueError as val_err:
            raise HTTPException(
                status_code=HTTP_413 if "exceeding" in str(val_err) else status.HTTP_400_BAD_REQUEST,
                detail=str(val_err),
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload.",
            )
    elif "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if not uploaded_file or not hasattr(uploaded_file, "read"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be uploaded under form key 'file'.",
            )
        records = await _parse_upload_file(uploaded_file)
        threshold_val = form.get("quality_threshold", 0.5)
        try:
            threshold = float(threshold_val)
        except (ValueError, TypeError):
            threshold = 0.5
        creator_id = form.get("creator_id", "preview_creator")
        source = form.get("source", "file_upload")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported Content-Type. Use application/json or multipart/form-data.",
        )

    # Tenant check if creator already exists in database
    existing_creator = db.get(Creator, creator_id)
    if existing_creator and not current_user.can_access_creator(existing_creator.id, existing_creator.workspace_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to inspect this creator's data.",
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
    current_user: User = Depends(get_current_user),
):
    """
    Runs full pipeline: schema mapping -> readiness validation -> DB persistence -> IngestionLog.
    Accepts either a JSON body or a multipart file upload (CSV, TSV, or JSON).
    Enforces authorization, input bounds, and tenant isolation.
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            payload = IngestJsonPayload(**body)
            records = payload.raw_data
            threshold = payload.quality_threshold
            creator_id = payload.creator_id
            source = payload.source or "custom_payload"
        except ValueError as val_err:
            raise HTTPException(
                status_code=HTTP_413 if "exceeding" in str(val_err) else status.HTTP_400_BAD_REQUEST,
                detail=str(val_err),
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload.",
            )
    elif "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if not uploaded_file or not hasattr(uploaded_file, "read"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be uploaded under form key 'file'.",
            )
        creator_id = form.get("creator_id")
        if not creator_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="creator_id form field is required when uploading a file.",
            )
        records = await _parse_upload_file(uploaded_file)
        threshold_val = form.get("quality_threshold", 0.5)
        try:
            threshold = float(threshold_val)
        except (ValueError, TypeError):
            threshold = 0.5

        headers = list(records[0].keys()) if records else []
        detected = detect_source_platform(headers)
        source = form.get("source") or detected
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported Content-Type. Use application/json or multipart/form-data.",
        )

    # Enforce tenant authorization: prevent ingesting into another tenant's creator
    existing_creator = db.get(Creator, creator_id)
    if existing_creator and not current_user.can_access_creator(existing_creator.id, existing_creator.workspace_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to ingest data for this creator.",
        )

    result = run_ingestion(
        session_or_factory=db,
        creator_id=creator_id,
        source=source,
        raw_data=records,
        quality_threshold=threshold,
        workspace_id=current_user.workspace_id,
    )
    if result.get("data_ready"):
        invalidate_analytics_cache(creator_id)

    return result


@router.post("/data/ingest/paste", response_model=IngestResponse)
def ingest_pasted_data(
    payload: IngestPastePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Parses and ingests raw tabular text copied directly from Google Sheets,
    Excel, or Markdown tables with authorization and size bounds.
    """
    # Enforce tenant authorization
    existing_creator = db.get(Creator, payload.creator_id)
    if existing_creator and not current_user.can_access_creator(existing_creator.id, existing_creator.workspace_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to ingest data for this creator.",
        )

    adapter = PasteAdapter()
    records = adapter.fetch(text=payload.text_data)

    if not records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid records could be parsed from the pasted text.",
        )

    if len(records) > settings.MAX_INGEST_RECORDS:
        raise HTTPException(
            status_code=HTTP_413,
            detail=f"Pasted dataset contains {len(records)} records, exceeding the limit of {settings.MAX_INGEST_RECORDS}.",
        )

    headers = list(records[0].keys())
    detected = detect_source_platform(headers)
    source = payload.source if payload.source != "bulk_paste" else f"paste_{detected}"

    result = run_ingestion(
        session_or_factory=db,
        creator_id=payload.creator_id,
        source=source,
        raw_data=records,
        quality_threshold=payload.quality_threshold,
        workspace_id=current_user.workspace_id,
    )
    if result.get("data_ready"):
        invalidate_analytics_cache(payload.creator_id)

    return result


@router.post("/data/ingest/meta-account", response_model=IngestResponse)
def ingest_from_meta_account(
    payload: MetaAccountIngestPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Directly connects to creator's own Instagram account via Meta Graph API
    using a creator-provided User/Page Access Token.
    Auto-discovers the connected Instagram Business account and pulls media + insights.
    """
    existing_creator = db.get(Creator, payload.creator_id)
    if existing_creator and not current_user.can_access_creator(existing_creator.id, existing_creator.workspace_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to ingest data for this creator.",
        )

    try:
        adapter = MetaAdapter(access_token=payload.access_token, ig_user_id=payload.ig_user_id)
        records = adapter.fetch_account_posts(limit=payload.limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Meta Graph API error: {str(e)}",
        )

    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No media posts found on the specified Instagram account.",
        )

    result = run_ingestion(
        session_or_factory=db,
        creator_id=payload.creator_id,
        source="meta_graph_api",
        raw_data=records,
        quality_threshold=payload.quality_threshold,
        workspace_id=current_user.workspace_id,
    )
    if result.get("data_ready"):
        invalidate_analytics_cache(payload.creator_id)

    return result


