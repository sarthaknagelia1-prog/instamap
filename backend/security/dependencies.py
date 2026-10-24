"""
backend/security/dependencies.py

FastAPI dependencies for user authentication and creator/workspace authorization.
Enforces default-deny access control on data-bearing and state-changing endpoints.
"""

from __future__ import annotations
from typing import Optional
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import Creator
from backend.database.session import get_db
from backend.security.auth import DEV_USER, User, authenticate_token


def get_current_user(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> User:
    """
    Extracts and verifies authentication credentials.
    Supports either 'X-API-Key: <key>' or 'Authorization: Bearer <key>'.
    In production or when REQUIRE_AUTH=True, rejects requests without valid credentials.
    In local dev when REQUIRE_AUTH=False, falls back to DEV_USER.
    """
    token = x_api_key or authorization

    if token:
        user = authenticate_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    # No credentials provided
    if settings.REQUIRE_AUTH or settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return DEV_USER


def verify_creator_access(
    creator_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Creator:
    """
    Verifies that the target creator exists AND that the authenticated user
    has permission to access it. Fails closed with 403 Forbidden on tenant mismatch.
    """
    creator = db.get(Creator, creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{creator_id}' not found.",
        )

    if not current_user.can_access_creator(creator.id, getattr(creator, "workspace_id", "default")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to access this creator's data.",
        )

    return creator


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforces administrator role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user
