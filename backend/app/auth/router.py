"""Authentication router — login, refresh, logout."""

import time
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis as AsyncRedis

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    decode_token,
)
from app.auth.models import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    verify_password,
)
from app.config import get_settings
from app.dependencies import (
    get_db,
    get_redis_client,
    get_current_user,
    CurrentUser,
    _get_permissions_for_role,
    create_audit_log,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis: AsyncRedis = Depends(get_redis_client),
):
    """Authenticate user with email and password. Returns JWT tokens."""
    settings = get_settings()

    # ── IP-based rate limiting for login (brute-force protection) ──────────
    ip = request.client.host if request.client else "unknown"
    login_key = f"rate:login:{ip}"
    now = time.time()
    window = settings.LOGIN_RATE_WINDOW_SECONDS

    pipe = redis.pipeline()
    pipe.zremrangebyscore(login_key, 0, now - window)
    pipe.zcard(login_key)
    pipe.zadd(login_key, {str(now): now})
    pipe.expire(login_key, window)
    results = await pipe.execute()
    login_count = results[1]

    if login_count >= settings.LOGIN_RATE_LIMIT_PER_IP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {window} seconds.",
        )

    # Find user by email
    user = await db.users.find_one({"email": body.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if account is locked
    if user.get("is_locked", False):
        locked_until = user.get("locked_until")
        if locked_until and time.time() < locked_until.timestamp():
            remaining = int(locked_until.timestamp() - time.time())
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked. Try again in {remaining} seconds.",
            )
        else:
            # Reset lock
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"is_locked": False, "failed_login_attempts": 0, "locked_until": None}},
            )

    # Verify password
    password_hash = user.get("password_hash", "")
    if not verify_password(body.password, password_hash):
        # Increment failed attempts
        new_attempts = user.get("failed_login_attempts", 0) + 1
        update = {"$set": {"failed_login_attempts": new_attempts}}
        if new_attempts >= 5:
            lock_duration = 300  # 5 minutes
            update["$set"]["is_locked"] = True
            update["$set"]["locked_until"] = datetime.now(timezone.utc) + timedelta(seconds=lock_duration)
        await db.users.update_one({"_id": user["_id"]}, update)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Reset failed attempts on success
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "failed_login_attempts": 0,
                "last_login_at": datetime.now(timezone.utc),
                "last_login_ip": request.client.host if request.client else "",
            }
        },
    )

    # Generate tokens
    user_id = str(user["_id"])
    role = user.get("role", "investigator")
    access_token = create_access_token(user_id, user["email"], role)
    refresh_token = create_refresh_token(user_id)

    # Store refresh token hash in user document
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$push": {
                "refresh_tokens": {
                    "token_hash": refresh_hash,
                    "device_info": request.headers.get("user-agent", ""),
                    "ip_address": request.client.host if request.client else "",
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": datetime.now(timezone.utc)
                    + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                }
            }
        },
    )

    # Audit log
    await create_audit_log(
        db=db,
        user_id=user_id,
        user_name=user.get("name", ""),
        user_role=role,
        action="login",
        resource_type="auth",
        resource_id=user_id,
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )

    permissions = _get_permissions_for_role(role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user_id,
            email=user["email"],
            name=user.get("name", ""),
            role=role,
            permissions=permissions,
        ),
    )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis: AsyncRedis = Depends(get_redis_client),
):
    """Refresh an access token using a valid refresh token."""
    settings = get_settings()

    # Verify refresh token
    payload = verify_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Verify refresh token exists in user document
    refresh_hash = hashlib.sha256(body.refresh_token.encode()).hexdigest()
    user = await db.users.find_one(
        {
            "_id": user_id,
            "refresh_tokens.token_hash": refresh_hash,
        }
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not recognized",
        )

    # Remove old refresh token (one-time use)
    await db.users.update_one(
        {"_id": user_id},
        {"$pull": {"refresh_tokens": {"token_hash": refresh_hash}}},
    )

    # Generate new tokens
    new_access = create_access_token(user_id, user["email"], user.get("role", "investigator"))
    new_refresh = create_refresh_token(user_id)

    # Store new refresh token
    new_refresh_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    await db.users.update_one(
        {"_id": user_id},
        {
            "$push": {
                "refresh_tokens": {
                    "token_hash": new_refresh_hash,
                    "device_info": request.headers.get("user-agent", ""),
                    "ip_address": request.client.host if request.client else "",
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": datetime.now(timezone.utc)
                    + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                }
            }
        },
    )

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis: AsyncRedis = Depends(get_redis_client),
):
    """Logout by blacklisting the current access token."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    if token:
        # Decode to get expiry
        payload = decode_token(token)
        if payload:
            exp = payload.get("exp", 0)
            now = int(time.time())
            ttl = max(exp - now, 0)
            if ttl > 0:
                await redis.setex(f"blacklist:token:{token}", ttl, "1")

        # Remove all refresh tokens for this user
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": {"refresh_tokens": []}},
        )

    await create_audit_log(
        db=db,
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        action="logout",
        resource_type="auth",
        resource_id=current_user.id,
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )

    return {"message": "Logged out successfully"}

