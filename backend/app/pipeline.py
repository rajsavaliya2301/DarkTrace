"""Content processing pipeline — orchestrates crawler → NLP → actors → scoring → alerts.

After the crawl engine stores raw content, this pipeline runs asynchronously:
  1. NLP analysis (entities, classification, sentiment, keywords)
  2. Actor profiling (create/link actor profiles)
  3. Threat scoring (0-1000 severity)
  4. Alert evaluation (match against rules, create alerts)
  5. Real-time notification broadcast (WebSocket/SSE)
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional

from app.config import get_settings
from app.database import get_mongodb

logger = logging.getLogger(__name__)

# In-memory broadcast channels for real-time updates
_new_content_subscribers: list = []
_new_actor_subscribers: list = []
_new_alert_subscribers: list = []


# ─── Pub/Sub for Real-Time Updates ─────────────────────────────────────────

class EventBroadcaster:
    """Simple in-memory pub/sub for broadcasting real-time events to WebSocket clients."""

    def __init__(self):
        self._subscribers: Dict[str, list] = {
            "content": [],
            "actor": [],
            "alert": [],
            "dashboard": [],
        }

    def subscribe(self, channel: str, queue: asyncio.Queue):
        """Subscribe a queue to a channel."""
        if channel in self._subscribers:
            self._subscribers[channel].append(queue)

    def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """Unsubscribe a queue from a channel."""
        if channel in self._subscribers:
            self._subscribers[channel] = [q for q in self._subscribers[channel] if q is not queue]

    async def broadcast(self, channel: str, event: dict):
        """Broadcast an event to all subscribers of a channel."""
        if channel not in self._subscribers:
            return
        dead_queues = []
        for queue in self._subscribers[channel]:
            try:
                await queue.put(event)
            except asyncio.QueueFull:
                dead_queues.append(queue)
            except Exception:
                dead_queues.append(queue)
        # Remove dead queues
        for q in dead_queues:
            self._subscribers[channel] = [sub for sub in self._subscribers[channel] if sub is not q]

    @property
    def subscriber_count(self) -> Dict[str, int]:
        return {ch: len(qs) for ch, qs in self._subscribers.items()}


# Singleton
_broadcaster: Optional[EventBroadcaster] = None


def get_broadcaster() -> EventBroadcaster:
    """Get or create the singleton event broadcaster."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = EventBroadcaster()
    return _broadcaster


# ─── Processing Pipeline ────────────────────────────────────────────────────


