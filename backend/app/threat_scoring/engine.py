"""Threat scoring engine — computes 0-1000 severity score for analyzed content."""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from app.threat_scoring.rules import ScoringRules, get_scoring_rules
from app.config import get_settings

logger = logging.getLogger(__name__)


class ThreatScoringEngine:
    """Computes threat severity scores (0-1000) based on multiple weighted factors."""

    async def score(
        self,
        content_id: str,
        classification: Dict,
        entities: Dict,
        sentiment: Dict,
        keyword_matches: Dict,
        published_date: Optional[str] = None,
        site_name: str = "unknown",
        source_type: str = "onion",
        actor_risk_score: Optional[int] = None,
    ) -> Dict:
        """Compute a comprehensive threat score for analyzed content."""
        rules = get_scoring_rules()
        weights = rules.get_weights()

        factors = {}

        # Factor 1: Threat classification
        class_score = rules.get_classification_score(classification.get("primary", "unknown"))
        class_weighted = class_score * weights["classification"]
        factors["threat_classification"] = {
            "score": class_score,
            "weight": weights["classification"],
            "weighted": round(class_weighted, 1),
        }

        # Factor 2: High-value targets (entities)
        hv_score = rules.get_high_value_target_score(entities)
        hv_weighted = hv_score * weights["high_value_targets"]
        factors["high_value_targets"] = {
            "score": hv_score,
            "weight": weights["high_value_targets"],
            "weighted": round(hv_weighted, 1),
        }

        # Factor 3: Actor reputation
        actor_score = actor_risk_score if actor_risk_score is not None else 0
        actor_weighted = actor_score * weights["actor_reputation"]
        factors["actor_reputation"] = {
            "score": actor_score,
            "weight": weights["actor_reputation"],
            "weighted": round(actor_weighted, 1),
        }

        # Factor 4: Freshness (recency)
        freshness_score = rules.get_freshness_score(published_date)
        freshness_weighted = freshness_score * weights["freshness"]
        factors["freshness"] = {
            "score": freshness_score,
            "weight": weights["freshness"],
            "weighted": round(freshness_weighted, 1),
        }

        # Factor 5: Sentiment
        sentiment_score = rules.get_sentiment_score(sentiment)
        sentiment_weighted = sentiment_score * weights["sentiment"]
        factors["sentiment"] = {
            "score": sentiment_score,
            "weight": weights["sentiment"],
            "weighted": round(sentiment_weighted, 1),
        }

        # Factor 6: Keyword matches
        kw_score = rules.get_keyword_match_score(keyword_matches)
        kw_weighted = kw_score * weights["keyword_matches"]
        factors["keyword_matches"] = {
            "score": kw_score,
            "weight": weights["keyword_matches"],
            "weighted": round(kw_weighted, 1),
        }

        # Factor 7: Site reputation
        site_score = rules.get_site_reputation_score(site_name, source_type)
        site_weighted = site_score * weights["site_reputation"]
        factors["site_reputation"] = {
            "score": site_score,
            "weight": weights["site_reputation"],
            "weighted": round(site_weighted, 1),
        }

        # Total raw score
        total_raw = sum(f["weighted"] for f in factors.values())

        # Normalize to 0-1000 scale
        max_possible = 1000 * sum(weights.values())  # = 1000
        normalized_score = min(1000, int(total_raw))

        # Ensure minimum score
        normalized_score = max(0, normalized_score)

        severity = rules.get_severity_label(normalized_score)

        # Build breakdown explanation
        breakdown_parts = []
        if factors["threat_classification"]["score"] > 0:
            breakdown_parts.append(f"{classification.get('primary', 'unknown')} classification")
        if factors["high_value_targets"]["score"] > 0:
            breakdown_parts.append("high-value targets mentioned")
        if factors["keyword_matches"]["score"] > 0:
            breakdown_parts.append(f"{len(keyword_matches.get('matched_keywords', []))} watchlist keywords matched")
        if factors["sentiment"]["score"] > 200:
            breakdown_parts.append("threatening/hostile sentiment")
        if factors["freshness"]["score"] > 150:
            breakdown_parts.append("recently posted content")

        return {
            "content_id": content_id,
            "score": normalized_score,
            "severity": severity,
            "factors": factors,
            "breakdown": "; ".join(breakdown_parts) if breakdown_parts else "No significant threat indicators",
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }

    async def score_and_store(
        self,
        content_id: str,
        classification: Dict,
        entities: Dict,
        sentiment: Dict,
        keyword_matches: Dict,
        published_date: Optional[str] = None,
        site_name: str = "unknown",
        source_type: str = "onion",
        actor_risk_score: Optional[int] = None,
    ) -> Dict:
        """Score content and store results in MongoDB and Elasticsearch."""
        result = await self.score(
            content_id=content_id,
            classification=classification,
            entities=entities,
            sentiment=sentiment,
            keyword_matches=keyword_matches,
            published_date=published_date,
            site_name=site_name,
            source_type=source_type,
            actor_risk_score=actor_risk_score,
        )

        try:
            from app.database import get_mongodb, get_elasticsearch
            db = await get_mongodb()

            await db.raw_content.update_one(
                {"_id": content_id},
                {
                    "$set": {
                        "processing_status": "scored",
                        "scoring": result,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            # Update Elasticsearch
            try:
                es = await get_elasticsearch()
                await es.update(
                    index="crawled_content",
                    id=content_id,
                    body={
                        "doc": {
                            "scoring": {
                                "score": result["score"],
                                "severity": result["severity"],
                            },
                            "processing_status": "scored",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                )
            except Exception as e:
                logger.warning("ES update failed for scoring %s: %s", content_id, e)

        except Exception as e:
            logger.error("Failed to store scoring for %s: %s", content_id, e)

        return result


# Singleton
_scoring_engine: Optional[ThreatScoringEngine] = None


async def get_scoring_engine() -> ThreatScoringEngine:
    """Get or create the singleton scoring engine."""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = ThreatScoringEngine()
    return _scoring_engine
