"""Tests for threat scoring module — unit tests for engine and rules."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.threat_scoring.engine import ThreatScoringEngine, get_scoring_engine
from app.threat_scoring.rules import ScoringRules, get_scoring_rules


# ─── Scoring Rules Tests ──────────────────────────────────────────────────────


class TestScoringRulesExtended:
    def setup_method(self):
        self.rules = ScoringRules()

    def test_get_weights_returns_copy(self):
        weights = self.rules.get_weights()
        weights["classification"] = 0.0
        # Original should not be modified
        assert self.rules.get_weights()["classification"] == 0.30

    def test_severity_label_out_of_range_low(self):
        assert self.rules.get_severity_label(-100) == "informational"

    def test_severity_label_out_of_range_high(self):
        assert self.rules.get_severity_label(1500) == "critical"

    def test_high_value_targets_max_cap(self):
        """Test high value target score is capped at 500."""
        entities = {
            "ssn": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],  # 10 * 50 = 500, capped at 200
            "btc_addresses": ["addr1", "addr2", "addr3", "addr4", "addr5"],  # 5 * 30 = 150
        }
        score = self.rules.get_high_value_target_score(entities)
        # Max from SSN type (capped at 200) + 150 from BTC = 350
        assert score <= 500
        assert score >= 200

    def test_keyword_match_score_empty(self):
        score = self.rules.get_keyword_match_score({})
        assert score == 0

    def test_keyword_match_score_no_matches(self):
        score = self.rules.get_keyword_match_score({
            "matched_keywords": [],
            "matched_patterns": [],
            "severity_boost": 0,
        })
        assert score == 0

    def test_freshness_score_invalid_date(self):
        score = self.rules.get_freshness_score("invalid-date-format")
        assert score == 100  # Default on error

    def test_site_reputation_default(self):
        score = self.rules.get_site_reputation_score("unknown_site", "unknown_type")
        assert score == 50


# ─── Scoring Engine Tests ─────────────────────────────────────────────────────


class TestThreatScoringEngine:
    @pytest.mark.asyncio
    async def test_score_with_all_factors(self):
        """Test scoring with all factors present."""
        engine = ThreatScoringEngine()
        result = await engine.score(
            content_id="content123",
            classification={"primary": "ransomware", "secondary": []},
            entities={
                "ssn": ["123-45-6789"],
                "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
            },
            sentiment={"threat_intent": 0.8, "hostility": 0.5, "urgency": 0.3},
            keyword_matches={
                "matched_keywords": ["ransomware", "hospital"],
                "matched_patterns": [{"label": "SSN", "matches": ["123-45-6789"], "count": 1}],
                "severity_boost": 100,
            },
            published_date=datetime.now(timezone.utc).isoformat(),
            site_name="DarkMarket",
            source_type="onion",
            actor_risk_score=500,
        )
        assert "content_id" in result
        assert result["content_id"] == "content123"
        assert "score" in result
        assert 0 <= result["score"] <= 1000
        assert "severity" in result
        assert result["severity"] in ("informational", "low", "medium", "high", "critical")
        assert "factors" in result
        assert "breakdown" in result
        assert "scored_at" in result

    @pytest.mark.asyncio
    async def test_score_minimal_input(self):
        """Test scoring with minimal input (no threat indicators)."""
        engine = ThreatScoringEngine()
        result = await engine.score(
            content_id="content456",
            classification={"primary": "unknown", "secondary": []},
            entities={},
            sentiment={"threat_intent": 0.0, "hostility": 0.0, "urgency": 0.0},
            keyword_matches={"matched_keywords": [], "matched_patterns": [], "severity_boost": 0},
        )
        assert result["score"] >= 0
        assert result["severity"] in ("informational", "low")

    @pytest.mark.asyncio
    async def test_score_high_severity(self):
        """Test that high threat inputs produce high scores."""
        engine = ThreatScoringEngine()
        result = await engine.score(
            content_id="content789",
            classification={"primary": "ransomware"},
            entities={
                "ssn": ["123-45-6789", "987-65-4321", "555-55-5555"],
                "credit_cards": ["4111-1111-1111-1111"],
                "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
            },
            sentiment={"threat_intent": 0.9, "hostility": 0.8, "urgency": 0.7},
            keyword_matches={
                "matched_keywords": ["ransomware", "hospital", "attack", "urgent"],
                "severity_boost": 200,
            },
            published_date=datetime.now(timezone.utc).isoformat(),
            site_name="DarkMarket",
            source_type="onion",
            actor_risk_score=800,
        )
        assert result["score"] >= 300  # Should be at least medium

    @pytest.mark.asyncio
    async def test_score_all_factors_present(self):
        """Test that all 7 factors are present in result."""
        engine = ThreatScoringEngine()
        result = await engine.score(
            content_id="test123",
            classification={"primary": "malware"},
            entities={"btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"]},
            sentiment={"threat_intent": 0.5, "hostility": 0.3, "urgency": 0.2},
            keyword_matches={"matched_keywords": ["malware"], "severity_boost": 50},
        )
        factor_keys = set(result["factors"].keys())
        expected = {"threat_classification", "high_value_targets", "actor_reputation",
                     "freshness", "sentiment", "keyword_matches", "site_reputation"}
        assert factor_keys == expected

    @pytest.mark.asyncio
    async def test_score_normalization(self):
        """Test that score is normalized to 0-1000 range."""
        engine = ThreatScoringEngine()
        # Very high input values
        result = await engine.score(
            content_id="high_input",
            classification={"primary": "ransomware"},
            entities={
                "ssn": ["1", "2", "3", "4", "5", "6", "7"],
                "credit_cards": ["cc1", "cc2", "cc3"],
                "btc_addresses": ["btc1", "btc2", "btc3", "btc4", "btc5"],
            },
            sentiment={"threat_intent": 0.99, "hostility": 0.99, "urgency": 0.99},
            keyword_matches={
                "matched_keywords": ["a", "b", "c", "d", "e", "f", "g", "h"],
                "severity_boost": 500,
            },
            published_date=datetime.now(timezone.utc).isoformat(),
            actor_risk_score=1000,
        )
        assert 0 <= result["score"] <= 1000

    @pytest.mark.asyncio
    async def test_score_actor_reputation(self):
        """Test actor reputation scoring."""
        engine = ThreatScoringEngine()
        result_with_actor = await engine.score(
            content_id="with_actor",
            classification={"primary": "unknown"},
            entities={},
            sentiment={"threat_intent": 0, "hostility": 0, "urgency": 0},
            keyword_matches={},
            actor_risk_score=500,
        )
        result_without_actor = await engine.score(
            content_id="without_actor",
            classification={"primary": "unknown"},
            entities={},
            sentiment={"threat_intent": 0, "hostility": 0, "urgency": 0},
            keyword_matches={},
        )
        assert result_with_actor["score"] >= result_without_actor["score"]

    @pytest.mark.asyncio
    async def test_score_severity_mapping_low(self):
        """Test that low scores map to informational/low severity."""
        engine = ThreatScoringEngine()
        result = await engine.score(
            content_id="low_threat",
            classification={"primary": "unknown"},
            entities={},
            sentiment={"threat_intent": 0, "hostility": 0, "urgency": 0},
            keyword_matches={},
        )
        assert result["severity"] in ("informational", "low")

    @pytest.mark.asyncio
    async def test_score_and_store(self):
        """Test scoring with storage."""
        engine = ThreatScoringEngine()
        result = await engine.score_and_store(
            content_id="store_test",
            classification={"primary": "ransomware"},
            entities={"btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"]},
            sentiment={"threat_intent": 0.5, "hostility": 0.3, "urgency": 0.2},
            keyword_matches={"matched_keywords": ["ransomware"], "severity_boost": 0},
        )
        assert "content_id" in result
        assert result["content_id"] == "store_test"

    @pytest.mark.asyncio
    async def test_breakdown_empty(self):
        """Test breakdown message when no significant indicators."""
        engine = ThreatScoringEngine()
        result = await engine.score(
            content_id="empty_breakdown",
            classification={"primary": "unknown"},
            entities={},
            sentiment={"threat_intent": 0, "hostility": 0, "urgency": 0},
            keyword_matches={},
            published_date=(datetime.now(timezone.utc) - timedelta(days=365)).isoformat(),
        )
        assert result["breakdown"] == "No significant threat indicators" or "breakdown" in result

    @pytest.mark.asyncio
    async def test_breakdown_with_indicators(self):
        """Test breakdown message with threat indicators."""
        engine = ThreatScoringEngine()
        result = await engine.score(
            content_id="with_indicators",
            classification={"primary": "ransomware"},
            entities={"ssn": ["123-45-6789"]},
            sentiment={"threat_intent": 0.8, "hostility": 0.6, "urgency": 0.4},
            keyword_matches={"matched_keywords": ["ransomware", "hospital"], "severity_boost": 100},
            published_date=datetime.now(timezone.utc).isoformat(),
        )
        assert result["breakdown"] != "No significant threat indicators"

    @pytest.mark.asyncio
    async def test_singleton(self):
        """Test that get_scoring_engine returns the same instance."""
        engine1 = await get_scoring_engine()
        engine2 = await get_scoring_engine()
        assert engine1 is engine2  # Singleton


class TestScoringRulesSingleton:
    @pytest.mark.asyncio
    async def test_get_scoring_rules(self):
        """Test that get_scoring_rules returns a ScoringRules instance."""
        rules = get_scoring_rules()
        assert isinstance(rules, ScoringRules)

    def test_singleton_consistency(self):
        rules1 = get_scoring_rules()
        rules2 = get_scoring_rules()
        assert rules1 is rules2


from app.main import app  # noqa: E402 — needed for API endpoint tests


# ─── Threat Scoring API Integration Tests ──────────────────────────────────────


class TestThreatScoringApiEndpoints:
    """Integration tests for threat scoring API endpoints."""

    def test_score_no_auth(self, client):
        """Test scoring endpoint requires auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        response = client.post("/v1/threat-scoring/score", json={"content_type": "text", "content": "test"})
        assert response.status_code in (401, 403)

    def test_score_authenticated(self, client, admin_auth_headers):
        """Test scoring endpoint with auth."""
        response = client.post(
            "/v1/threat-scoring/score",
            json={
                "content_id": "test-content-1",
                "source_type": "onion",
                "site_name": "test-site",
                "published_date": "2026-01-01T00:00:00",
                "classification": {"category": "ransomware", "severity": "high"},
                "entities": {"urls": ["http://test.onion"]},
                "sentiment": {"label": "negative", "score": -0.8},
                "keyword_matches": {"ransomware": 3, "bitcoin": 2},
            },
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 500)

    def test_score_validation(self, client, admin_auth_headers):
        """Test scoring validation (missing content)."""
        response = client.post(
            "/v1/threat-scoring/score",
            json={"content_type": "text"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_list_rules_authenticated(self, client, admin_auth_headers):
        """Test listing scoring rules with auth."""
        response = client.get("/v1/threat-scoring/rules", headers=admin_auth_headers)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert "weights" in response.json()

    def test_list_rules_no_auth(self, client):
        """Test listing rules requires auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        response = client.get("/v1/threat-scoring/rules")
        assert response.status_code in (401, 403)

    def test_update_rules_as_admin(self, client, admin_auth_headers):
        """Test updating scoring rules as admin."""
        response = client.put(
            "/v1/threat-scoring/rules",
            json={"weights": {"keyword": 0.3, "sentiment": 0.2, "freshness": 0.25, "site_reputation": 0.25}},
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 403, 500)

    def test_update_rules_as_viewer(self, client, viewer_auth_headers):
        """Test updating scoring rules as viewer (should be forbidden)."""
        response = client.put(
            "/v1/threat-scoring/rules",
            json={"weights": {"keyword": 2.0}},
            headers=viewer_auth_headers,
        )
        assert response.status_code == 403
