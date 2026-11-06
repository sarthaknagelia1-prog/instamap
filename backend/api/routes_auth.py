"""
backend/api/routes_auth.py

Authentication and session endpoints:
- POST /auth/login: Exchanges credentials for an HttpOnly browser session + user context.
- GET /auth/me: Returns current authenticated user and workspace tenancy details.
"""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.config import settings
from backend.security import User, get_current_user, authenticate_token
from backend.security.auth import create_browser_session, revoke_browser_session
from backend.database.session import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or creator handle")
    workspace_id: Optional[str] = Field("default", description="Workspace tenant identifier")
    api_key: Optional[str] = Field(None, description="Secret API key or access token")


class LoginResponse(BaseModel):
    token_type: str = "bearer"
    user_id: str
    workspace_id: str
    role: str
    allowed_creators: List[str]


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticates an API key or grants a local development session.
    Browser sessions are returned only as HttpOnly cookies.
    """
    user = None
    # Credentials are exchanged for a server-side session; the browser receives only an HttpOnly cookie.
    if payload.api_key and payload.api_key.strip():
        user = authenticate_token(payload.api_key.strip())
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key or access token.",
            )

    else:
        # Passwordless developer entry is explicitly limited to non-production optional-auth mode.
        if not settings.is_development or settings.REQUIRE_AUTH:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="An API key is required.")
        if not payload.username.strip():
            raise HTTPException(status_code=422, detail="Username is required.")
        user = User(
            user_id=payload.username.strip(),
            workspace_id=(payload.workspace_id or settings.DEFAULT_WORKSPACE_ID).strip(),
            # This admin shortcut is only reachable on the loopback-only local dev server.
            role="system_admin",
            allowed_creators=[],
        )

    session_id = create_browser_session(user, db)
    response.set_cookie(
        "instamap_session", session_id, httponly=True,
        secure=settings.SESSION_COOKIE_SECURE or not settings.is_development,
        samesite="lax", path="/", max_age=60 * 60 * 12,
    )

    return {
        "token_type": "bearer",
        "user_id": user.user_id,
        "workspace_id": user.workspace_id,
        "role": user.role,
        "allowed_creators": user.allowed_creators,
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user identity and workspace context."""
    return {
        "user_id": current_user.user_id,
        "workspace_id": current_user.workspace_id,
        "role": current_user.role,
        "allowed_creators": current_user.allowed_creators,
        "is_authenticated": current_user.is_authenticated,
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logs out the active user and clears session."""
    revoke_browser_session(request.cookies.get("instamap_session"), db)
    response.delete_cookie("instamap_session", path="/", httponly=True, samesite="lax")
    return {"status": "logged_out", "user_id": current_user.user_id}

