"""Neo4j graph operations for actor relationships and entity linkage."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from neo4j import AsyncDriver

from app.database import get_neo4j

logger = logging.getLogger(__name__)


class ActorGraph:
    """Manages actor graph operations in Neo4j."""

    async def ensure_constraints(self):
        """Ensure required Neo4j constraints exist."""
        driver = await get_neo4j()
        async with driver.session(database="neo4j") as session:
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Actor) REQUIRE a.uuid IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Pseudonym) REQUIRE p.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.value IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR (a:Actor) ON (a.uuid)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Pseudonym) ON (p.name)",
                "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.value)",
            ]
            for cypher in constraints:
                try:
                    await session.run(cypher)
                except Exception as e:
                    logger.warning("Neo4j constraint/index creation warning: %s", e)

    async def create_or_update_actor(self, actor_data: dict) -> str:
        """Create or update an actor node. Returns actor UUID."""
        driver = await get_neo4j()
        uuid = actor_data.get("uuid", "")
        risk_score = actor_data.get("risk_score", 0)
        now = datetime.now(timezone.utc).isoformat()

        async with driver.session(database="neo4j") as session:
            result = await session.run(
                """
                MERGE (a:Actor {uuid: $uuid})
                ON CREATE SET
                    a.risk_score = $risk_score,
                    a.first_seen = $now,
                    a.last_seen = $now,
                    a.total_posts = 1,
                    a.notes = ''
                ON MATCH SET
                    a.risk_score = $risk_score,
                    a.last_seen = $now,
                    a.total_posts = COALESCE(a.total_posts, 0) + 1
                RETURN a.uuid
                """,
                uuid=uuid,
                risk_score=risk_score,
                now=now,
            )
            record = await result.single()
            return record["a.uuid"] if record else uuid

    async def link_pseudonym(self, actor_uuid: str, pseudonym: str, platform: str = "", confidence: float = 1.0):
        """Link a pseudonym to an actor."""
        driver = await get_neo4j()
        now = datetime.now(timezone.utc).isoformat()

        async with driver.session(database="neo4j") as session:
            await session.run(
                """
                MERGE (p:Pseudonym {name: $pseudonym})
                ON CREATE SET
                    p.first_seen = $now,
                    p.last_seen = $now,
                    p.platforms = [$platform],
                    p.post_count = 1
                ON MATCH SET
                    p.last_seen = $now,
                    p.platforms = CASE WHEN NOT $platform IN p.platforms
                        THEN p.platforms + $platform
                        ELSE p.platforms END,
                    p.post_count = COALESCE(p.post_count, 0) + 1
                WITH p
                MATCH (a:Actor {uuid: $actor_uuid})
                MERGE (a)-[r:USES]->(p)
                ON CREATE SET
                    r.first_seen = $now,
                    r.confidence = $confidence,
                    r.method = 'explicit'
                ON MATCH SET
                    r.confidence = $confidence,
                    r.method = 'explicit'
                """,
                actor_uuid=actor_uuid,
                pseudonym=pseudonym,
                platform=platform,
                now=now,
                confidence=confidence,
            )

    async def link_entity(self, pseudonym: str, entity_type: str, entity_value: str, confidence: float = 0.9):
        """Link a cryptocurrency address or other entity to a pseudonym."""
        driver = await get_neo4j()
        now = datetime.now(timezone.utc).isoformat()

        async with driver.session(database="neo4j") as session:
            await session.run(
                """
                MERGE (e:Entity {value: $value})
                ON CREATE SET
                    e.type = $entity_type,
                    e.first_seen = $now,
                    e.last_seen = $now,
                    e.total_mentions = 1
                ON MATCH SET
                    e.type = $entity_type,
                    e.last_seen = $now,
                    e.total_mentions = COALESCE(e.total_mentions, 0) + 1
                WITH e
                MATCH (p:Pseudonym {name: $pseudonym})
                MERGE (p)-[r:CONTROLS]->(e)
                ON CREATE SET
                    r.first_seen = $now,
                    r.confidence = $confidence
                ON MATCH SET
                    r.confidence = $confidence
                """,
                pseudonym=pseudonym,
                entity_type=entity_type,
                value=entity_value,
                now=now,
                confidence=confidence,
            )

    async def link_content(self, actor_uuid: str, content_id: str, site: str = "", url: str = ""):
        """Link content to an actor."""
        driver = await get_neo4j()
        now = datetime.now(timezone.utc).isoformat()

        async with driver.session(database="neo4j") as session:
            await session.run(
                """
                MERGE (c:Content {uuid: $content_id})
                ON CREATE SET
                    c.last_seen = $now,
                    c.url = $url
                ON MATCH SET
                    c.last_seen = $now,
                    c.url = $url
                WITH c
                MATCH (a:Actor {uuid: $actor_uuid})
                MERGE (a)-[r:POSTED]->(c)
                ON CREATE SET
                    r.posted_at = $now,
                    r.site = $site,
                    r.platform = ''
                ON MATCH SET
                    r.site = $site,
                    r.platform = ''
                """,
                actor_uuid=actor_uuid,
                content_id=content_id,
                site=site,
                url=url,
                now=now,
            )

    async def link_actor_to_site(self, actor_uuid: str, site_domain: str, site_type: str = "onion"):
        """Link an actor to a site they are active on."""
        driver = await get_neo4j()
        now = datetime.now(timezone.utc).isoformat()

        async with driver.session(database="neo4j") as session:
            await session.run(
                """
                MERGE (s:Site {domain: $domain})
                ON CREATE SET
                    s.type = $site_type,
                    s.site_name = $domain,
                    s.status = 'active',
                    s.reputation_score = 50.0,
                    s.first_discovered = $now,
                    s.last_crawled = $now
                ON MATCH SET
                    s.type = $site_type,
                    s.last_crawled = $now
                WITH s
                MATCH (a:Actor {uuid: $actor_uuid})
                MERGE (a)-[r:ACTIVE_ON]->(s)
                ON CREATE SET
                    r.first_seen = $now,
                    r.last_seen = $now,
                    r.total_posts = 1
                ON MATCH SET
                    r.last_seen = $now,
                    r.total_posts = COALESCE(r.total_posts, 0) + 1
                """,
                actor_uuid=actor_uuid,
                domain=site_domain,
                site_type=site_type,
                now=now,
            )

    async def get_actor_profile(self, actor_uuid: str) -> Optional[Dict]:
        """Get full actor profile with pseudonyms, entities, and relationships."""
        driver = await get_neo4j()

        async with driver.session(database="neo4j") as session:
            # Get actor node
            result = await session.run(
                "MATCH (a:Actor {uuid: $uuid}) RETURN a",
                uuid=actor_uuid,
            )
            record = await result.single()
            if not record:
                return None
            actor_node = record["a"]

            # Get pseudonyms
            result = await session.run(
                """
                MATCH (a:Actor {uuid: $uuid})-[r:USES]->(p:Pseudonym)
                RETURN p.name as name, p.platforms as platforms,
                       p.first_seen as first_seen, p.last_seen as last_seen
                """,
                uuid=actor_uuid,
            )
            pseudonyms = []
            async for record in result:
                pseudonyms.append({
                    "name": record.get("name"),
                    "platforms": record.get("platforms", []),
                    "first_seen": str(record.get("first_seen", "")),
                    "last_seen": str(record.get("last_seen", "")),
                })

            # Get entities
            result = await session.run(
                """
                MATCH (a:Actor {uuid: $uuid})-[:USES]->(p:Pseudonym)-[:CONTROLS]->(e:Entity)
                RETURN e.value as value, e.type as type, e.first_seen as first_seen
                """,
                uuid=actor_uuid,
            )
            entities = {"btc_addresses": [], "emails": [], "pgp_keys": []}
            async for record in result:
                etype = record.get("type", "")
                evalue = record.get("value", "")
                if "btc" in etype:
                    entities["btc_addresses"].append(evalue)
                elif "email" in etype:
                    entities["emails"].append(evalue)
                elif "pgp" in etype:
                    entities["pgp_keys"].append(evalue)
                else:
                    entities.setdefault("other", []).append(evalue)

            # Get network graph (1-hop)
            result = await session.run(
                """
                MATCH path = (a:Actor {uuid: $uuid})-[r:TRANSACTED_WITH*1..1]-(connected:Actor)
                RETURN connected.uuid as id, connected.risk_score as risk_score
                """,
                uuid=actor_uuid,
            )
            connected_actors = []
            async for record in result:
                connected_actors.append({
                    "id": record.get("id"),
                    "risk_score": record.get("risk_score", 0),
                })

            return {
                "id": actor_uuid,
                "risk_score": actor_node.get("risk_score", 0),
                "total_posts": actor_node.get("total_posts", 0),
                "first_seen": str(actor_node.get("first_seen", "")),
                "last_seen": str(actor_node.get("last_seen", "")),
                "pseudonyms": pseudonyms,
                "linked_entities": entities,
                "connected_actors": connected_actors,
            }

    async def get_actor_network_graph(self, actor_uuid: str, max_hops: int = 2) -> Dict:
        """Get the network graph for visualization."""
        driver = await get_neo4j()

        async with driver.session(database="neo4j") as session:
            result = await session.run(
                f"""
                MATCH path = (a:Actor {{uuid: $uuid}})-[*1..{max_hops}]-(connected)
                UNWIND nodes(path) as n
                RETURN DISTINCT n
                """,
                uuid=actor_uuid,
            )
            nodes_map = {}
            async for record in result:
                node = record["n"]
                labels = list(node.labels)
                node_id = node.get("uuid") or node.get("name") or node.get("domain")
                if node_id:
                    label = node.get("name") or node.get("domain") or str(node_id)
                    nodes_map[str(node_id)] = {
                        "id": str(node_id),
                        "label": str(label)[:50],
                        "type": labels[0] if labels else "unknown",
                        "risk_score": node.get("risk_score", 0),
                    }

            # Get relationships
            result = await session.run(
                f"""
                MATCH path = (a:Actor {{uuid: $uuid}})-[r:*1..{max_hops}]-(connected)
                UNWIND relationships(path) as rel
                RETURN DISTINCT rel
                """,
                uuid=actor_uuid,
            )
            edges = []
            seen_edges = set()
            async for record in result:
                rel = record["rel"]
                start_id = str(rel.start_node.get("uuid") or rel.start_node.get("name") or rel.start_node.get("domain", ""))
                end_id = str(rel.end_node.get("uuid") or rel.end_node.get("name") or rel.end_node.get("domain", ""))
                edge_key = f"{start_id}-{end_id}-{rel.type}"
                if edge_key not in seen_edges and start_id and end_id:
                    seen_edges.add(edge_key)
                    edges.append({
                        "source": start_id,
                        "target": end_id,
                        "label": rel.type,
                        "count": rel.get("count", 1),
                    })

            return {
                "nodes": list(nodes_map.values()),
                "edges": edges,
            }

    async def search_actors(self, search_term: str = "", risk_min: int = 0, page: int = 1, per_page: int = 25) -> Dict:
        """Search actors by pseudonym or properties."""
        driver = await get_neo4j()

        async with driver.session(database="neo4j") as session:
            if search_term:
                result = await session.run(
                    """
                    MATCH (a:Actor)-[:USES]->(p:Pseudonym)
                    WHERE p.name CONTAINS $search_term OR a.uuid CONTAINS $search_term
                    RETURN DISTINCT a.uuid as id, a.risk_score as risk_score,
                           a.total_posts as total_posts, a.first_seen as first_seen,
                           a.last_seen as last_seen,
                           COLLECT(DISTINCT p.name) as pseudonyms
                    ORDER BY a.risk_score DESC
                    SKIP $skip LIMIT $limit
                    """,
                    search_term=search_term,
                    skip=(page - 1) * per_page,
                    limit=per_page,
                )
            else:
                result = await session.run(
                    """
                    MATCH (a:Actor)
                    WHERE a.risk_score >= $risk_min
                    RETURN a.uuid as id, a.risk_score as risk_score,
                           a.total_posts as total_posts, a.first_seen as first_seen,
                           a.last_seen as last_seen,
                           [] as pseudonyms
                    ORDER BY a.risk_score DESC
                    SKIP $skip LIMIT $limit
                    """,
                    risk_min=risk_min,
                    skip=(page - 1) * per_page,
                    limit=per_page,
                )

            actors = []
            async for record in result:
                actors.append({
                    "id": record.get("id"),
                    "risk_score": record.get("risk_score", 0),
                    "total_posts": record.get("total_posts", 0),
                    "first_seen": str(record.get("first_seen", "")),
                    "last_seen": str(record.get("last_seen", "")),
                    "pseudonyms": record.get("pseudonyms", []),
                })

            # Count total
            if search_term:
                count_result = await session.run(
                    """
                    MATCH (a:Actor)-[:USES]->(p:Pseudonym)
                    WHERE p.name CONTAINS $search_term OR a.uuid CONTAINS $search_term
                    RETURN COUNT(DISTINCT a) as total
                    """,
                    search_term=search_term,
                )
            else:
                count_result = await session.run(
                    "MATCH (a:Actor) WHERE a.risk_score >= $risk_min RETURN COUNT(a) as total",
                    risk_min=risk_min,
                )
            count_record = await count_result.single()
            total = count_record["total"] if count_record else 0

            return {
                "data": actors,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": max(1, (total + per_page - 1) // per_page),
                },
            }


# Singleton
_actor_graph: Optional[ActorGraph] = None


async def get_actor_graph() -> ActorGraph:
    """Get or create the singleton actor graph."""
    global _actor_graph
    if _actor_graph is None:
        _actor_graph = ActorGraph()
        await _actor_graph.ensure_constraints()
    return _actor_graph
