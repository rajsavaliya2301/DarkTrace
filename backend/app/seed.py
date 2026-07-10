"""Seed script — creates default alert rules, watchlists, and admin data.

Run on first startup to populate the database with initial configuration.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.database import get_mongodb

logger = logging.getLogger(__name__)


DEFAULT_ALERT_RULES = [
    {
        "name": "Critical Threat Detection",
        "description": "Triggers on content classified as critical-severity threats (terrorism, weapons, trafficking)",
        "enabled": True,
        "severity_threshold": 700,
        "conditions": [
            {
                "field": "classification.primary",
                "operator": "in",
                "value": ["terrorism", "weapons_trafficking", "human_trafficking", "narcotics"],
            },
            {
                "field": "score",
                "operator": "gt",
                "value": 600,
            },
        ],
        "notifications": [],
        "cooldown_minutes": 1440,  # 24 hours
    },
    {
        "name": "Data Breach / Leak Alert",
        "description": "Triggers on content involving data breaches, leaked databases, or credential dumps",
        "enabled": True,
        "severity_threshold": 500,
        "conditions": [
            {
                "field": "classification.primary",
                "operator": "in",
                "value": ["data_breach", "cyber_espionage", "financial_fraud"],
            },
        ],
        "notifications": [],
        "cooldown_minutes": 1440,
    },
    {
        "name": "Indian PII Detection",
        "description": "Triggers when Indian PII (Aadhaar, PAN, Voter ID) is detected in content",
        "enabled": True,
        "severity_threshold": 400,
        "conditions": [
            {
                "field": "entities.aadhaar",
                "operator": "gt",
                "value": 0,
            },
        ],
        "notifications": [],
        "cooldown_minutes": 2880,  # 48 hours
    },
    {
        "name": "High-Value Target Mention",
        "description": "Triggers when high-value entity types are mentioned (BTC addresses, credentials)",
        "enabled": True,
        "severity_threshold": 300,
        "conditions": [
            {
                "field": "entities.btc_addresses",
                "operator": "gt",
                "value": 0,
            },
        ],
        "notifications": [],
        "cooldown_minutes": 1440,
    },
    {
        "name": "Watchlist Keyword Match",
        "description": "Triggers when any watchlist keyword is matched in content with moderate score",
        "enabled": True,
        "severity_threshold": 200,
        "conditions": [
            {
                "field": "keyword_matches.matched_keywords",
                "operator": "gt",
                "value": 0,
            },
        ],
        "notifications": [],
        "cooldown_minutes": 1440,
    },
    {
        "name": "High Severity Content",
        "description": "Catches any content scoring above 500 regardless of classification",
        "enabled": True,
        "severity_threshold": 500,
        "conditions": [],
        "notifications": [],
        "cooldown_minutes": 720,  # 12 hours
    },
]

DEFAULT_WATCHLISTS = [
    {
        "name": "Indian Financial Fraud",
        "description": "Keywords related to Indian banking fraud, UPI scams, and financial cybercrime",
        "keywords": [
            "aadhaar", "pan card", "upi", "gpay", "phonepe", "paytm",
            "bank fraud", "credit card dump", "cvv", "dumps",
            "hdfc", "icici", "sbi", "axis bank", "kotak",
            "net banking", "otp bypass", "carding", "fullz",
            "income tax", "itr filing", "gst fraud",
        ],
        "regex_patterns": [],
        "severity_boost": 200,
        "is_active": True,
    },
    {
        "name": "Cyber Terrorism & Extremism",
        "description": "Keywords related to terrorism, extremism, and radicalization",
        "keywords": [
            "isis", "jihad", "mujahideen", "terrorist", "terrorism",
            "bomb making", "ied", "explosive", "suicide attack",
            "lone wolf", "radicalization", "recruitment",
            "al-qaeda", "taliban", "islamic state",
        ],
        "regex_patterns": [],
        "severity_boost": 300,
        "is_active": True,
    },
    {
        "name": "Drug Trafficking",
        "description": "Keywords for narcotics and illegal substance trafficking",
        "keywords": [
            "cocaine", "heroin", "fentanyl", "meth", "methamphetamine",
            "mdma", "ecstasy", "opium", "morphine",
            "dark web market", "silk road", "alphabay",
            "drug trafficking", "narcotics", "cannabis oil",
            "lsd", "ketamine", "xanax", "oxycodone",
        ],
        "regex_patterns": [],
        "severity_boost": 250,
        "is_active": True,
    },
    {
        "name": "Weapons & Arms Trafficking",
        "description": "Keywords for illegal weapons trade and trafficking",
        "keywords": [
            "ak-47", "rifle", "pistol", "machine gun", "assault rifle",
            "ammunition", "grenade", "explosive", "firearm",
            "gun running", "arms dealer", "weapons trafficking",
            "3d printed gun", "ghost gun", "silencer",
            "military grade", "armor piercing",
        ],
        "regex_patterns": [],
        "severity_boost": 300,
        "is_active": True,
    },
    {
        "name": "Human Trafficking",
        "description": "Keywords for human trafficking, forced labor, and modern slavery",
        "keywords": [
            "human trafficking", "sex trafficking", "forced labor",
            "modern slavery", "child exploitation", "trafficking victim",
            "smuggling", "illegal immigration", "passport forgery",
            "bride trafficking", "organ harvesting",
        ],
        "regex_patterns": [],
        "severity_boost": 350,
        "is_active": True,
    },
    {
        "name": "Data Breach & Cybercrime",
        "description": "Keywords for data breaches, hacking, and cybercriminal activity",
        "keywords": [
            "data breach", "database dump", "leaked", "breach",
            "credential dump", "hacked", "exploit", "0day",
            "ransomware", "lockbit", "blackcat", "alphv",
            "phishing kit", "malware", "trojan", "rat",
            "ddos", "botnet", "c2 server", "command and control",
        ],
        "regex_patterns": [],
        "severity_boost": 200,
        "is_active": True,
    },
]


async def seed_database():
    """Seed the database with default data if collections are empty."""
    db = await get_mongodb()
    now = datetime.now(tz=timezone.utc)

    # ── Seed Alert Rules ────────────────────────────────────────────────────
    existing_rules = await db.alert_rules.count_documents({})
    if existing_rules == 0:
        logger.info("Seeding %d default alert rules...", len(DEFAULT_ALERT_RULES))
        for rule in DEFAULT_ALERT_RULES:
            rule["_id"] = str(uuid.uuid4())
            rule["match_count"] = 0
            rule["last_triggered_at"] = None
            rule["created_by"] = "system"
            rule["created_at"] = now
            rule["updated_at"] = now
            await db.alert_rules.insert_one(rule)
        logger.info("Alert rules seeded successfully")
    else:
        logger.info("Alert rules collection already has %d rules, skipping seed", existing_rules)

    # ── Seed Watchlists ─────────────────────────────────────────────────────
    existing_watchlists = await db.watchlists.count_documents({})
    if existing_watchlists == 0:
        logger.info("Seeding %d default watchlists...", len(DEFAULT_WATCHLISTS))
        for wl in DEFAULT_WATCHLISTS:
            wl["_id"] = str(uuid.uuid4())
            wl["match_count"] = 0
            wl["entities"] = []
            wl["created_by"] = "system"
            wl["created_at"] = now
            wl["updated_at"] = now
            await db.watchlists.insert_one(wl)
        logger.info("Watchlists seeded successfully")
    else:
        logger.info("Watchlists collection already has %d entries, skipping seed", existing_watchlists)

    # ── Elasticsearch Index Setup ───────────────────────────────────────────
    try:
        from app.database import get_elasticsearch
        es = await get_elasticsearch()

        # Define indices with explicit mappings for crawled_content
        INDEX_MAPPINGS = {
            "crawled_content": {
                "mappings": {
                    "properties": {
                        "document_type": {"type": "keyword"},
                        "source_type": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "site_name": {"type": "keyword"},
                        "scoring.severity": {"type": "keyword"},
                        "url": {"type": "text"},
                        "title": {"type": "text"},
                        "content_text": {"type": "text"},
                        "author": {"type": "text"},
                        "crawl_timestamp": {"type": "date"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "entities": {"type": "object", "enabled": False},
                        "analysis": {"type": "object", "enabled": False},
                        "scoring": {
                            "type": "object",
                            "enabled": True,
                            "properties": {
                                "score": {"type": "float"},
                                "severity": {"type": "keyword"},
                            }
                        },
                    }
                }
            },
            "alerts": {},
            "actors": {},
        }

        from elasticsearch import BadRequestError

        for index, mapping in INDEX_MAPPINGS.items():
            exists = await es.indices.exists(index=index)
            if not exists:
                try:
                    if mapping:
                        await es.indices.create(index=index, **mapping)
                    else:
                        await es.indices.create(index=index)
                    logger.info("Created Elasticsearch index: %s", index)
                except BadRequestError as e:
                    if "already_exists" in str(e).lower():
                        logger.info("ES index %s already exists (race with another worker)", index)
                    else:
                        logger.warning("ES index creation failed for %s: %s", index, e)
            elif mapping and mapping.get("mappings"):
                # Update mapping for existing index (e.g. when we add new fields)
                try:
                    current = await es.indices.get_mapping(index=index)
                    current_props = current.get(index, {}).get("mappings", {}).get("properties", {})
                    needs_recreate = False
                    needs_update = False
                    for key, val in mapping["mappings"]["properties"].items():
                        existing = current_props.get(key)
                        if existing != val:
                            # If the change requires recreation (e.g. enabled flag changed), flag it
                            if existing and isinstance(existing, dict) and isinstance(val, dict):
                                if existing.get("enabled") != val.get("enabled"):
                                    needs_recreate = True
                            needs_update = True
                    if needs_recreate:
                        await es.indices.delete(index=index)
                        await es.indices.create(index=index, **mapping)
                        logger.info("Recreated ES index: %s (mapping conflict)", index)
                    elif needs_update:
                        await es.indices.put_mapping(index=index, **mapping["mappings"])
                        logger.info("Updated mapping for ES index: %s", index)
                    else:
                        logger.debug("ES index %s mapping is up-to-date", index)
                except Exception as map_err:
                    logger.warning("Could not update mapping for %s: %s", index, map_err)
    except Exception as e:
        logger.warning("ES index setup failed: %s", e)

    logger.info("Database seeding complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_database())