async def process_crawled_content(content_id: str, content_doc: dict) -> Dict:
    """Run the full processing pipeline on crawled content.

    Stages:
      1. NLP analysis (if not already analyzed)
      2. Actor profiling
      3. Threat scoring
      4. Alert evaluation
      5. Broadcast real-time update
    """
    start_time = time.time()
    logger.info("Pipeline: Starting processing for content %s", content_id)
    db = await get_mongodb()

    text_content = content_doc.get("text_content", "")
    title = content_doc.get("title", "")
    url = content_doc.get("url", "")
    site_name = content_doc.get("site_name", "unknown")
    source_type = content_doc.get("source_type", "onion")
    author = content_doc.get("author", "")

    if not text_content:
        logger.warning("Pipeline: No text content for %s, skipping", content_id)
        return {"content_id": content_id, "status": "skipped", "reason": "no_text"}

    # ── Stage 1: NLP Analysis ──────────────────────────────────────────────
    try:
        from app.nlp.analyzer import get_nlp_analyzer
        analyzer = await get_nlp_analyzer()
        analysis = await analyzer.analyze(content_id, text_content, title)
        logger.info(
            "Pipeline: NLP done for %s — class=%s, lang=%s, %.1fms",
            content_id,
            analysis.get("classification", {}).get("primary", "?"),
            analysis.get("language_detection", {}).get("language", "?"),
            analysis.get("processing_time_ms", 0),
        )
    except Exception as e:
        logger.error("Pipeline: NLP analysis failed for %s: %s", content_id, e)
        analysis = {
            "content_id": content_id,
            "entities": {},
            "classification": {"primary": "unknown", "confidence": 0},
            "sentiment": {"label": "neutral", "score": 0},
            "keyword_matches": {"matched_keywords": []},
            "error": str(e),
        }

    # Store analysis in MongoDB
    try:
        await db.raw_content.update_one(
            {"_id": content_id},
            {
                "$set": {
                    "processing_status": "analyzed",
                    "analyzed_at": datetime.now(tz=timezone.utc),
                    "analysis": analysis,
                    "updated_at": datetime.now(tz=timezone.utc),
                }
            },
        )
    except Exception as e:
        logger.warning("Pipeline: Failed to store analysis for %s: %s", content_id, e)

    # ── Stage 2: Actor Profiling ───────────────────────────────────────────
    actor_id = None
    if author and author.strip():
        try:
            from app.actors.profiler import get_actor_profiler
            profiler = await get_actor_profiler()
            actor_id = await profiler.process_content(
                content_id=content_id,
                author=author,
                content_text=text_content,
                entities=analysis.get("entities", {}),
                site_name=site_name,
                source_type=source_type,
                url=url,
                title=title,
            )
            if actor_id:
                logger.info("Pipeline: Actor %s linked for content %s", actor_id, content_id)
        except Exception as e:
            logger.error("Pipeline: Actor profiling failed for %s: %s", content_id, e)

    # ── Stage 3: Threat Scoring ────────────────────────────────────────────
    scoring_result = None
    try:
        from app.threat_scoring.engine import get_scoring_engine
        engine = await get_scoring_engine()
        scoring_result = await engine.score_and_store(
            content_id=content_id,
            classification=analysis.get("classification", {}),
            entities=analysis.get("entities", {}),
            sentiment=analysis.get("sentiment", {}),
            keyword_matches=analysis.get("keyword_matches", {}),
            published_date=None,
            site_name=site_name,
            source_type=source_type,
            actor_risk_score=None,
        )
        logger.info(
            "Pipeline: Scoring done for %s — score=%d, severity=%s",
            content_id,
            scoring_result.get("score", 0),
            scoring_result.get("severity", "?"),
        )
    except Exception as e:
        logger.error("Pipeline: Threat scoring failed for %s: %s", content_id, e)

    # ── Stage 4: Alert Evaluation ──────────────────────────────────────────
    alert = None
    if scoring_result:
        try:
            from app.alerts.engine import get_alert_engine
            alert_engine = await get_alert_engine()
            content_meta = {
                "content_id": content_id,
                "url": url,
                "site_name": site_name,
                "source_type": source_type,
                "author": author,
            }
            alert = await alert_engine.process_scored_content(
                scoring_result=scoring_result,
                analysis=analysis,
                content_meta=content_meta,
            )
            if alert:
                logger.info(
                    "Pipeline: Alert %s created for content %s (severity=%s)",
                    alert.get("_id", "?"), content_id, alert.get("severity", "?"),
                )
        except Exception as e:
            logger.error("Pipeline: Alert evaluation failed for %s: %s", content_id, e)

    # ── Stage 5: Broadcast Real-Time Updates ───────────────────────────────
    try:
        broadcaster = get_broadcaster()

        # Broadcast content update
        await broadcaster.broadcast("content", {
            "type": "content_processed",
            "content_id": content_id,
            "url": url,
            "title": analysis.get("classification", {}).get("primary", ""),
            "classification": analysis.get("classification", {}),
            "severity": scoring_result.get("severity", "unknown") if scoring_result else "unknown",
            "score": scoring_result.get("score", 0) if scoring_result else 0,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        })

        # Broadcast actor update
        if actor_id:
            await broadcaster.broadcast("actor", {
                "type": "actor_updated",
                "actor_id": actor_id,
                "pseudonym": author,
                "content_id": content_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            })

        # Broadcast alert update
        if alert:
            await broadcaster.broadcast("alert", {
                "type": "alert_created",
                "alert_id": str(alert.get("_id", "")),
                "title": alert.get("title", ""),
                "severity": alert.get("severity", "medium"),
                "score": alert.get("score", 0),
                "category": alert.get("category", "unknown"),
                "source_type": alert.get("source_type", "onion"),
                "source_url": alert.get("source_url", ""),
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            })

        # Broadcast dashboard update (aggregated)
        await broadcaster.broadcast("dashboard", {
            "type": "dashboard_update",
            "content_id": content_id,
            "score": scoring_result.get("score", 0) if scoring_result else 0,
            "severity": scoring_result.get("severity", "unknown") if scoring_result else "unknown",
            "has_alert": alert is not None,
            "has_actor": actor_id is not None,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        })

    except Exception as e:
        logger.warning("Pipeline: Broadcast failed: %s", e)

    elapsed = (time.time() - start_time) * 1000
    logger.info(
        "Pipeline: Completed for %s in %.1fms — actor=%s, alert=%s",
        content_id, elapsed, actor_id or "none", alert.get("_id", "none") if alert else "none",
    )

    return {
        "content_id": content_id,
        "status": "completed",
        "processing_time_ms": round(elapsed, 1),
        "analysis": analysis.get("classification", {}).get("primary", "unknown"),
        "score": scoring_result.get("score") if scoring_result else None,
        "severity": scoring_result.get("severity") if scoring_result else None,
        "actor_id": actor_id,
        "alert_id": str(alert.get("_id", "")) if alert else None,
    }
