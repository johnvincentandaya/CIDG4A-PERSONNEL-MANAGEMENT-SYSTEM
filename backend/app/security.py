from __future__ import annotations

import os

from fastapi import HTTPException, Request, status


def _is_truthy_env(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def is_auth_enabled() -> bool:
    """Auth is enabled by default.

    Set AUTH_DISABLED=1 to explicitly disable authentication (not recommended).
    """
    return not _is_truthy_env(os.getenv("AUTH_DISABLED"))


def require_auth(request: Request) -> None:
    """Dependency that enforces authentication when auth is enabled."""
    enabled = is_auth_enabled()
    sess_auth = bool(request.session.get("authenticated"))

    if not enabled:
        return

    if not sess_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
