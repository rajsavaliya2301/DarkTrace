"""Configurable scoring rules for the threat scoring engine."""

import json
from typing import Dict, List, Optional

from app.config import get_settings


class ScoringRules:
    """Manages configurable scoring rules and weights."""

    DEFAULT_WEIGHTS = {
        "classification": 0.30,
        "high_value_targets": 0.20,
        "actor_reputation": 0.15,
        "freshness": 0.10,
        "sentiment": 0.10,
        "keyword_matches": 0.10,
        "site_reputation": 0.05,
    }

    SEVERITY_THRESHOLDS = {
        "informational": (0, 200),
        "low": (201, 400),
        "medium": (401, 600),
        "high": (601, 800),
        "critical": (801, 1000),
    }

    # High-value entity types (including Indian-specific PII)
    HIGH_VALUE_ENTITIES = [
        "ssn", "credit_cards", "aadhaar", "pan", "passport",
        "voter_id", "driving_license", "upi_ids", "gst_numbers",
        "ifsc_codes", "bank_accounts", "vehicle_registration",
        "credit_card_bins",
    ]

    # Classification score mapping (how much each class contributes)
    CLASSIFICATION_SCORES = {
        "terrorism": 350,
        "weapons_trafficking": 310,
        "human_trafficking": 340,
        "narcotics": 280,
        "cyber_espionage": 290,
        "extremism": 300,
        "ransomware": 250,
        "data_breach": 230,
        "exploit": 220,
        "identity_theft": 220,
        "malware": 200,
        "intelligence": 200,
        "carding": 190,
        "fraud": 180,
        "illegal_goods": 170,
        "services": 150,
        "hacktivism": 120,
        "unknown": 0,
    }

    def __init__(self):
        self._weights = self.DEFAULT_WEIGHTS.copy()

    def get_weights(self) -> Dict[str, float]:
        """Get current scoring weights."""
        return self._weights.copy()

    def update_weights(self, new_weights: Dict[str, float]) -> Dict[str, float]:
        """Update scoring weights (must sum to 1.0)."""
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        self._weights.update(new_weights)
        return self._weights.copy()

    def get_severity_label(self, score: int) -> str:
        """Get severity label for a numeric score."""
        for severity, (low, high) in self.SEVERITY_THRESHOLDS.items():
            if low <= score <= high:
                return severity
        return "informational" if score < 200 else "critical"

    def get_classification_score(self, primary_class: str) -> int:
        """Get base score contribution from a threat classification."""
        return self.CLASSIFICATION_SCORES.get(primary_class, 0)

    def get_high_value_target_score(self, entities: Dict) -> int:
        """Calculate score contribution from high-value targets mentioned."""
        score = 0
        for entity_type in self.HIGH_VALUE_ENTITIES:
            items = entities.get(entity_type, [])
            if items:
                score += min(len(items) * 50, 200)  # Max 200 from entity matches

        # Indian PII is particularly valuable on dark web
        indian_pii_types = ["aadhaar", "pan", "voter_id", "driving_license", "passport"]
        for entity_type in indian_pii_types:
            items = entities.get(entity_type, [])
            if items:
                score += min(len(items) * 80, 300)  # Higher weight for Indian PII

        # UPI/Bank/IFSC data indicates financial targeting
        financial_india = ["upi_ids", "ifsc_codes", "bank_accounts"]
        for entity_type in financial_india:
            items = entities.get(entity_type, [])
            if items:
                score += min(len(items) * 40, 150)

        # BTC/ETH addresses indicate financial activity
        for crypto in ["btc_addresses", "eth_addresses", "xmr_addresses"]:
            items = entities.get(crypto, [])
            if items:
                score += min(len(items) * 30, 150)
        return min(score, 600)

    def get_keyword_match_score(self, keyword_matches: Dict) -> int:
        """Calculate score from keyword matches."""
        matched_keywords = keyword_matches.get("matched_keywords", [])
        matched_patterns = keyword_matches.get("matched_patterns", [])
        severity_boost = keyword_matches.get("severity_boost", 0)

        base_score = len(matched_keywords) * 30 + len(matched_patterns) * 50
        base_score += severity_boost
        return min(base_score, 500)

    def get_sentiment_score(self, sentiment: Dict) -> int:
        """Calculate score from sentiment analysis."""
        threat_intent = sentiment.get("threat_intent", 0) * 200
        hostility = sentiment.get("hostility", 0) * 150
        urgency = sentiment.get("urgency", 0) * 100
        return int(threat_intent + hostility + urgency)

    def get_freshness_score(self, published_date: Optional[str] = None) -> int:
        """Calculate score based on how recent the content is."""
        import time
        from datetime import datetime, timezone

        if not published_date:
            return 100  # Default: moderately fresh

        try:
            if isinstance(published_date, str):
                pub_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            else:
                pub_date = published_date
            hours_old = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600
            if hours_old < 1:
                return 200
            elif hours_old < 24:
                return 150
            elif hours_old < 168:  # 7 days
                return 100
            elif hours_old < 720:  # 30 days
                return 50
            else:
                return 20
        except Exception:
            return 100

    def get_site_reputation_score(self, site_name: str, source_type: str) -> int:
        """Calculate score based on site reputation."""
        # Known malicious or high-risk site types
        reputation_scores = {
            "onion": 80,  # Default .onion bonus
            "i2p": 100,  # I2P is more obscure
            "surface": 30,  # Surface web
        }
        base = reputation_scores.get(source_type, 50)

        # Known high-threat sites get additional bonus
        high_risk_sites = [
            "breachforum", "raidforum", "exploit", "nulled", "cracked",
            "carding", "dumpshop", "intelforge", "darkleaks", "breacheddb",
            "hydra", "silkroad", "alphabay", "torrez", "darkmarket",
            "isis", "jihad", "terror", "recruitment", "propaganda",
        ]
        if site_name and any(risk in site_name.lower() for risk in high_risk_sites):
            base = min(base + 40, 150)

        return base


# Singleton
_scoring_rules: Optional[ScoringRules] = None


def get_scoring_rules() -> ScoringRules:
    """Get or create the singleton scoring rules."""
    global _scoring_rules
    if _scoring_rules is None:
        _scoring_rules = ScoringRules()
    return _scoring_rules
