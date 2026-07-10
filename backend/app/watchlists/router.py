"""Watchlists CRUD API endpoints."""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.watchlists.models import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    RegexPattern,
    new_watchlist_document,
)
from app.dependencies import (
    get_db,
    get_current_user,
    CurrentUser,
    require_permission,
    log_user_action,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


@router.get("", response_model=dict)
async def list_watchlists(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("watchlists:read")),
):
    """List all watchlists."""
    cursor = db.watchlists.find().sort("created_at", -1)
    watchlists = await cursor.to_list(length=None)
    data = []
    for w in watchlists:
        data.append(
            WatchlistResponse(
                id=str(w["_id"]),
                name=w.get("name", ""),
                description=w.get("description"),
                keywords=w.get("keywords", []),
                regex_patterns=[RegexPattern(**p) for p in w.get("regex_patterns", [])],
                entities=w.get("entities", []),
                severity_boost=w.get("severity_boost", 100),
                is_active=w.get("is_active", True),
                created_by=str(w.get("created_by", "")),
                created_at=w.get("created_at"),
                match_count=w.get("match_count", 0),
            )
        )
    return {"data": data}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    request: Request,
    body: WatchlistCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("watchlists:write")),
):
    """Create a new watchlist."""
    doc = new_watchlist_document(body, current_user.id)
    await db.watchlists.insert_one(doc)

    await log_user_action(
        request, current_user, "watchlist_created", "watchlist", doc["_id"],
        details={"name": body.name},
    )

    return {"id": doc["_id"], "name": body.name, "created_at": doc["created_at"].isoformat()}


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("watchlists:read")),
):
    """Get a single watchlist."""
    w = await db.watchlists.find_one({"_id": watchlist_id})
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")

    return WatchlistResponse(
        id=str(w["_id"]),
        name=w.get("name", ""),
        description=w.get("description"),
        keywords=w.get("keywords", []),
        regex_patterns=[RegexPattern(**p) for p in w.get("regex_patterns", [])],
        entities=w.get("entities", []),
        severity_boost=w.get("severity_boost", 100),
        is_active=w.get("is_active", True),
        created_by=str(w.get("created_by", "")),
        created_at=w.get("created_at"),
        match_count=w.get("match_count", 0),
    )


@router.put("/{watchlist_id}", response_model=dict)
async def update_watchlist(
    request: Request,
    watchlist_id: str,
    body: WatchlistUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("watchlists:write")),
):
    """Update a watchlist."""
    existing = await db.watchlists.find_one({"_id": watchlist_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")

    update_fields = {"updated_at": datetime.now(timezone.utc)}
    for field in ["name", "description", "keywords", "entities", "severity_boost", "is_active"]:
        val = getattr(body, field, None)
        if val is not None:
            update_fields[field] = val
    if body.regex_patterns is not None:
        update_fields["regex_patterns"] = [p.dict() for p in body.regex_patterns]

    await db.watchlists.update_one({"_id": watchlist_id}, {"$set": update_fields})

    await log_user_action(
        request, current_user, "watchlist_updated", "watchlist", watchlist_id,
    )

    return {"id": watchlist_id, "updated_at": update_fields["updated_at"].isoformat()}


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    request: Request,
    watchlist_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("watchlists:write")),
):
    """Delete a watchlist."""
    existing = await db.watchlists.find_one({"_id": watchlist_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")
    await db.watchlists.delete_one({"_id": watchlist_id})
    await log_user_action(request, current_user, "watchlist_deleted", "watchlist", watchlist_id)
    return None
