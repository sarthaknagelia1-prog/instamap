"""
backend/security/auth.py

Authentication and Authorization models and credential validation.
Provides centralized principal representation and tenant context.
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from backend.config import settings


@dataclass
class User:
    """Authenticated user context containing identity, tenant scope, and roles."""
    user_id: str
    workspace_id: str
    role: str = "member"  # "admin", "member", "viewer"
    allowed_creators: List[str] = field(default_factory=list)
    is_authenticated: bool = True

    def can_access_creator(self, creator_id: str, creator_workspace_id: Optional[str] = None) -> bool:
        """Determines if the user has authorization for a given creator."""
        if self.role == "admin":
            return True
        if creator_workspace_id and creator_workspace_id != self.workspace_id:
            return False
        if self.allowed_creators and creator_id not in self.allowed_creators:
            return False
        return True


# Default developer context when running in local development with REQUIRE_AUTH=False
DEV_USER = User(
    user_id="dev-user",
    workspace_id=settings.DEFAULT_WORKSPACE_ID,
    role="admin",
    allowed_creators=[],
    is_authenticated=False,
)

# Built-in demo / test credential directory
DEFAULT_KEY_REGISTRY: Dict[str, Dict] = {
    "test-admin-key": {
        "user_id": "admin-1",
        "workspace_id": "system-admin",
        "role": "admin",
        "allowed_creators": [],
    },
    "key-tenant-alpha": {
        "user_id": "user-alpha",
        "workspace_id": "ws-alpha",
        "role": "member",
        "allowed_creators": [],
    },
    "key-tenant-beta": {
        "user_id": "user-beta",
        "workspace_id": "ws-beta",
        "role": "member",
        "allowed_creators": [],
    },
}


def get_configured_key_registry() -> Dict[str, Dict]:
    """Combines built-in keys with any configured via API_KEYS environment variable."""
    registry = dict(DEFAULT_KEY_REGISTRY)
    raw = settings.API_KEYS_RAW.strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                registry.update(parsed)
        except Exception:
            # Also support comma-separated "key=user:workspace:role" pairs
            for pair in raw.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    parts = v.split(":")
                    registry[k.strip()] = {
                        "user_id": parts[0] if len(parts) > 0 else "user",
                        "workspace_id": parts[1] if len(parts) > 1 else settings.DEFAULT_WORKSPACE_ID,
                        "role": parts[2] if len(parts) > 2 else "member",
                        "allowed_creators": parts[3].split(";") if len(parts) > 3 and parts[3] else [],
                    }
    return registry


def authenticate_token(token: str) -> Optional[User]:
    """Validates an API key / Bearer token and returns the corresponding User."""
    clean_token = token.strip()
    if clean_token.startswith("Bearer "):
        clean_token = clean_token[7:].strip()

    registry = get_configured_key_registry()
    data = registry.get(clean_token)
    if not data:
        return None

    return User(
        user_id=data.get("user_id", "authenticated-user"),
        workspace_id=data.get("workspace_id", settings.DEFAULT_WORKSPACE_ID),
        role=data.get("role", "member"),
        allowed_creators=data.get("allowed_creators", []),
        is_authenticated=True,
    )
