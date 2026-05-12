from __future__ import annotations

import hmac
import os
import re

from fastapi import APIRouter, HTTPException, Request, status, Response
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv, set_key

from ..security import is_auth_enabled

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements. Returns (is_valid, error_message)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."
    return True, ""


def calculate_password_strength(password: str) -> dict:
    """Calculate password strength score (0-5) and return details."""
    score = 0
    
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    
    strength_labels = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong"]
    strength_label = strength_labels[min(score, 5)]
    
    return {
        "score": min(score, 5),
        "strength": strength_label,
        "requirements": {
            "length": len(password) >= 8,
            "uppercase": bool(re.search(r'[A-Z]', password)),
            "lowercase": bool(re.search(r'[a-z]', password)),
            "number": bool(re.search(r'\d', password)),
            "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
        }
    }


def _dotenv_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def _save_app_password(password: str) -> None:
    dotenv_path = _dotenv_path()
    dotenv_path.parent.mkdir(parents=True, exist_ok=True)
    if not dotenv_path.exists():
        dotenv_path.write_text("")
    set_key(str(dotenv_path), "APP_PASSWORD", password)
    load_dotenv(dotenv_path, override=True)


def _authenticated_request(request: Request) -> None:
    if is_auth_enabled() and not request.session.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )


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
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is enabled but not configured. Please set APP_PASSWORD environment variable.",
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


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, request: Request):
    _authenticated_request(request)

    expected = os.getenv("APP_PASSWORD", "")
    if is_auth_enabled() and not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is enabled but not configured. Please set APP_PASSWORD environment variable.",
        )

    if expected and not hmac.compare_digest(payload.current_password or "", expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match.",
        )

    if hmac.compare_digest(payload.new_password or "", expected):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password.",
        )

    valid, message = validate_password_strength(payload.new_password or "")
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    _save_app_password(payload.new_password or "")
    return {"ok": True, "message": "Password changed successfully."}


@router.post("/password-strength")
def password_strength(payload: LoginRequest):
    score = calculate_password_strength(payload.password or "")
    return score
