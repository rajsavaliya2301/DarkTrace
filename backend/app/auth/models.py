"""User model and Pydantic schemas for authentication."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field
import bcrypt

from app.config import get_settings


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    """Public user representation."""
    id: str
    email: str
    name: str
    role: str
    permissions: List[str]


class UserCreate(BaseModel):
    """Create user payload."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="investigator", pattern="^(investigator|admin|auditor)$")


class UserUpdate(BaseModel):
    """Update user payload."""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    role: Optional[str] = Field(None, pattern="^(investigator|admin|auditor)$")
    is_active: Optional[bool] = None


class ApiKeyCreate(BaseModel):
    """API key creation request."""
    name: str = Field(..., min_length=1, max_length=64)
    permissions: List[str] = Field(default=["alerts:read"])


class ApiKeyResponse(BaseModel):
    """API key response (key shown once)."""
    key_id: str
    name: str
    key: str
    created_at: datetime


# ─── Password Hashing ─────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    settings = get_settings()
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ─── MongoDB User Document Helpers ──────────────────────────────────────────────


def new_user_document(
    email: str,
    name: str,
    password: str,
    role: str = "investigator",
) -> dict:
    """Create a MongoDB user document dict."""
    now = datetime.now(timezone.utc)
    return {
        "_id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "role": role,
        "is_active": True,
        "is_locked": False,
        "failed_login_attempts": 0,
        "locked_until": None,
        "last_login_at": None,
        "last_login_ip": None,
        "mfa_enabled": False,
        "mfa_secret": None,
        "api_keys": [],
        "preferences": {
            "theme": "dark",
            "notifications": {
                "email_alerts": True,
                "dashboard_alerts": True,
                "sms_alerts": False,
            },
            "default_report_format": "pdf",
            "items_per_page": 25,
        },
        "refresh_tokens": [],
        "created_at": now,
        "updated_at": now,
    }
