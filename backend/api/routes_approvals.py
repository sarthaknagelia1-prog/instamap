"""
backend/api/routes_approvals.py

REST API Endpoints for Approval & Review Layer:
- GET  /approvals: List queue items with creator and status filtering
- GET  /approvals/{id}: Detailed inspection of an approval item
- POST /approvals/{id}/decision: Submit review decision (approve, reject, request revision)
- GET  /approvals/stats/{creator_id}: Summary metrics on approval velocity and queue health
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.session import get_db
from backend.database.models import ApprovalItem, ContentDraft, Experiment, Strategy, ContentPlan, Creator, utcnow
from backend.security import get_current_user, verify_creator_access, User
from backend.approvals.events import event_bus

router = APIRouter(prefix="/approvals", tags=["Approvals"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="approved | rejected | revision_requested")
    notes: Optional[str] = Field(None, description="Creator feedback or revision instructions")
    rejection_reason: Optional[str] = Field(None, description="Reason if rejected")


class ApprovalItemResponse(BaseModel):
    id: str
    creator_id: str
    item_type: str
    item_id: str
    action_type: str
    risk_level: str
    status: str
    summary: str
    payload_snapshot: Dict[str, Any]
    reviewer_decision: Dict[str, Any]
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None


class ApprovalStatsResponse(BaseModel):
    creator_id: str
    total_items: int
    pending_count: int
    approved_count: int
    rejected_count: int
    revision_requested_count: int
    approval_rate_pct: float


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def _format_approval(record: ApprovalItem) -> Dict[str, Any]:
    return {
        "id": record.id,
        "creator_id": record.creator_id,
        "item_type": record.item_type,
        "item_id": record.item_id,
        "action_type": record.action_type,
        "risk_level": record.risk_level,
        "status": record.status,
        "summary": record.summary,
        "payload_snapshot": record.payload_snapshot or {},
        "reviewer_decision": record.reviewer_decision or {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "reviewed_at": record.reviewed_at.isoformat() if record.reviewed_at else None,
    }


def enqueue_approval_item(
    creator_id: str,
    item_type: str,
    item_id: str,
    action_type: str,
    summary: str,
    payload_snapshot: Dict[str, Any],
    risk_level: str = "medium",
    db: Optional[Session] = None,
) -> ApprovalItem:
    """Enqueues an item into the approval queue with pending status."""
    item_id_str = str(uuid.uuid4())
    record = ApprovalItem(
        id=item_id_str,
        creator_id=creator_id,
        item_type=item_type,
        item_id=item_id,
        action_type=action_type,
        risk_level=risk_level,
        status="pending",
        summary=summary,
        payload_snapshot=payload_snapshot,
        reviewer_decision={},
        created_at=utcnow(),
    )

    if db is not None:
        db.add(record)
        db.commit()

    event_bus.publish("approval.created", {
        "approval_id": item_id_str,
        "creator_id": creator_id,
        "item_type": item_type,
        "action_type": action_type,
    })

    return record


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.get("", response_model=List[ApprovalItemResponse])
def list_approvals(
    creator_id: Optional[str] = Query(None, description="Filter by creator ID"),
    status: Optional[str] = Query("pending", description="Filter by status ('pending', 'approved', 'rejected', or 'all')"),
    item_type: Optional[str] = Query(None, description="Filter by item type ('content_draft', 'strategy', etc.)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists approval queue items with tenant isolation and optional status/creator filtering."""
    query = db.query(ApprovalItem)

    if creator_id:
        verify_creator_access(creator_id, db=db, current_user=current_user)
        query = query.filter(ApprovalItem.creator_id == creator_id)
    else:
        if current_user.role != "admin":
            from sqlalchemy import select
            workspace_creators = select(Creator.id).filter(Creator.workspace_id == current_user.workspace_id)
            query = query.filter(ApprovalItem.creator_id.in_(workspace_creators))

    if status and status.lower() != "all":
        query = query.filter(ApprovalItem.status == status.lower())
    if item_type:
        query = query.filter(ApprovalItem.item_type == item_type)

    records = query.order_by(desc(ApprovalItem.created_at)).all()
    return [_format_approval(r) for r in records]


