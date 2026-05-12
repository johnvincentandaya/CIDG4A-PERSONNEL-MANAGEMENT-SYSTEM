from __future__ import annotations

import hmac
import os

from fastapi import APIRouter, HTTPException, Request, status, Response
from pydantic import BaseModel

from ..security import is_auth_enabled

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


@router.get("/me")
def me(request: Request):
    enabled = is_auth_enabled()
    configured = bool(os.getenv("APP_PASSWORD"))
    authenticated = True if not enabled else bool(request.session.get("authenticated"))
    return {"enabled": enabled, "configured": configured, "authenticated": authenticated}


@router.post("/login")
def login(payload: LoginRequest, request: Request):
    expected = os.getenv("APP_PASSWORD", "")
    if is_auth_enabled() and not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is not configured for authentication (APP_PASSWORD is missing).",
        )

    if expected and not hmac.compare_digest(payload.password or "", expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    request.session["authenticated"] = True
    return {"ok": True}


@router.post("/logout")
def logout(request: Request, response: Response):
    request.session.clear()
    # Delete the signed session cookie as well.
    response.delete_cookie("cidg_session", path="/")
    return {"ok": True}
