"""Admin API endpoints — users, audit logs, health checks."""

import hashlib
import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel, EmailStr, Field

from app.auth.models import UserCreate, UserUpdate, UserResponse, ApiKeyCreate, hash_password, new_user_document
from app.dependencies import (
    get_db,
    get_es,
    get_current_user,
    CurrentUser,
    require_permission,
    require_role,
    log_user_action,
    create_audit_log,
)
from app.database import get_redis, get_neo4j
from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


class UserAdminResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    user_id: str
    user_name: str
    action: str
    resource_type: str
    resource_id: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# ─── Users ────────────────────────────────────────────────────────────────────


@router.get("/users", response_model=dict)
async def list_users(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """List all users."""
    cursor = db.users.find({}, {
        "password_hash": 0,
        "refresh_tokens": 0,
        "mfa_secret": 0,
        "api_keys.key_hash": 0,
    }).sort("created_at", -1)
    users = await cursor.to_list(length=None)
    data = []
    for u in users:
        data.append(
            UserAdminResponse(
                id=str(u["_id"]),
                email=u.get("email", ""),
                name=u.get("name", ""),
                role=u.get("role", "investigator"),
                is_active=u.get("is_active", True),
                last_login=u.get("last_login_at"),
                created_at=u.get("created_at"),
            )
        )
    return {"data": data}


@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    body: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Create a new user."""
    # Check duplicate email
    existing = await db.users.find_one({"email": body.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    doc = new_user_document(
        email=body.email,
        name=body.name,
        password=body.password,
        role=body.role,
    )
    await db.users.insert_one(doc)

    await log_user_action(
        request, current_user, "user_created", "user", doc["_id"],
        details={"email": body.email, "role": body.role},
    )

    return {
        "id": doc["_id"],
        "email": body.email,
        "name": body.name,
        "role": body.role,
        "created_at": doc["created_at"].isoformat(),
    }


@router.put("/users/{user_id}", response_model=dict)
async def update_user(
    request: Request,
    user_id: str,
    body: UserUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Update a user."""
    existing = await db.users.find_one({"_id": user_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_fields = {"updated_at": datetime.now(timezone.utc)}
    for field in ["name", "role", "is_active"]:
        val = getattr(body, field, None)
        if val is not None:
            update_fields[field] = val

    await db.users.update_one({"_id": user_id}, {"$set": update_fields})

    await log_user_action(
        request, current_user, "user_updated", "user", user_id,
        details={"changes": list(update_fields.keys())},
    )

    return {"id": user_id, "updated_at": update_fields["updated_at"].isoformat()}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    request: Request,
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Delete a user."""
    existing = await db.users.find_one({"_id": user_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    await db.users.delete_one({"_id": user_id})
    await log_user_action(request, current_user, "user_deleted", "user", user_id)
    return None


@router.post("/users/{user_id}/api-keys", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: Request,
    user_id: str,
    body: ApiKeyCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Generate an API key for a user."""

    existing = await db.users.find_one({"_id": user_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    import secrets
    key_id = str(uuid_lib.uuid4())
    raw_key = f"dt_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key_entry = {
        "key_id": key_id,
        "key_hash": key_hash,
        "name": body.name,
        "permissions": body.permissions,
        "is_active": True,
        "last_used_at": None,
        "created_at": datetime.now(timezone.utc),
        "expires_at": None,
    }

    await db.users.update_one(
        {"_id": user_id},
        {"$push": {"api_keys": api_key_entry}},
    )

    await log_user_action(
        request, current_user, "api_key_created", "api_key", key_id,
        details={"user_id": user_id, "name": body.name},
    )

    return {
        "key_id": key_id,
        "name": body.name,
        "key": raw_key,
        "created_at": api_key_entry["created_at"].isoformat(),
    }


# ─── Audit Logs ───────────────────────────────────────────────────────────────


@router.get("/audit-logs", response_model=dict)
async def get_audit_logs(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("admin", "auditor")),
):
    """Get audit logs with optional filters."""
    per_page = min(per_page, 100)
    query = {}

    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action
    if date_from:
        query["timestamp"] = query.get("timestamp", {})
        query["timestamp"]["$gte"] = int(datetime.fromisoformat(date_from).timestamp())
    if date_to:
        query["timestamp"] = query.get("timestamp", {})
        query["timestamp"]["$lte"] = int(datetime.fromisoformat(date_to).timestamp())

    total = await db.audit_logs.count_documents(query)
    cursor = (
        db.audit_logs.find(query)
        .sort("timestamp", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    logs = await cursor.to_list(length=per_page)

    data = []
    for log in logs:
        data.append(
            AuditLogResponse(
                id=str(log["_id"]),
                timestamp=datetime.fromtimestamp(log.get("timestamp", 0), timezone.utc),
                user_id=log.get("user_id", ""),
                user_name=log.get("user_name", ""),
                action=log.get("action", ""),
                resource_type=log.get("resource_type", ""),
                resource_id=log.get("resource_id", ""),
                details=log.get("details"),
                ip_address=log.get("ip_address"),
                user_agent=log.get("user_agent"),
            )
        )

    return {
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        },
    }


# ─── Health Check ─────────────────────────────────────────────────────────────


@router.get("/health", response_model=dict)
async def system_health(
    db: AsyncIOMotorDatabase = Depends(get_db),
    es: AsyncElasticsearch = Depends(get_es),
    redis: AsyncRedis = Depends(get_redis),
):
    """Get system health status for all services."""
    services = {}

    # API Gateway
    services["api_gateway"] = {"status": "up"}

    # MongoDB
    try:
        await db.command("ping")
        services["mongodb"] = {"status": "up", "health": "healthy"}
    except Exception as e:
        services["mongodb"] = {"status": "down", "error": str(e)}

    # Elasticsearch
    try:
        health = await es.cluster.health()
        services["elasticsearch"] = {
            "status": "up",
            "health": health.get("status", "unknown"),
        }
    except Exception as e:
        services["elasticsearch"] = {"status": "down", "error": str(e)}

    # Redis
    try:
        await redis.ping()
        services["redis"] = {"status": "up"}
    except Exception as e:
        services["redis"] = {"status": "down", "error": str(e)}

    # Neo4j
    try:
        neo4j_driver = await get_neo4j()
        async with neo4j_driver.session(database="neo4j") as session:
            result = await session.run("RETURN 1 as val")
            await result.single()
        services["neo4j"] = {"status": "up"}
    except Exception as e:
        services["neo4j"] = {"status": "down", "error": str(e)}

    # Crawler
    try:
        from app.crawler.scheduler import get_scheduler
        scheduler = await get_scheduler()
        jobs = await scheduler.get_all_jobs()
        services["crawler"] = {"status": "up", "workers": 2, "queue_depth": len(jobs)}
    except Exception as e:
        services["crawler"] = {"status": "unknown", "error": str(e)}

    # Determine overall status
    all_up = all(s.get("status") == "up" for s in services.values())
    any_down = any(s.get("status") == "down" for s in services.values())

    if all_up:
        overall = "healthy"
    elif any_down:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "services": services,
    }


# ─── Reprocess Content ──────────────────────────────────────────────────────


@router.post("/reprocess", response_model=dict)
async def reprocess_content(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Reprocess all unprocessed or previously crawled content through the pipeline.

    This is useful after initial deployment to backfill alerts and actor profiles.
    """
    from app.pipeline import process_crawled_content
    import asyncio

    # Find content that hasn't been processed through the full pipeline yet
    unprocessed = await db.raw_content.find(
        {"$or": [
            {"processing_status": {"$in": ["parsed", None]}},
            {"processing_status": {"$exists": False}},
        ]}
    ).sort("fetch_timestamp", -1).limit(500).to_list(length=500)

    if not unprocessed:
        return {"message": "No unprocessed content found", "reprocessed": 0}

    tasks = []
    for doc in unprocessed:
        content_id = str(doc["_id"])
        tasks.append(process_crawled_content(content_id, doc))

    # Run in batches of 10 to avoid overwhelming resources
    batch_size = 10
    completed = 0
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        results = await asyncio.gather(*batch, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("status") == "completed":
                completed += 1

    await log_user_action(
        request, current_user, "content_reprocessed", "content", "bulk",
        details={"total_found": len(unprocessed), "completed": completed},
    )

    return {
        "message": f"Reprocessed {completed} of {len(unprocessed)} content items",
        "total_found": len(unprocessed),
        "completed": completed,
    }