@router.get("/stats/{creator_id}", response_model=ApprovalStatsResponse)
def get_approval_stats(
    creator_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Computes approval velocity and status metrics for an authorized creator."""
    creator = db.get(Creator, creator_id)
    if creator:
        if not current_user.can_access_creator(creator.id, getattr(creator, "workspace_id", "default")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you do not have permission to view stats for this creator.",
            )
    elif not current_user.can_access_creator(creator_id, None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to view stats for this creator.",
        )

    items = db.query(ApprovalItem).filter(ApprovalItem.creator_id == creator_id).all()
    total = len(items)
    pending = sum(1 for i in items if i.status == "pending")
    approved = sum(1 for i in items if i.status == "approved")
    rejected = sum(1 for i in items if i.status == "rejected")
    revisions = sum(1 for i in items if i.status == "revision_requested")

    decided = approved + rejected
    rate = round((approved / decided) * 100.0, 1) if decided > 0 else 0.0

    return {
        "creator_id": creator_id,
        "total_items": total,
        "pending_count": pending,
        "approved_count": approved,
        "rejected_count": rejected,
        "revision_requested_count": revisions,
        "approval_rate_pct": rate,
    }


@router.get("/{approval_id}", response_model=ApprovalItemResponse)
def get_approval_item(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves full details of a specific approval queue item with authorization."""
    record = db.get(ApprovalItem, approval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval item not found.")

    verify_creator_access(record.creator_id, db=db, current_user=current_user)
    return _format_approval(record)


@router.post("/{approval_id}/decision", response_model=ApprovalItemResponse)
def submit_approval_decision(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits a review decision (approved, rejected, or revision_requested).
    Enforces tenant authorization and strict state machine transitions (SEC-07):
    - Rejects transitions on non-pending items with 409 Conflict.
    - Records reviewer identity and timestamp in audit trail.
    - Cascades the state change to the underlying resource:
      * Approved draft -> status 'approved'
      * Rejected draft -> status 'archived' (preserves audit integrity)
      * Approved experiment -> status 'active'
      * Rejected experiment -> status 'cancelled'
    """
    record = db.get(ApprovalItem, approval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval item not found.")

    # Authorization
    verify_creator_access(record.creator_id, db=db, current_user=current_user)

    # State transition validation (SEC-07)
    if record.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval item '{approval_id}' has already been decided with status '{record.status}'.",
        )

    decision = payload.decision.lower().strip()
    if decision not in ("approved", "rejected", "revision_requested"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approved', 'rejected', or 'revision_requested'.",
        )

    now = utcnow()
    record.status = decision
    record.reviewed_at = now
    record.reviewer_decision = {
        "decision": decision,
        "notes": payload.notes,
        "rejection_reason": payload.rejection_reason,
        "reviewed_at": now.isoformat(),
        "reviewer_id": current_user.user_id,
        "reviewer_workspace": current_user.workspace_id,
        "reviewer_role": current_user.role,
    }

    # Cascade state change to underlying resource
    if record.item_type in ("content_draft", "draft"):
        draft = db.get(ContentDraft, record.item_id)
        if draft:
            if decision == "approved":
                draft.status = "approved"
            elif decision == "rejected":
                draft.status = "archived"  # Never delete, archive for auditability
    elif record.item_type == "experiment":
        exp = db.get(Experiment, record.item_id)
        if exp:
            if decision == "approved":
                exp.status = "active"
            elif decision == "rejected":
                exp.status = "cancelled"

    db.commit()

    # Emit event notification
    event_bus.publish("approval.resolved", {
        "approval_id": record.id,
        "creator_id": record.creator_id,
        "item_type": record.item_type,
        "decision": decision,
        "reviewer_id": current_user.user_id,
    })

    return _format_approval(record)
