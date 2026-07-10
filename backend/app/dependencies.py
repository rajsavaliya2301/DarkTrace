"""Dependency injection for FastAPI — auth, database sessions, rate limiting."""

import json
import logging
import time
import hashlib
from typing import Optional, List

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from elasticsearch import AsyncElasticsearch
from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import AsyncDriver
from redis.asyncio import Redis as AsyncRedis
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_mongodb, get_elasticsearch, get_neo4j, get_redis

logger = logging.getLogger(__name__)

# Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)

# ─── Database Dependencies ────────────────────────────────────────────────────


async def get_db() -> AsyncIOMotorDatabase:
    """Dependency: get MongoDB database."""
    return await get_mongodb()


async def get_es() -> AsyncElasticsearch:
    """Dependency: get Elasticsearch client."""
    return await get_elasticsearch()


async def get_neo4j_db() -> AsyncDriver:
    """Dependency: get Neo4j driver."""
    return await get_neo4j()


async def get_redis_client() -> AsyncRedis:
    """Dependency: get Redis client."""
    return await get_redis()


# ─── Auth Dependencies ────────────────────────────────────────────────────────


class CurrentUser(BaseModel):
    """Authenticated user info injected into request handlers."""

    id: str
    email: str
    name: str
    role: str
    permissions: List[str]

    def has_permission(self, required: str) -> bool:
        return required in self.permissions

    def has_role(self, *roles: str) -> bool:
        return self.role in roles


def _get_permissions_for_role(role: str) -> List[str]:
    """Map role to permissions list."""
    role_permissions = {
        "admin": [
            "alerts:read", "alerts:write",
            "search:read",
            "crawler:read", "crawler:write",
            "watchlists:read", "watchlists:write",
            "reports:read", "reports:create",
            "actors:read",
            "admin:read", "admin:write",
            "dashboard:read",
            "export:write",
        ],
        "investigator": [
            "alerts:read", "alerts:write",
            "search:read",
            "crawler:read", "crawler:write",
            "watchlists:read", "watchlists:write",
            "reports:read", "reports:create",
            "actors:read",
            "dashboard:read",
            "export:write",
        ],
        "auditor": [
            "search:read",
            "reports:read",
            "actors:read",
            "admin:read",
            "dashboard:read",
        ],
        "siem_integration": [
            "alerts:read",
        ],
    }
    return role_permissions.get(role, [])


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis: AsyncRedis = Depends(get_redis_client),
) -> CurrentUser:
    """Extract and validate current user from JWT or API key."""
    settings = get_settings()

    # 1) Try API key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return await _resolve_api_key(api_key, db)

    # 2) Try Bearer token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check if token is blacklisted (logout)
    is_blacklisted = await redis.get(f"blacklist:token:{token}")
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # Verify JWT
    from app.auth.jwt import verify_access_token

    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Load user from DB
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    role = user.get("role", "investigator")
    return CurrentUser(
        id=str(user["_id"]),
        email=user.get("email", ""),
        name=user.get("name", ""),
        role=role,
        permissions=_get_permissions_for_role(role),
    )


async def _resolve_api_key(api_key: str, db: AsyncIOMotorDatabase) -> CurrentUser:
    """Resolve user from API key."""
    import hashlib

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    user = await db.users.find_one({"api_keys.key_hash": key_hash, "api_keys.is_active": True})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    # Update last used
    await db.users.update_one(
        {"_id": user["_id"], "api_keys.key_hash": key_hash},
        {"$set": {"api_keys.$.last_used_at": int(time.time())}},
    )

    role = user.get("role", "investigator")
    return CurrentUser(
        id=str(user["_id"]),
        email=user.get("email", ""),
        name=user.get("name", ""),
        role=role,
        permissions=_get_permissions_for_role(role),
    )


# ─── Role-based access control ────────────────────────────────────────────────


def require_permission(permission: str):
    """Dependency factory: require a specific permission."""

    async def _check_permission(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return current_user

    return _check_permission


def require_role(*roles: str):
    """Dependency factory: require one of the specified roles."""

    async def _check_role(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_role(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{' or '.join(roles)}' required",
            )
        return current_user

    return _check_role


# ─── Audit Logging ────────────────────────────────────────────────────────────


async def create_audit_log(
    db: AsyncIOMotorDatabase,
    user_id: str,
    user_name: str,
    user_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
) -> str:
    """Create an audit log entry with tamper-evident hash chaining."""
    # Get the previous log entry's hash
    last_log = await db.audit_logs.find_one(
        {}, sort=[("_id", -1)], projection={"tamper_hash": 1}
    )
    previous_hash = last_log["tamper_hash"] if last_log else "0" * 64

    log_entry = {
        "timestamp": int(time.time()),
        "user_id": user_id,
        "user_name": user_name,
        "user_role": user_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "ip_address": ip_address or "",
        "user_agent": user_agent or "",
        "request_id": request_id or "",
        "previous_hash": previous_hash,
    }

    # Compute tamper-evident hash
    serialized = json.dumps(log_entry, sort_keys=True, default=str)
    log_entry["tamper_hash"] = hashlib.sha256(
        (previous_hash + serialized).encode()
    ).hexdigest()

    result = await db.audit_logs.insert_one(log_entry)
    return str(result.inserted_id)


async def log_user_action(
    request: Request,
    current_user: CurrentUser,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[dict] = None,
):
    """Convenience function to log an action from a request handler."""
    db = await get_mongodb()
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
        request_id=request.headers.get("x-request-id", ""),
    )


# ─── Rate Limiting ────────────────────────────────────────────────────────────


async def check_rate_limit(
    request: Request,
    redis: AsyncRedis = Depends(get_redis_client),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
) -> None:
    """Rate limiting middleware dependency."""
    settings = get_settings()
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS

    # Determine rate limit key
    if current_user:
        key = f"rate:user:{current_user.id}"
        limit = settings.RATE_LIMIT_PER_USER
    else:
        ip = request.client.host if request.client else "unknown"
        key = f"rate:ip:{ip}"
        limit = settings.RATE_LIMIT_PER_IP

    # Sliding window via sorted set
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window)
    results = await pipe.execute()

    count = results[1]  # zcard result
    if count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {limit} requests per {window}s",
        )
