"""Dashboard API endpoints — summary, trending, timeline."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch

from app.dependencies import get_db, get_es, get_current_user, CurrentUser, require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=dict)
async def dashboard_summary(
    db: AsyncIOMotorDatabase = Depends(get_db),
    es: AsyncElasticsearch = Depends(get_es),
    current_user: CurrentUser = Depends(require_permission("dashboard:read")),
):
    """Get dashboard summary with key metrics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    last_24h = now - timedelta(hours=24)

    # Active alerts by severity
    alert_pipeline = [
        {"$match": {"created_at": {"$gte": last_24h}}},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
    ]
    severity_counts = await db.alerts.aggregate(alert_pipeline).to_list(length=None)
    active_alerts = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for r in severity_counts:
        sev = r["_id"]
        active_alerts[sev] = active_alerts.get(sev, 0) + r["count"]
        active_alerts["total"] += r["count"]

    # Alert trend compared to yesterday
    yesterday_counts = await db.alerts.count_documents({
        "created_at": {"$gte": yesterday_start, "$lt": today_start},
    })
    today_counts = await db.alerts.count_documents({
        "created_at": {"$gte": today_start},
    })
    trend_pct = 0
    if yesterday_counts > 0:
        trend_pct = round(((today_counts - yesterday_counts) / yesterday_counts) * 100, 1)

    # Crawler status
    active_targets = await db.crawl_targets.count_documents({"status": "active"})
    queued_jobs = await db.crawl_jobs.count_documents({"status": "queued"})
    running_jobs = await db.crawl_jobs.count_documents({"status": "in_progress"})
    pages_today = await db.raw_content.count_documents({
        "fetch_timestamp": {"$gte": today_start},
    })

    # Success rate
    total_jobs_today = await db.crawl_jobs.count_documents({
        "started_at": {"$gte": today_start},
    })
    failed_jobs_today = await db.crawl_jobs.count_documents({
        "started_at": {"$gte": today_start},
        "status": "failed",
    })
    success_rate = 100.0
    if total_jobs_today > 0:
        success_rate = round(((total_jobs_today - failed_jobs_today) / total_jobs_today) * 100, 1)

    # Actor stats
    total_actors = await db.actor_profiles.count_documents({})
    high_risk_actors = await db.actor_profiles.count_documents({"risk_score": {"$gte": 600}})
    new_actors_today = await db.actor_profiles.count_documents({
        "first_seen": {"$gte": today_start},
    })

    # Recent alerts
    recent_cursor = (
        db.alerts.find()
        .sort("created_at", -1)
        .limit(5)
    )
    recent_alerts = []
    async for a in recent_cursor:
        recent_alerts.append({
            "id": str(a["_id"]),
            "title": a.get("title", ""),
            "severity": a.get("severity", "medium"),
            "created_at": a.get("created_at"),
            "source_type": a.get("source_type", "onion"),
        })

    # Top categories
    category_pipeline = [
        {"$match": {"created_at": {"$gte": last_24h}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    top_categories = []
    async for r in db.alerts.aggregate(category_pipeline):
        top_categories.append({
            "category": r["_id"],
            "count": r["count"],
            "trend": "+0%",  # Would need historical comparison
        })

    return {
        "active_alerts": {
            **active_alerts,
            "trend": f"{trend_pct:+.1f}%",
        },
        "crawler_status": {
            "active_targets": active_targets,
            "queued_jobs": queued_jobs,
            "running_jobs": running_jobs,
            "pages_today": pages_today,
            "success_rate": f"{success_rate}%",
        },
        "actors": {
            "total_tracked": total_actors,
            "high_risk": high_risk_actors,
            "new_today": new_actors_today,
        },
        "recent_alerts": recent_alerts,
        "top_categories": top_categories,
    }


@router.get("/trending", response_model=dict)
async def dashboard_trending(
    days: int = 7,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard:read")),
):
    """Get trending data — products, marketplaces, actors, language distribution."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    # Most mentioned products (from classification)
    product_pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    most_mentioned = []
    async for r in db.alerts.aggregate(product_pipeline):
        if r["_id"]:
            most_mentioned.append({
                "product": r["_id"].replace("_", " ").title(),
                "mentions": r["count"],
                "trend": "+0%",
            })

    # Most active sites
    sites_pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {"_id": "$source_site", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    active_sites = []
    async for r in db.alerts.aggregate(sites_pipeline):
        if r["_id"]:
            active_sites.append({
                "site": r["_id"],
                "posts": r["count"],
                "trend": "+0%",
            })

    # Top threat actors
    actor_cursor = (
        db.actor_profiles.find()
        .sort("risk_score", -1)
        .limit(10)
    )
    top_actors = []
    async for a in actor_cursor:
        pseudonyms = a.get("pseudonyms", [])
        top_actors.append({
            "pseudonym": pseudonyms[0] if pseudonyms else "Unknown",
            "risk_score": a.get("risk_score", 0),
            "recent_posts": a.get("total_posts", 0),
        })

    # Language distribution
    lang_pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    total_lang = 0
    lang_counts = {}
    async for r in db.alerts.aggregate(lang_pipeline):
        if r["_id"]:
            lang_counts[r["_id"]] = r["count"]
            total_lang += r["count"]

    lang_dist = []
    if total_lang > 0:
        for lang, count in lang_counts.items():
            lang_dist.append({
                "language": lang,
                "percentage": round((count / total_lang) * 100, 1),
            })
        lang_dist.sort(key=lambda x: x["percentage"], reverse=True)

    return {
        "most_mentioned_products": most_mentioned or [
            {"product": "Example Data", "mentions": 0, "trend": "0%"}
        ],
        "most_active_marketplaces": active_sites or [
            {"site": "Example Site", "posts": 0, "trend": "0%"}
        ],
        "top_threat_actors": top_actors or [
            {"pseudonym": "Unknown", "risk_score": 0, "recent_posts": 0}
        ],
        "language_distribution": lang_dist or [
            {"language": "en", "percentage": 100.0}
        ],
    }


@router.get("/timeline", response_model=dict)
async def dashboard_timeline(
    days: int = 7,
    granularity: str = "day",
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("dashboard:read")),
):
    """Get timeline data for activity charts."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    date_format = {
        "hour": "%Y-%m-%dT%H:00:00",
        "day": "%Y-%m-%d",
        "week": "%Y-%W",
        "month": "%Y-%m",
    }.get(granularity, "%Y-%m-%d")

    # Alert timeline
    alert_pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": date_format, "date": "$created_at"}},
                "alerts": {"$sum": 1},
                "critical": {"$sum": {"$cond": [{"$eq": ["$severity", "critical"]}, 1, 0]}},
                "high": {"$sum": {"$cond": [{"$eq": ["$severity", "high"]}, 1, 0]}},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    alert_timeline = []
    async for r in db.alerts.aggregate(alert_pipeline):
        alert_timeline.append({
            "date": r["_id"],
            "alerts": r["alerts"],
            "critical": r["critical"],
            "high": r["high"],
        })

    # Crawl timeline
    crawl_pipeline = [
        {"$match": {"fetch_timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": date_format, "date": "$fetch_timestamp"}},
                "pages": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    crawl_timeline = []
    async for r in db.raw_content.aggregate(crawl_pipeline):
        crawl_timeline.append({
            "date": r["_id"],
            "pages": r["pages"],
        })

    return {
        "alert_timeline": alert_timeline,
        "crawl_timeline": crawl_timeline,
        "period": f"last_{days}_days",
    }
