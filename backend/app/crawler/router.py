"""Crawler API endpoints — targets and jobs management."""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.crawler.engine import get_crawl_engine
from app.crawler.scheduler import get_scheduler
from app.database import get_mongodb
from app.dependencies import (
    get_db,
    get_current_user,
    CurrentUser,
    require_permission,
    log_user_action,
    check_rate_limit,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawler", tags=["Crawler"])


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────


class CrawlTargetCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=1024)
    site_name: str = Field(..., min_length=1, max_length=256)
    source_type: str = Field(default="onion", pattern="^(onion|i2p|surface)$")
    crawl_frequency: str = Field(
        default="every_6h",
        pattern="^(every_1h|every_2h|every_4h|every_6h|every_8h|every_12h|every_24h|every_48h|every_7d|every_30d)$",
    )
    parser_type: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = Field(default=None, max_length=1024)
    tags: Optional[List[str]] = Field(default=None)


class CrawlTargetUpdate(BaseModel):
    site_name: Optional[str] = Field(None, max_length=256)
    source_type: Optional[str] = Field(None, pattern="^(onion|i2p|surface)$")
    crawl_frequency: Optional[str] = Field(
        None, pattern="^(every_1h|every_2h|every_4h|every_6h|every_8h|every_12h|every_24h|every_48h|every_7d|every_30d)$"
    )
    status: Optional[str] = Field(None, pattern="^(active|paused|disabled)$")
    notes: Optional[str] = Field(None, max_length=1024)
    tags: Optional[List[str]] = None


class CrawlTargetResponse(BaseModel):
    id: str
    url: str
    site_name: str
    source_type: str
    status: str
    crawl_frequency: str
    category: Optional[str] = None
    use_tor: bool = False
    last_crawled: Optional[datetime] = None
    last_status: Optional[str] = None
    pages_crawled: int = 0
    added_by: Optional[str] = None
    added_at: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CrawlJobResponse(BaseModel):
    id: str
    target_id: str
    target_url: str
    status: str
    pages_fetched: int = 0
    pages_total: int = 0
    errors: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    proxy_used: Optional[str] = None


class CrawlJobListResponse(BaseModel):
    data: List[CrawlJobResponse]
    pagination: dict


class CrawlTargetListResponse(BaseModel):
    data: List[CrawlTargetResponse]


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/targets", response_model=CrawlTargetListResponse)
async def list_targets(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("crawler:read")),
):
    """List all crawl targets."""
    cursor = db.crawl_targets.find().sort("added_at", -1)
    targets = await cursor.to_list(length=None)
    data = []
    for t in targets:
        proxy_config = t.get("proxy_config", {})
        data.append(
            CrawlTargetResponse(
                id=str(t["_id"]),
                url=t.get("url", ""),
                site_name=t.get("site_name", ""),
                source_type=t.get("source_type", "onion"),
                status=t.get("status", "active"),
                crawl_frequency=t.get("crawl_frequency", "every_6h"),
                category=t.get("category"),
                use_tor=proxy_config.get("use_tor", False) or t.get("is_tor_only", False),
                last_crawled=t.get("last_crawled_at"),
                last_status=t.get("last_crawl_status"),
                pages_crawled=t.get("page_count", 0),
                added_by=str(t.get("added_by", "")),
                added_at=t.get("added_at"),
                notes=t.get("notes"),
                tags=t.get("tags"),
            )
        )
    return CrawlTargetListResponse(data=data)


@router.post("/targets", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_target(
    request: Request,
    body: CrawlTargetCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("crawler:write")),
):
    """Add a new crawl target."""
    # Check duplicate
    existing = await db.crawl_targets.find_one({"url": body.url})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target URL already exists")

    target_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    target_doc = {
        "_id": target_id,
        "url": body.url,
        "site_name": body.site_name,
        "source_type": body.source_type,
        "status": "active",
        "crawl_frequency": body.crawl_frequency,
        "parser_type": body.parser_type or "generic",
        "parser_config": {},
        "auth_info": {},
        "politeness_config": {"crawl_delay": 5.0, "max_concurrent": 4, "max_depth": 2},
        "scope": {"allowed_domains": [], "exclude_patterns": [], "include_patterns": []},
        "last_crawled_at": None,
        "last_crawl_status": None,
        "page_count": 0,
        "reputation_score": 50.0,
        "is_tor_only": body.source_type == "onion",
        "notes": body.notes or "",
        "tags": body.tags or [],
        "added_by": current_user.id,
        "added_at": now,
        "updated_at": now,
    }
    await db.crawl_targets.insert_one(target_doc)

    # Register with scheduler
    scheduler = await get_scheduler()
    await scheduler.add_recurring_job(
        target_id=target_id,
        target_url=body.url,
        frequency=body.crawl_frequency,
        source_type=body.source_type,
    )

    await log_user_action(
        request, current_user, "target_added", "crawl_target", target_id,
        details={"url": body.url, "site_name": body.site_name},
    )

    return {"id": target_id, "url": body.url, "status": "active", "created_at": now.isoformat()}


