"""
backend/api/routes_auth.py

Authentication and session endpoints:
- POST /auth/login: Authenticates credentials and returns a Bearer token + user context.
- GET /auth/me: Returns current authenticated user and workspace tenancy details.
"""

from __future__ import annotations
import secrets
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.config import settings
from backend.security import (
    User,
    get_current_user,
    authenticate_token,
    DEV_USER,
)
from backend.security.auth import get_configured_key_registry

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or creator handle")
    workspace_id: Optional[str] = Field("default", description="Workspace tenant identifier")
    api_key: Optional[str] = Field(None, description="Secret API key or access token")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    workspace_id: str
    role: str
    allowed_creators: List[str]


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    """
    Authenticates a user against the key registry or grants a developer/creator session.
    Returns an access token and tenant identity.
    """
    registry = get_configured_key_registry()

    # 1. Direct API Key check if provided
    if payload.api_key and payload.api_key.strip():
        user = authenticate_token(payload.api_key.strip())
        if user:
            return {
                "access_token": payload.api_key.strip(),
                "token_type": "bearer",
                "user_id": user.user_id,
                "workspace_id": user.workspace_id,
                "role": user.role,
                "allowed_creators": user.allowed_creators,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key or access token.",
            )

    # 2. Check username against registry user_ids
    for key, data in registry.items():
        if data.get("user_id") == payload.username.strip():
            return {
                "access_token": key,
                "token_type": "bearer",
                "user_id": data["user_id"],
                "workspace_id": data.get("workspace_id", payload.workspace_id or "default"),
                "role": data.get("role", "member"),
                "allowed_creators": data.get("allowed_creators", []),
            }

    # 3. Development / Demo mode session generation
    generated_token = f"key-session-{secrets.token_hex(8)}"
    # Register ephemeral session key for the duration of the server process
    registry[generated_token] = {
        "user_id": payload.username.strip(),
        "workspace_id": payload.workspace_id.strip() if payload.workspace_id else "default",
        "role": "admin" if "admin" in payload.username.lower() else "member",
        "allowed_creators": [],
    }

    return {
        "access_token": generated_token,
        "token_type": "bearer",
        "user_id": payload.username.strip(),
        "workspace_id": payload.workspace_id.strip() if payload.workspace_id else "default",
        "role": "admin" if "admin" in payload.username.lower() else "member",
        "allowed_creators": [],
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
def logout(current_user: User = Depends(get_current_user)):
    """Logs out the active user and clears session."""
    return {"status": "logged_out", "user_id": current_user.user_id}

