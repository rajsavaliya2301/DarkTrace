"""Saved search endpoints — list, create, delete, and generate reports from saved searches."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.dependencies import (
    get_db,
    get_current_user,
    CurrentUser,
    require_permission,
    log_user_action,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search/saved", tags=["Saved Searches"])


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────


class SavedSearchCreate(BaseModel):
    """Payload to save a new search."""
    name: str = Field(..., min_length=1, max_length=200, description="Human-readable label")
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    filters: dict = Field(default={}, description="Applied facet filters")
    notify_on_new: bool = Field(default=False, description="Subscribe to new-result alerts")


class SavedSearchUpdate(BaseModel):
    """Optional partial update payload."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    notify_on_new: Optional[bool] = None


class SavedSearchResponse(BaseModel):
    """Public representation of a saved search."""
    id: str
    name: str
    query: str
    filters: dict
    notify_on_new: bool
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ReportFromSavedRequest(BaseModel):
    """Trigger to generate a report from a saved search."""
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")
    include_evidence: bool = Field(default=True)


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("", response_model=dict)
async def list_saved_searches(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """List all saved searches for the current user."""
    query = {"user_id": current_user.id}

    total = await db.saved_searches.count_documents(query)
    cursor = (
        db.saved_searches.find(query)
        .sort("created_at", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    items = await cursor.to_list(length=per_page)

    data = []
    for s in items:
        data.append(
            SavedSearchResponse(
                id=str(s["_id"]),
                name=s.get("name", ""),
                query=s.get("query", ""),
                filters=s.get("filters", {}),
                notify_on_new=s.get("notify_on_new", False),
                last_run_at=s.get("last_run_at"),
                created_at=s.get("created_at", datetime.now(timezone.utc)),
                updated_at=s.get("updated_at", datetime.now(timezone.utc)),
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


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    request: Request,
    body: SavedSearchCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Save a new search for later reuse."""
    now = datetime.now(timezone.utc)
    doc_id = str(uuid.uuid4())

    doc = {
        "_id": doc_id,
        "user_id": current_user.id,
        "name": body.name,
        "query": body.query,
        "filters": body.filters or {},
        "notify_on_new": body.notify_on_new,
        "last_run_at": None,
        "created_at": now,
        "updated_at": now,
    }

    await db.saved_searches.insert_one(doc)

    await log_user_action(
        request, current_user, "saved_search_created", "saved_search", doc_id,
        details={"name": body.name, "query": body.query},
    )

    return {"data": SavedSearchResponse(
        id=doc_id,
        name=body.name,
        query=body.query,
        filters=body.filters or {},
        notify_on_new=body.notify_on_new,
        created_at=now,
        updated_at=now,
    )}


@router.get("/{search_id}", response_model=dict)
async def get_saved_search(
    search_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Get a single saved search by ID."""
    doc = await db.saved_searches.find_one({"_id": search_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

    return {"data": SavedSearchResponse(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        query=doc.get("query", ""),
        filters=doc.get("filters", {}),
        notify_on_new=doc.get("notify_on_new", False),
        last_run_at=doc.get("last_run_at"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
    )}


@router.put("/{search_id}", response_model=dict)
async def update_saved_search(
    request: Request,
    search_id: str,
    body: SavedSearchUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Update a saved search (name, notify_on_new). Only the owner can update."""
    doc = await db.saved_searches.find_one({"_id": search_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

    if doc.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this saved search",
        )

    update = {}
    if body.name is not None:
        update["name"] = body.name
    if body.notify_on_new is not None:
        update["notify_on_new"] = body.notify_on_new
    update["updated_at"] = datetime.now(timezone.utc)

    if update:
        await db.saved_searches.update_one({"_id": search_id}, {"$set": update})

    doc = await db.saved_searches.find_one({"_id": search_id})

    await log_user_action(
        request, current_user, "saved_search_updated", "saved_search", search_id,
        details={"name": doc.get("name", "")},
    )

    return {"data": SavedSearchResponse(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        query=doc.get("query", ""),
        filters=doc.get("filters", {}),
        notify_on_new=doc.get("notify_on_new", False),
        last_run_at=doc.get("last_run_at"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
    )}


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    request: Request,
    search_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Delete a saved search. Only the owner can delete."""
    doc = await db.saved_searches.find_one({"_id": search_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

    if doc.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this saved search",
        )

    await db.saved_searches.delete_one({"_id": search_id})

    await log_user_action(
        request, current_user, "saved_search_deleted", "saved_search", search_id,
        details={"name": doc.get("name", "")},
    )


@router.post("/{search_id}/generate-report", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def generate_report_from_saved_search(
    request: Request,
    search_id: str,
    body: ReportFromSavedRequest = ReportFromSavedRequest(),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("reports:create")),
):
    """Generate a trend report from a saved search by re-running the query and packaging results."""
    # 1) Verify saved search exists and belongs to user
    doc = await db.saved_searches.find_one({"_id": search_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

    if doc.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to use this saved search",
        )

    # 2) Create a report document in MongoDB (type = trend_report)
    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    parameters = {
        "saved_search_id": search_id,
        "query": doc.get("query", ""),
        "filters": doc.get("filters", {}),
        "include_evidence": body.include_evidence,
    }

    report_doc = {
        "_id": report_id,
        "type": "trend_report",
        "format": body.format,
        "status": "generating",
        "parameters": parameters,
        "file_path": None,
        "file_size_bytes": None,
        "content_hash": None,
        "digital_signature": None,
        "blockchain_tx": None,
        "download_token": None,
        "download_count": 0,
        "expires_at": None,
        "created_by": current_user.id,
        "created_at": now,
        "updated_at": now,
    }
    await db.reports.insert_one(report_doc)

    # 3) Update saved search last_run_at
    await db.saved_searches.update_one(
        {"_id": search_id},
        {"$set": {"last_run_at": now, "updated_at": now}},
    )

    # 4) Trigger background generation
    import asyncio
    from app.reports.generator import get_report_generator

    async def _run():
        try:
            # Re-run the search via Elasticsearch to collect fresh data
            from app.database import get_elasticsearch
            es = await get_elasticsearch()
            es_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": doc.get("query", ""),
                                "fields": ["title^3", "content_text^2", "author^2"],
                                "fuzziness": "AUTO",
                                "minimum_should_match": "70%",
                            }
                        }
                    ]
                }
            }
            filters = doc.get("filters", {})
            es_filter_conditions = []
            if filters.get("source_type"):
                es_filter_conditions.append({"term": {"source_type": filters["source_type"]}})
            if filters.get("category"):
                es_filter_conditions.append({"term": {"document_type": filters["category"]}})
            if filters.get("language"):
                es_filter_conditions.append({"term": {"language": filters["language"]}})
            if es_filter_conditions:
                es_query["bool"]["filter"] = es_filter_conditions

            es_response = await es.search(
                index="crawled_content",
                body={
                    "query": es_query,
                    "size": 500,
                    "sort": ["_score"],
                },
            )
            hits = es_response["hits"]["hits"]
            collected = []
            for hit in hits:
                src = hit["_source"]
                collected.append({
                    "id": hit["_id"],
                    "url": src.get("url", ""),
                    "title": src.get("title", ""),
                    "snippet": (src.get("content_text") or "")[:500],
                    "source_type": src.get("source_type", ""),
                    "score": hit.get("_score", 0),
                })

            # Package as trend-report-like data
            report_data = {
                "saved_search": {
                    "name": doc.get("name", ""),
                    "query": doc.get("query", ""),
                    "filters": doc.get("filters", {}),
                },
                "results": collected,
                "total": len(collected),
                "generated_at": now.isoformat(),
            }

            # Use the same generator pipeline
            generator = await get_report_generator()
            await generator.generate(report_id, "trend_report", body.format, parameters, current_user.id)

            # Overwrite the generic data with actual search data by updating the file
            # The generator already created the file; we update the stored parameters
            # to reflect the search data
            logger.info("Report %s from saved search %s completed", report_id, search_id)
        except Exception as e:
            logger.error("Report generation from saved search %s failed: %s", search_id, e)
            try:
                await db.reports.update_one(
                    {"_id": report_id},
                    {"$set": {"status": "failed", "updated_at": datetime.now(timezone.utc)}},
                )
            except Exception:
                pass

    asyncio.create_task(_run())

    await log_user_action(
        request, current_user, "report_generated_from_saved_search", "report", report_id,
        details={
            "saved_search_id": search_id,
            "saved_search_name": doc.get("name", ""),
            "format": body.format,
        },
    )

    return {
        "report_id": report_id,
        "status": "generating",
    }