@router.put("/targets/{target_id}", response_model=dict)
async def update_target(
    request: Request,
    target_id: str,
    body: CrawlTargetUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("crawler:write")),
):
    """Update a crawl target."""
    existing = await db.crawl_targets.find_one({"_id": target_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    update_fields = {}
    for field in ["site_name", "source_type", "crawl_frequency", "status", "notes", "tags"]:
        val = getattr(body, field, None)
        if val is not None:
            update_fields[field] = val
    update_fields["updated_at"] = datetime.now(timezone.utc)

    await db.crawl_targets.update_one({"_id": target_id}, {"$set": update_fields})

    await log_user_action(
        request, current_user, "target_updated", "crawl_target", target_id,
        details={"changes": list(update_fields.keys())},
    )

    return {"id": target_id, "updated_at": update_fields["updated_at"].isoformat()}


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    request: Request,
    target_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("crawler:write")),
):
    """Delete a crawl target."""
    existing = await db.crawl_targets.find_one({"_id": target_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    await db.crawl_targets.delete_one({"_id": target_id})
    await log_user_action(
        request, current_user, "target_deleted", "crawl_target", target_id,
    )
    return None


@router.post("/targets/{target_id}/crawl", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def trigger_crawl(
    request: Request,
    target_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("crawler:write")),
):
    """Trigger an immediate crawl for a target."""
    target = await db.crawl_targets.find_one({"_id": target_id})
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    # Create a crawl job document
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    job_doc = {
        "_id": job_id,
        "id": job_id,  # Engine expects "id" key (see engine.py line 35)
        "target_id": target_id,
        "target_url": target.get("url", ""),
        "site_name": target.get("site_name", "unknown"),
        "source_type": target.get("source_type", "onion"),
        "proxy_config": target.get("proxy_config", {}),
        "status": "queued",
        "priority": 1,
        "scheduled_at": now,
        "started_at": None,
        "completed_at": None,
        "pages_fetched": 0,
        "pages_total": 0,
        "pages_failed": 0,
        "errors": [],
        "proxy_pool_used": [],
        "crawl_depth": target.get("politeness_config", {}).get("max_depth", 2),
        "triggered_by": current_user.id,
        "created_at": now,
        "updated_at": now,
    }
    await db.crawl_jobs.insert_one(job_doc)

    # Execute the crawl (async in background)
    import asyncio
    asyncio.create_task(_execute_crawl_job(job_id, target_id, job_doc))

    await log_user_action(
        request, current_user, "crawl_triggered", "crawl_job", job_id,
        details={"target_url": target.get("url", "")},
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "estimated_completion": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/jobs", response_model=CrawlJobListResponse)
async def list_jobs(
    request: Request,
    status_filter: Optional[str] = None,
    target_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 25,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("crawler:read")),
):
    """List crawl jobs with optional filters."""
    query = {}
    if status_filter:
        query["status"] = status_filter
    if target_id:
        query["target_id"] = target_id

    total = await db.crawl_jobs.count_documents(query)
    cursor = (
        db.crawl_jobs.find(query)
        .sort("created_at", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    jobs = await cursor.to_list(length=per_page)

    data = []
    for j in jobs:
        data.append(
            CrawlJobResponse(
                id=str(j["_id"]),
                target_id=j.get("target_id", ""),
                target_url=j.get("target_url", ""),
                status=j.get("status", "unknown"),
                pages_fetched=j.get("pages_fetched", 0),
                pages_total=j.get("pages_total", 0),
                errors=j.get("pages_failed", 0),
                started_at=j.get("started_at"),
                completed_at=j.get("completed_at"),
                proxy_used=", ".join(j.get("proxy_pool_used", [])),
            )
        )

    return CrawlJobListResponse(
        data=data,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        },
    )


@router.get("/jobs/{job_id}", response_model=CrawlJobResponse)
async def get_job(
    job_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("crawler:read")),
):
    """Get a specific crawl job status."""
    job = await db.crawl_jobs.find_one({"_id": job_id})
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return CrawlJobResponse(
        id=str(job["_id"]),
        target_id=job.get("target_id", ""),
        target_url=job.get("target_url", ""),
        status=job.get("status", "unknown"),
        pages_fetched=job.get("pages_fetched", 0),
        pages_total=job.get("pages_total", 0),
        errors=job.get("pages_failed", 0),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        proxy_used=", ".join(job.get("proxy_pool_used", [])),
    )


async def _execute_crawl_job(job_id: str, target_id: str, job_doc: dict):
    """Background task to execute a crawl job."""
    try:
        db = await get_mongodb()
        engine = await get_crawl_engine()

        # Mark as running
        await db.crawl_jobs.update_one(
            {"_id": job_id},
            {"$set": {"status": "in_progress", "started_at": datetime.now(timezone.utc)}},
        )

        # Execute
        result = await engine.execute_job(job_doc)

        # Mark as completed
        await db.crawl_jobs.update_one(
            {"_id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                    "pages_fetched": result.get("pages_crawled", 0),
                    "pages_total": result.get("pages_crawled", 0),
                    "pages_failed": result.get("errors", 0),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        # Update target last crawled
        await db.crawl_targets.update_one(
            {"_id": target_id},
            {
                "$set": {
                    "last_crawled_at": datetime.now(timezone.utc),
                    "last_crawl_status": "success",
                    "updated_at": datetime.now(timezone.utc),
                },
                "$inc": {"page_count": result.get("pages_crawled", 0)},
            },
        )

        logger.info("Crawl job %s completed: %s", job_id, result)

    except Exception as e:
        logger.error("Crawl job %s failed: %s", job_id, e)
        try:
            db = await get_mongodb()
            await db.crawl_jobs.update_one(
                {"_id": job_id},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
        except Exception:
            pass
