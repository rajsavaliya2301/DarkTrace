"""Actor profiling engine — builds profiles from pseudonyms, writing style, entities."""

import hashlib
import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.actors.graph import get_actor_graph
from app.database import get_mongodb

logger = logging.getLogger(__name__)


class ActorProfiler:
    """Profiles threat actors from parsed content — stylometry, cross-platform linking."""

    async def process_content(self, content_id: str, author: str, content_text: str,
                                entities: Dict, site_name: str, source_type: str,
                                url: str = "", title: str = "") -> Optional[str]:
        """Process content to update or create actor profile. Returns actor UUID."""
        if not author or not author.strip():
            return None

        author = author.strip()
        db = await get_mongodb()

        # Try to find existing actor via pseudonym in Neo4j
        actor_graph = await get_actor_graph()
        profile = await actor_graph.search_actors(search_term=author)

        existing_actor_id = None
        if profile and profile.get("data"):
            # Found existing actor
            existing_actor_id = profile["data"][0]["id"]
            logger.debug("Found existing actor %s for pseudonym %s", existing_actor_id, author)
        else:
            # Check if we have a MongoDB record for this pseudonym
            existing_profile = await db.actor_profiles.find_one({"pseudonyms": author})
            if existing_profile:
                existing_actor_id = str(existing_profile["_id"])
            else:
                # Create new actor
                existing_actor_id = str(uuid_lib.uuid4())
                initial_profile = {
                    "_id": existing_actor_id,
                    "pseudonyms": [author],
                    "risk_score": 0,
                    "first_seen": datetime.now(timezone.utc),
                    "last_seen": datetime.now(timezone.utc),
                    "total_posts": 1,
                    "active_platforms": [site_name] if site_name else [],
                    "linked_entities": {
                        "btc_addresses": entities.get("btc_addresses", []),
                        "emails": entities.get("emails", []),
                        "pgp_keys": [],
                    },
                    "top_categories": [],
                    "bio_summary": "",
                    "activity_timeline": [],
                    "recent_activity": [],
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
                await db.actor_profiles.insert_one(initial_profile)
                logger.info("Created new actor profile %s for %s", existing_actor_id, author)

        # Update Neo4j
        await actor_graph.create_or_update_actor({
            "uuid": existing_actor_id,
            "risk_score": 0,
        })
        await actor_graph.link_pseudonym(existing_actor_id, author, site_name)

        # Link entities
        for btc in entities.get("btc_addresses", []):
            await actor_graph.link_entity(author, "btc_address", btc)
        for email in entities.get("emails", []):
            await actor_graph.link_entity(author, "email", email)

        # Link content
        await actor_graph.link_content(existing_actor_id, content_id, site_name, url)

        # Link to site
        if site_name:
            await actor_graph.link_actor_to_site(existing_actor_id, site_name, source_type)

        # Update MongoDB profile
        await db.actor_profiles.update_one(
            {"_id": existing_actor_id},
            {
                "$set": {
                    "last_seen": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
                "$addToSet": {
                    "pseudonyms": author,
                    "active_platforms": site_name if site_name else "",
                },
                "$inc": {"total_posts": 1},
                "$push": {
                    "recent_activity": {
                        "$each": [{
                            "content_id": content_id,
                            "title": title,
                            "category": "",
                            "url": url,
                            "site_name": site_name,
                            "crawled_at": datetime.now(timezone.utc).isoformat(),
                        }],
                        "$position": 0,
                        "$slice": 50,
                    }
                },
            },
        )

        # Index in Elasticsearch
        try:
            from app.database import get_elasticsearch
            es = await get_elasticsearch()
            # Build pseudonyms list
            profile_data = await db.actor_profiles.find_one({"_id": existing_actor_id})
            if profile_data:
                await es.index(
                    index="actors",
                    id=existing_actor_id,
                    body={
                        "id": existing_actor_id,
                        "pseudonyms": profile_data.get("pseudonyms", []),
                        "risk_score": profile_data.get("risk_score", 0),
                        "first_seen": profile_data.get("first_seen", datetime.now(timezone.utc)).isoformat(),
                        "last_seen": profile_data.get("last_seen", datetime.now(timezone.utc)).isoformat(),
                        "total_posts": profile_data.get("total_posts", 0),
                        "active_platforms": profile_data.get("active_platforms", []),
                        "top_categories": profile_data.get("top_categories", []),
                    },
                    refresh="wait_for",
                )
        except Exception as e:
            logger.warning("ES indexing failed for actor %s: %s", existing_actor_id, e)

        return existing_actor_id


# Singleton
_actor_profiler: Optional[ActorProfiler] = None


async def get_actor_profiler() -> ActorProfiler:
    """Get or create the singleton actor profiler."""
    global _actor_profiler
    if _actor_profiler is None:
        _actor_profiler = ActorProfiler()
    return _actor_profiler
