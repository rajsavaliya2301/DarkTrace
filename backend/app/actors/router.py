"""Actors API endpoints — list, detail, graph, search."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.actors.graph import get_actor_graph
from app.dependencies import (
    get_db,
    get_current_user,
    CurrentUser,
    require_permission,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actors", tags=["Actors"])


@router.get("", response_model=dict)
async def list_actors(
    page: int = 1,
    per_page: int = 25,
    risk_score_min: int = 0,
    q: Optional[str] = None,
    sort_by: str = "risk_score",
    current_user: CurrentUser = Depends(require_permission("actors:read")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List actors with pagination and search."""
    actor_graph = await get_actor_graph()
    result = await actor_graph.search_actors(
        search_term=q or "",
        risk_min=risk_score_min,
        page=page,
        per_page=per_page,
    )

    # Enrich actors with URLs/content from MongoDB profiles
    if result.get("data"):
        actor_ids = [a["id"] for a in result["data"]]
        mongo_profiles = await db.actor_profiles.find(
            {"_id": {"$in": actor_ids}},
            {
                "_id": 1,
                "recent_activity": 1,
                "active_platforms": 1,
                "top_categories": 1,
                "linked_entities": 1,
            },
        ).to_list(length=len(actor_ids))

        profile_map = {p["_id"]: p for p in mongo_profiles}

        for actor in result["data"]:
            mongo_data = profile_map.get(actor["id"], {})
            recent = mongo_data.get("recent_activity", [])

            # URLs
            actor["urls"] = list(dict.fromkeys(
                r.get("url", "") for r in recent if r.get("url")
            ))
            first_url = next((r.get("url") for r in recent if r.get("url")), "")
            actor["source_url"] = first_url
            actor["source_title"] = next((r.get("title", "") for r in recent if r.get("url")), "")
            actor["content_ids"] = [r.get("content_id", "") for r in recent if r.get("content_id")]
            actor["recent_activity"] = recent[:5]

            # Fields required by frontend ActorList component
            actor["active_platforms"] = mongo_data.get("active_platforms", [])
            actor["top_categories"] = mongo_data.get("top_categories", [])

            # Convert entity arrays to counts for frontend
            raw_entities = mongo_data.get("linked_entities", {})
            linked_entities = {}
            for key in ("btc_addresses", "emails", "pgp_keys"):
                val = raw_entities.get(key, [])
                linked_entities[key] = len(val) if isinstance(val, list) else (val if isinstance(val, (int, float)) else 0)
            actor["linked_entities"] = linked_entities

    return result


@router.get("/search", response_model=dict)
async def search_actors(
    q: str = "",
    risk_score_min: int = 0,
    page: int = 1,
    per_page: int = 25,
    current_user: CurrentUser = Depends(require_permission("actors:read")),
):
    """Search actors by pseudonym."""
    actor_graph = await get_actor_graph()
    result = await actor_graph.search_actors(
        search_term=q,
        risk_min=risk_score_min,
        page=page,
        per_page=per_page,
    )
    return result


@router.get("/{actor_id}", response_model=dict)
async def get_actor(
    actor_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("actors:read")),
):
    """Get detailed actor profile."""
    # Try Neo4j first
    actor_graph = await get_actor_graph()
    profile = await actor_graph.get_actor_profile(actor_id)

    if not profile:
        # Fallback to MongoDB
        mongo_profile = await db.actor_profiles.find_one({"_id": actor_id})
        if not mongo_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found")

        profile = {
            "id": actor_id,
            "risk_score": mongo_profile.get("risk_score", 0),
            "total_posts": mongo_profile.get("total_posts", 0),
            "first_seen": mongo_profile.get("first_seen"),
            "last_seen": mongo_profile.get("last_seen"),
            "pseudonyms": [{"name": p, "platforms": [], "first_seen": None, "last_seen": None}
                           for p in mongo_profile.get("pseudonyms", [])],
            "linked_entities": mongo_profile.get("linked_entities", {}),
            "connected_actors": [],
        }

    # Fetch additional details from MongoDB
    mongo_profile = await db.actor_profiles.find_one({"_id": actor_id})
    if mongo_profile:
        profile["active_platforms"] = mongo_profile.get("active_platforms", [])
        profile["top_categories"] = mongo_profile.get("top_categories", [])
        profile["activity_timeline"] = mongo_profile.get("activity_timeline", [])
        profile["recent_activity"] = mongo_profile.get("recent_activity", [])
        profile["risk_factors"] = mongo_profile.get("risk_factors", [])

        # Build pseudonyms with platform info
        pseudonyms = []
        for p_name in mongo_profile.get("pseudonyms", []):
            pseudonyms.append({
                "name": p_name,
                "platforms": mongo_profile.get("active_platforms", []),
                "first_seen": mongo_profile.get("first_seen"),
                "last_seen": mongo_profile.get("last_seen"),
            })
        profile["pseudonyms"] = pseudonyms
    else:
        profile["active_platforms"] = []
        profile["top_categories"] = []
        profile["activity_timeline"] = []
        profile["recent_activity"] = []
        profile["risk_factors"] = []

    return profile


@router.get("/{actor_id}/graph", response_model=dict)
async def get_actor_graph_endpoint(
    actor_id: str,
    hops: int = 2,
    current_user: CurrentUser = Depends(require_permission("actors:read")),
):
    """Get actor network graph for visualization."""
    actor_graph = await get_actor_graph()
    graph = await actor_graph.get_actor_network_graph(actor_id, max_hops=hops)

    if not graph["nodes"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found in graph")

    return graph
