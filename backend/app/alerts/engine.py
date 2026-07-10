"""Alert matching and dispatch engine."""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.alerts.models import new_alert_document
from app.config import get_settings
from app.database import get_mongodb, get_elasticsearch, get_redis

logger = logging.getLogger(__name__)


class AlertEngine:
    """Matches scored content against alert rules and dispatches notifications."""

    async def process_scored_content(self, scoring_result: Dict, analysis: Dict, content_meta: Dict) -> Optional[Dict]:
        """Process a scored content result — match against rules and create alerts."""
        db = await get_mongodb()

        # Get all enabled alert rules
        rules = await db.alert_rules.find({"enabled": True}).to_list(length=None)
        if not rules:
            logger.debug("No enabled alert rules found")
            return None

        score = scoring_result.get("score", 0)
        severity = scoring_result.get("severity", "informational")
        content_id = scoring_result.get("content_id", "")

        best_alert = None

        for rule in rules:
            matched = await self._evaluate_rule(rule, scoring_result, analysis, content_meta)
            if matched:
                # Check deduplication
                dedup_key = hashlib.sha256(
                    f"{content_id}:{rule['_id']}".encode()
                ).hexdigest()
                if await self._is_deduplicated(dedup_key, rule):
                    logger.debug("Skipping deduplicated alert for rule %s", rule.get("name"))
                    continue

                # Create alert
                alert = await self._create_alert(rule, scoring_result, analysis, content_meta, dedup_key)

                if best_alert is None or self._alert_priority(alert) > self._alert_priority(best_alert):
                    best_alert = alert

        return best_alert

    async def _evaluate_rule(self, rule: dict, scoring_result: Dict, analysis: Dict, content_meta: Dict) -> bool:
        """Evaluate whether a rule should trigger on this content."""
        # Check severity threshold first
        score = scoring_result.get("score", 0)
        threshold = rule.get("severity_threshold", 0)
        if score < threshold:
            return False

        conditions = rule.get("conditions", [])
        if not conditions:
            # No conditions = catch-all rule (just threshold check)
            return True

        for condition in conditions:
            field = condition.get("field", "")
            operator = condition.get("operator", "")
            value = condition.get("value")

            actual_value = self._resolve_field(field, scoring_result, analysis, content_meta)
            if not self._apply_operator(actual_value, operator, value):
                return False

        return True

    def _resolve_field(self, field: str, scoring_result: Dict, analysis: Dict, content_meta: Dict) -> any:
        """Resolve a dot-notation field path from the available data."""
        # Search in scoring_result, analysis, content_meta
        data_sources = [scoring_result, analysis, content_meta]

        parts = field.split(".")
        for source in data_sources:
            current = source
            try:
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part)
                    else:
                        current = None
                        break
                if current is not None:
                    return current
            except (KeyError, TypeError, AttributeError):
                continue
        return None

    def _apply_operator(self, actual: any, operator: str, expected: any) -> bool:
        """Apply a comparison operator."""
        try:
            if operator == "in":
                return actual in expected if isinstance(expected, list) else actual == expected
            elif operator == "contains_any":
                if isinstance(actual, list) and isinstance(expected, list):
                    return any(item in actual for item in expected)
                if isinstance(actual, str) and isinstance(expected, list):
                    return any(e.lower() in actual.lower() for e in expected)
                return False
            elif operator == "gt":
                return float(actual) > float(expected)
            elif operator == "lt":
                return float(actual) < float(expected)
            elif operator == "eq":
                return actual == expected
            elif operator == "ne":
                return actual != expected
            elif operator == "regex":
                import re
                return bool(re.search(str(expected), str(actual)))
            return False
        except (ValueError, TypeError):
            return False

    async def _is_deduplicated(self, dedup_key: str, rule: dict) -> bool:
        """Check if this alert was already triggered within the cooldown window."""
        try:
            redis = await get_redis()
            cooldown = rule.get("cooldown_minutes", 1440)
            key = f"dedup:alert:{dedup_key}"
            exists = await redis.get(key)
            if exists:
                return True
            await redis.setex(key, cooldown * 60, "1")
            return False
        except Exception:
            return False

    async def _create_alert(self, rule: dict, scoring_result: Dict, analysis: Dict, content_meta: Dict, dedup_key: str) -> Dict:
        """Create an alert document and index it."""
        db = await get_mongodb()

        classification = analysis.get("classification", {})
        entities = analysis.get("entities", {})
        keyword_matches = analysis.get("keyword_matches", {})

        rule_name = rule.get("name", "Alert")
        score = scoring_result.get("score", 0)
        severity = scoring_result.get("severity", "medium")
        primary_class = classification.get("primary", "unknown")
        source_url = content_meta.get("url", "")
        source_type = content_meta.get("source_type", "onion")

        # Build alert title
        title = f"{rule_name}: {primary_class.replace('_', ' ').title()}"
        if source_url:
            site = content_meta.get("site_name", "")
            if site:
                title += f" on {site}"

        # Build summary
        matched_kws = keyword_matches.get("matched_keywords", [])
        summary_parts = [f"Score: {score} ({severity})"]
        if matched_kws:
            summary_parts.append(f"Matched: {', '.join(matched_kws[:5])}")
        breakdown = scoring_result.get("breakdown", "")
        if breakdown:
            summary_parts.append(breakdown)
        summary = " | ".join(summary_parts)

        # Timeline
        now = datetime.now(timezone.utc)

        alert_doc = {
            "_id": str(hashlib.sha256(f"{content_meta.get('content_id', '')}:{rule['_id']}:{time.time()}".encode()).hexdigest()[:36]),
            "title": title[:256],
            "severity": severity,
            "score": score,
            "score_breakdown": scoring_result.get("factors", {}),
            "status": "new",
            "category": primary_class,
            "source_type": source_type,
            "source_url": source_url,
            "source_site": content_meta.get("site_name", ""),
            "content_id": content_meta.get("content_id", ""),
            "summary": summary[:500],
            "matched_keywords": matched_kws,
            "actor_pseudonym": content_meta.get("author"),
            "actor_profile_id": None,
            "assignee": None,
            "acknowledged_by": None,
            "comments": [],
            "entities": entities,
            "analysis": analysis,
            "timeline": [
                {"event": "alert_created", "timestamp": now.isoformat(), "detail": title},
            ],
            "related_alerts": [],
            "dedup_key": dedup_key,
            "rule_id": str(rule["_id"]),
            "rule_name": rule_name,
            "created_at": now,
            "updated_at": now,
        }

        await db.alerts.insert_one(alert_doc)

        # Index in Elasticsearch
        try:
            es = await get_elasticsearch()
            await es.index(
                index="alerts",
                id=alert_doc["_id"],
                body={
                    "id": alert_doc["_id"],
                    "title": title,
                    "severity": severity,
                    "score": score,
                    "status": "new",
                    "category": primary_class,
                    "source_type": source_type,
                    "source_url": source_url,
                    "source_site": content_meta.get("site_name", ""),
                    "summary": summary[:500],
                    "matched_keywords": matched_kws,
                    "actor_pseudonym": content_meta.get("author"),
                    "actor_id": None,
                    "assignee": None,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                },
                refresh="wait_for",
            )
        except Exception as e:
            logger.warning("ES indexing failed for alert %s: %s", alert_doc["_id"], e)

        # Update rule match count
        await db.alert_rules.update_one(
            {"_id": rule["_id"]},
            {
                "$inc": {"match_count": 1},
                "$set": {"last_triggered_at": now},
            },
        )

        # Store dedup in MongoDB as well
        await db.dedup_cache.insert_one({
            "_id": dedup_key,
            "alert_id": alert_doc["_id"],
            "rule_id": str(rule["_id"]),
            "content_id": content_meta.get("content_id", ""),
            "triggered_at": now,
            "expires_at": datetime.now(timezone.utc),
        })

        logger.info(
            "Alert created: %s (severity=%s, score=%d, rule=%s)",
            alert_doc["_id"], severity, score, rule_name,
        )

        return alert_doc

    def _alert_priority(self, alert: dict) -> int:
        """Get numeric priority for alert comparison."""
        severity_map = {"critical": 5, "high": 4, "medium": 3, "low": 2, "informational": 1}
        return severity_map.get(alert.get("severity"), 0)


# Singleton
_alert_engine: Optional[AlertEngine] = None


async def get_alert_engine() -> AlertEngine:
    """Get or create the singleton alert engine."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine
