"""JWT token creation, verification, and refresh logic."""

import time
import uuid
from typing import Optional, Dict, Any

import jwt as pyjwt

from app.config import get_settings


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a JWT access token with configurable expiry."""
    settings = get_settings()
    now = int(time.time())
    expires = now + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": now,
        "exp": expires,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)

    token = pyjwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token with longer expiry."""
    settings = get_settings()
    now = int(time.time())
    expires = now + (settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": expires,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }

    token = pyjwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode an access token. Returns payload or None."""
    settings = get_settings()
    try:
        payload = pyjwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )
        if payload.get("type") != "access":
            return None
        return payload
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a refresh token. Returns payload or None."""
    settings = get_settings()
    try:
        payload = pyjwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode a token without verifying expiry (for blacklist checks)."""
    settings = get_settings()
    try:
        payload = pyjwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        return payload
    except pyjwt.InvalidTokenError:
        return None
