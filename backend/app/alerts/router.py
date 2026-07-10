"""Alerts API endpoints — list, detail, update, bulk, stats."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch

from app.alerts.models import (
    AlertResponse,
    AlertDetailResponse,
    AlertUpdateRequest,
    AlertBulkUpdateRequest,
    AlertStatsResponse,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertCondition,
    AlertNotification,
)
from app.dependencies import (
    get_db,
    get_es,
    get_current_user,
    CurrentUser,
    require_permission,
    log_user_action,
)
from app.dependencies import get_redis_client
from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])
alert_rules_router = APIRouter(prefix="/alert-rules", tags=["Alert Rules"])


# ─── Alerts ───────────────────────────────────────────────────────────────────


@router.get("", response_model=dict)
async def list_alerts(
    request: Request,
    page: int = 1,
    per_page: int = 25,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    source_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    q: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncIOMotorDatabase = Depends(get_db),
    es: AsyncElasticsearch = Depends(get_es),
    current_user: CurrentUser = Depends(require_permission("alerts:read")),
):
    """List alerts with filtering, pagination, and full-text search."""
    per_page = min(per_page, 100)

    # Build query
    query = {}
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    if source_type:
        query["source_type"] = source_type
    if date_from:
        query["created_at"] = query.get("created_at", {})
        query["created_at"]["$gte"] = datetime.fromisoformat(date_from)
    if date_to:
        query["created_at"] = query.get("created_at", {})
        query["created_at"]["$lte"] = datetime.fromisoformat(date_to)

    # Full-text search via Elasticsearch if q is provided
    if q:
        try:
            es_query = {
                "bool": {
                    "must": [
                        {"multi_match": {
                            "query": q,
                            "fields": ["title^3", "summary^2", "matched_keywords", "actor_pseudonym"],
                            "fuzziness": "AUTO",
                        }}
                    ]
                }
            }
            if severity:
                es_query["bool"]["filter"] = [{"term": {"severity": severity}}]
            if status:
                es_query["bool"]["filter"] = es_query["bool"].get("filter", []) + [{"term": {"status": status}}]
            if category:
                es_query["bool"]["filter"] = es_query["bool"].get("filter", []) + [{"term": {"category": category}}]

            es_result = await es.search(
                index="alerts",
                body={
                    "query": es_query,
                    "from": (page - 1) * per_page,
                    "size": per_page,
                    "sort": [{sort_by: {"order": sort_order}}],
                },
            )
            alert_ids = [hit["_id"] for hit in es_result["hits"]["hits"]]
            total = es_result["hits"]["total"]["value"]

            # Fetch full documents from MongoDB
            cursor = db.alerts.find({"_id": {"$in": alert_ids}})
            alerts_map = {}
            async for a in cursor:
                alerts_map[str(a["_id"])] = a
            # Preserve ES ordering
            alerts = [alerts_map.get(aid) for aid in alert_ids if aid in alerts_map]
        except Exception as e:
            logger.warning("ES search failed, falling back to MongoDB: %s", e)
            # Fallback to MongoDB text search
            query["$text"] = {"$search": q}
            total = await db.alerts.count_documents(query)
            sort_dir = -1 if sort_order == "desc" else 1
            cursor = (
                db.alerts.find(query)
                .sort(sort_by, sort_dir)
                .skip((page - 1) * per_page)
                .limit(per_page)
            )
            alerts = await cursor.to_list(length=per_page)
    else:
        total = await db.alerts.count_documents(query)
        sort_dir = -1 if sort_order == "desc" else 1
        cursor = (
            db.alerts.find(query)
            .sort(sort_by, sort_dir)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        alerts = await cursor.to_list(length=per_page)

    data = []
    for a in alerts:
        data.append(
            AlertResponse(
                id=str(a["_id"]),
                title=a.get("title", ""),
                severity=a.get("severity", "medium"),
                score=a.get("score", 0),
                status=a.get("status", "new"),
                category=a.get("category", "unknown"),
                source_type=a.get("source_type", "onion"),
                source_url=a.get("source_url"),
                created_at=a.get("created_at", datetime.now(timezone.utc)),
                acknowledged_by=a.get("acknowledged_by"),
                summary=a.get("summary"),
                matched_keywords=a.get("matched_keywords", []),
                actor_pseudonym=a.get("actor_pseudonym"),
                actor_profile_id=a.get("actor_profile_id"),
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


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    request: Request,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    granularity: str = "day",
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("alerts:read")),
):
    """Get alert statistics with trend data."""
    now = datetime.now(timezone.utc)
    if date_from:
        start_date = datetime.fromisoformat(date_from)
    else:
        start_date = now - timedelta(days=7)
    if date_to:
        end_date = datetime.fromisoformat(date_to)
    else:
        end_date = now

    query = {"created_at": {"$gte": start_date, "$lte": end_date}}

    # Total
    total = await db.alerts.count_documents(query)

    # By severity
    severity_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
    ]
    severity_results = await db.alerts.aggregate(severity_pipeline).to_list(length=None)
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for r in severity_results:
        by_severity[r["_id"]] = r["count"]

    # By category
    category_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    ]
    category_results = await db.alerts.aggregate(category_pipeline).to_list(length=None)
    by_category = {}
    for r in category_results:
        by_category[r["_id"]] = r["count"]

    # By status
    status_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    status_results = await db.alerts.aggregate(status_pipeline).to_list(length=None)
    by_status = {"new": 0, "acknowledged": 0, "investigating": 0, "resolved": 0, "false_positive": 0}
    for r in status_results:
        by_status[r["_id"]] = r["count"]

    # Trend data
    date_format = {
        "hour": "%Y-%m-%dT%H:00:00",
        "day": "%Y-%m-%d",
        "week": "%Y-%W",
        "month": "%Y-%m",
    }.get(granularity, "%Y-%m-%d")

    trend_pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": {"$dateToString": {"format": date_format, "date": "$created_at"}},
                "count": {"$sum": 1},
                "critical": {"$sum": {"$cond": [{"$eq": ["$severity", "critical"]}, 1, 0]}},
                "high": {"$sum": {"$cond": [{"$eq": ["$severity", "high"]}, 1, 0]}},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    trend_results = await db.alerts.aggregate(trend_pipeline).to_list(length=None)
    trend = [
        {"date": r["_id"], "count": r["count"], "critical": r["critical"], "high": r["high"]}
        for r in trend_results
    ]

    return AlertStatsResponse(
        total=total,
        by_severity=by_severity,
        by_category=by_category,
        by_status=by_status,
        trend=trend,
    )


@router.get("/{alert_id}", response_model=AlertDetailResponse)
async def get_alert(
    alert_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("alerts:read")),
):
    """Get detailed alert information."""
    alert = await db.alerts.find_one({"_id": alert_id})
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return AlertDetailResponse(
        id=str(alert["_id"]),
        title=alert.get("title", ""),
        severity=alert.get("severity", "medium"),
        score=alert.get("score", 0),
        score_breakdown=alert.get("score_breakdown"),
        status=alert.get("status", "new"),
        assignee=alert.get("assignee"),
        category=alert.get("category", "unknown"),
        source={
            "url": alert.get("source_url"),
            "site_name": alert.get("source_site"),
            "source_type": alert.get("source_type"),
            "crawl_timestamp": alert.get("created_at").isoformat() if alert.get("created_at") else None,
        },
        content={
            "title": alert.get("title"),
            "author": alert.get("actor_pseudonym"),
            "content_text": alert.get("summary"),
        },
        entities=alert.get("entities"),
        analysis=alert.get("analysis"),
        actor={
            "profile_id": alert.get("actor_profile_id"),
            "pseudonyms": [alert.get("actor_pseudonym")] if alert.get("actor_pseudonym") else [],
        } if alert.get("actor_pseudonym") else None,
        timeline=alert.get("timeline", []),
        related_alerts=alert.get("related_alerts", []),
        created_at=alert.get("created_at", datetime.now(timezone.utc)),
        updated_at=alert.get("updated_at", datetime.now(timezone.utc)),
    )


@router.patch("/{alert_id}", response_model=dict)
async def update_alert(
    request: Request,
    alert_id: str,
    body: AlertUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    es: AsyncElasticsearch = Depends(get_es),
    current_user: CurrentUser = Depends(require_permission("alerts:write")),
):
    """Update alert status and/or assignee."""
    alert = await db.alerts.find_one({"_id": alert_id})
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    now = datetime.now(timezone.utc)
    update_fields = {
        "status": body.status,
        "updated_at": now,
    }
    if body.assignee:
        update_fields["assignee"] = body.assignee
    if body.comment:
        update_fields["$push"] = {"comments": {
            "user_id": current_user.id,
            "user_name": current_user.name,
            "text": body.comment,
            "timestamp": now.isoformat(),
        }}

    # Add timeline entry
    await db.alerts.update_one(
        {"_id": alert_id},
        {
            "$set": update_fields,
            "$push": {
                "timeline": {
                    "event": f"status_{body.status}",
                    "timestamp": now.isoformat(),
                    "detail": f"Status changed to {body.status} by {current_user.name}",
                }
            },
        },
    )

    # Update Elasticsearch
    try:
        await es.update(
            index="alerts",
            id=alert_id,
            body={
                "doc": {
                    "status": body.status,
                    "assignee": body.assignee,
                    "updated_at": now.isoformat(),
                }
            },
        )
    except Exception as e:
        logger.warning("ES update failed for alert %s: %s", alert_id, e)

    await log_user_action(
        request, current_user, "alert_update", "alert", alert_id,
        details={"status": body.status, "assignee": body.assignee},
    )

    return {
        "id": alert_id,
        "status": body.status,
        "assignee": body.assignee,
        "updated_at": now.isoformat(),
    }


@router.post("/bulk", response_model=dict)
async def bulk_update_alerts(
    request: Request,
    body: AlertBulkUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("alerts:write")),
):
    """Bulk update alerts (acknowledge, investigate, resolve, false positive)."""
    status_map = {
        "acknowledge": "acknowledged",
        "investigating": "investigating",
        "resolved": "resolved",
        "false_positive": "false_positive",
    }
    new_status = status_map.get(body.action, "acknowledged")

    now = datetime.now(timezone.utc)
    result = await db.alerts.update_many(
        {"_id": {"$in": body.alert_ids}},
        {
            "$set": {
                "status": new_status,
                "assignee": body.assignee,
                "updated_at": now,
            },
            "$push": {
                "timeline": {
                    "event": f"bulk_{new_status}",
                    "timestamp": now.isoformat(),
                    "detail": f"Bulk status changed to {new_status} by {current_user.name}",
                }
            },
        },
    )

    await log_user_action(
        request, current_user, "alert_bulk_update", "alert", ",".join(body.alert_ids),
        details={"action": body.action, "count": result.modified_count},
    )

    return {
        "updated_count": result.modified_count,
        "message": f"{result.modified_count} alerts {new_status}",
    }


# ─── Alert Rules ──────────────────────────────────────────────────────────────


@alert_rules_router.get("", response_model=dict)
async def list_alert_rules(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("alerts:read")),
):
    """List all alert rules."""
    cursor = db.alert_rules.find().sort("created_at", -1)
    rules = await cursor.to_list(length=None)
    data = []
    for r in rules:
        data.append({
            "id": str(r["_id"]),
            "name": r.get("name", ""),
            "description": r.get("description", ""),
            "enabled": r.get("enabled", True),
            "severity_threshold": r.get("severity_threshold", 400),
            "conditions": r.get("conditions", []),
            "notifications": r.get("notifications", []),
            "created_by": str(r.get("created_by", "")),
            "created_at": r.get("created_at"),
            "triggered_count": r.get("match_count", 0),
        })
    return {"data": data}


@alert_rules_router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    request: Request,
    body: AlertRuleCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("alerts:write")),
):
    """Create a new alert rule."""
    from datetime import datetime, timezone
    import uuid

    rule_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    rule_doc = {
        "_id": rule_id,
        "name": body.name,
        "description": body.description or "",
        "enabled": body.enabled,
        "severity_threshold": body.severity_threshold,
        "conditions": [c.dict() for c in body.conditions],
        "notifications": [n.dict() for n in body.notifications],
        "cooldown_minutes": body.cooldown_minutes,
        "match_count": 0,
        "last_triggered_at": None,
        "created_by": current_user.id,
        "created_at": now,
        "updated_at": now,
    }
    await db.alert_rules.insert_one(rule_doc)

    await log_user_action(
        request, current_user, "alert_rule_created", "alert_rule", rule_id,
        details={"name": body.name},
    )

    return {"id": rule_id, "name": body.name, "created_at": now.isoformat()}


@alert_rules_router.put("/{rule_id}", response_model=dict)
async def update_alert_rule(
    request: Request,
    rule_id: str,
    body: AlertRuleUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("alerts:write")),
):
    """Update an alert rule."""
    existing = await db.alert_rules.find_one({"_id": rule_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    update_fields = {"updated_at": datetime.now(timezone.utc)}
    for field in ["name", "description", "enabled", "severity_threshold", "conditions", "notifications", "cooldown_minutes"]:
        val = getattr(body, field, None)
        if val is not None:
            if field in ("conditions", "notifications"):
                update_fields[field] = [v.dict() if hasattr(v, 'dict') else v for v in val]
            else:
                update_fields[field] = val

    await db.alert_rules.update_one({"_id": rule_id}, {"$set": update_fields})

    await log_user_action(
        request, current_user, "alert_rule_updated", "alert_rule", rule_id,
    )

    return {"id": rule_id, "updated_at": update_fields["updated_at"].isoformat()}


@alert_rules_router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    request: Request,
    rule_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("alerts:write")),
):
    """Delete an alert rule."""
    existing = await db.alert_rules.find_one({"_id": rule_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await db.alert_rules.delete_one({"_id": rule_id})
    await log_user_action(request, current_user, "alert_rule_deleted", "alert_rule", rule_id)
    return None
