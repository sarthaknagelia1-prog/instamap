"""
backend/api/routes_advisory.py

REST API Endpoints for Growth Advisory Engine (AI Copilot / Chatbot):
- POST /advisory/chat: Conversational advice grounded in creator's database metrics.
- GET  /advisory/prompts/{creator_id}: Recommended starter questions tailored to creator.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Creator, utcnow
from backend.security import get_current_user, verify_creator_access, User
from backend.agents.advisory_agent import run_advisory_agent, gather_creator_advisory_context

router = APIRouter(prefix="/advisory", tags=["Advisory Engine"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class ChatRequest(BaseModel):
    creator_id: str = Field(..., description="Unique creator identifier")
    message: str = Field(..., max_length=10000, description="User question or guidance request")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous conversation turns")


class ChatResponse(BaseModel):
    creator_id: str
    reply: str
    suggested_followups: List[str]
    grounded_context: Dict[str, Any]
    timestamp: str


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat_with_growth_advisor(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Conversational AI Growth Advisor:
    Answers creator inquiries with recommendations grounded in their actual
    historical metrics, peak windows, format allocations, and active trend radar.
    """
    cid = payload.creator_id.strip()
    msg = payload.message.strip()

    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    verify_creator_access(cid, db=db, current_user=current_user)

    advisor_result = run_advisory_agent(
        creator_id=cid,
        user_message=msg,
        conversation_history=payload.conversation_history,
        db=db,
    )

    return {
        "creator_id": cid,
        "reply": advisor_result["reply"],
        "suggested_followups": advisor_result.get("suggested_followups", []),
        "grounded_context": advisor_result.get("grounded_context", {}),
        "timestamp": utcnow().isoformat(),
    }


@router.get("/prompts/{creator_id}")
def get_advisory_starter_prompts(
    creator_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns tailored starter prompt chips for an authorized creator."""
    creator = verify_creator_access(creator_id, db=db, current_user=current_user)
    niche = creator.niche if creator and creator.niche else "Tech & AI"

    return {
        "creator_id": creator.id,
        "niche": niche,
        "starter_prompts": [
            f"⚡ Give me 3 high-retention hooks for {niche}",
            "🕒 When is my peak algorithmic posting window and why?",
            "📊 How can I increase my average engagement rate and saves?",
            "🔥 What industry trends should I turn into Reels this week?",
            "🧪 How does my Welch's t-test experiment eliminate guesswork?",
        ],
    }
