"""Tests for alerts module — unit and API endpoint tests."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from app.alerts.models import (
    AlertCondition,
    AlertNotification,
    AlertRuleCreate,
    AlertUpdateRequest,
    AlertBulkUpdateRequest,
    new_alert_document,
)
from app.alerts.engine import AlertEngine
from app.threat_scoring.rules import ScoringRules


# ─── Unit Tests ───────────────────────────────────────────────────────────────


class TestAlertModels:
    def test_alert_condition(self):
        cond = AlertCondition(field="threat_classification", operator="in", value=["ransomware"])
        assert cond.field == "threat_classification"
        assert cond.operator == "in"
        assert cond.value == ["ransomware"]

    def test_alert_notification(self):
        notif = AlertNotification(type="email", target="team@police.gov.in")
        assert notif.type == "email"
        assert notif.target == "team@police.gov.in"

    def test_alert_notification_webhook(self):
        notif = AlertNotification(type="webhook", target="https://hooks.example.com/alerts")
        assert notif.type == "webhook"
        assert notif.target == "https://hooks.example.com/alerts"

    def test_alert_rule_create(self):
        rule = AlertRuleCreate(
            name="Test Rule",
            description="Test description",
            severity_threshold=500,
            conditions=[AlertCondition(field="severity", operator="eq", value="high")],
            notifications=[AlertNotification(type="dashboard_alert")],
        )
        assert rule.name == "Test Rule"
        assert rule.severity_threshold == 500
        assert len(rule.conditions) == 1
        assert len(rule.notifications) == 1

    def test_alert_rule_create_defaults(self):
        rule = AlertRuleCreate(name="Minimal Rule")
        assert rule.enabled is True
        assert rule.severity_threshold == 400
        assert rule.cooldown_minutes == 1440

    def test_new_alert_document(self):
        alert = new_alert_document(
            title="Test Alert",
            severity="high",
            score=750,
            category="ransomware",
            source_url="http://test.onion",
            source_type="onion",
            content_id="content123",
            matched_keywords=["ransomware", "hospital"],
            summary="Test summary",
        )
        assert alert["title"] == "Test Alert"
        assert alert["severity"] == "high"
        assert alert["score"] == 750
        assert alert["status"] == "new"
        assert len(alert["timeline"]) == 1
        assert alert["timeline"][0]["event"] == "alert_created"

    def test_new_alert_document_with_entities(self):
        alert = new_alert_document(
            title="Alert with entities",
            severity="critical",
            score=900,
            category="data_breach",
            source_url="http://test.onion",
            source_type="onion",
            content_id="content456",
            entities={"emails": ["test@test.com"]},
            analysis={"classification": {"primary": "data_breach"}},
        )
        assert alert["entities"]["emails"] == ["test@test.com"]
        assert alert["analysis"]["classification"]["primary"] == "data_breach"

    def test_alert_update_request(self):
        update = AlertUpdateRequest(status="acknowledged", assignee="investigator1")
        assert update.status == "acknowledged"
        assert update.assignee == "investigator1"

    def test_alert_update_with_comment(self):
        update = AlertUpdateRequest(status="investigating", comment="Looking into this")
        assert update.status == "investigating"
        assert update.comment == "Looking into this"

    def test_alert_bulk_update(self):
        bulk = AlertBulkUpdateRequest(
            alert_ids=["id1", "id2", "id3"],
            action="resolved",
            assignee="investigator1",
        )
        assert len(bulk.alert_ids) == 3
        assert bulk.action == "resolved"


class TestScoringRules:
    def setup_method(self):
        self.rules = ScoringRules()

    def test_severity_labels(self):
        assert self.rules.get_severity_label(100) == "informational"
        assert self.rules.get_severity_label(300) == "low"
        assert self.rules.get_severity_label(500) == "medium"
        assert self.rules.get_severity_label(700) == "high"
        assert self.rules.get_severity_label(900) == "critical"

    def test_severity_boundaries(self):
        assert self.rules.get_severity_label(0) == "informational"
        assert self.rules.get_severity_label(200) == "informational"
        assert self.rules.get_severity_label(201) == "low"
        assert self.rules.get_severity_label(400) == "low"
        assert self.rules.get_severity_label(401) == "medium"
        assert self.rules.get_severity_label(600) == "medium"
        assert self.rules.get_severity_label(601) == "high"
        assert self.rules.get_severity_label(800) == "high"
        assert self.rules.get_severity_label(801) == "critical"
        assert self.rules.get_severity_label(1000) == "critical"

    def test_classification_scores(self):
        assert self.rules.get_classification_score("ransomware") == 250
        assert self.rules.get_classification_score("malware") == 200
        assert self.rules.get_classification_score("exploit") == 220
        assert self.rules.get_classification_score("data_breach") == 230
        assert self.rules.get_classification_score("unknown") == 0

    def test_high_value_targets(self):
        entities = {
            "ssn": ["123-45-6789"],
            "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
        }
        score = self.rules.get_high_value_target_score(entities)
        assert score > 0
        # SSN gives 50, BTC gives 30
        assert score >= 80

    def test_high_value_targets_missing(self):
        score = self.rules.get_high_value_target_score({})
        assert score == 0

    def test_high_value_targets_multiple(self):
        entities = {
            "ssn": ["123-45-6789", "987-65-4321"],
            "credit_cards": ["4111-1111-1111-1111"],
        }
        score = self.rules.get_high_value_target_score(entities)
        # 2 SSNs = 100, 1 credit card = 50
        assert score >= 150

    def test_keyword_match_score(self):
        matches = {
            "matched_keywords": ["ransomware", "hospital"],
            "matched_patterns": [{"label": "SSN", "matches": ["123-45-6789"], "count": 1}],
            "severity_boost": 100,
        }
        score = self.rules.get_keyword_match_score(matches)
        # 2 keywords * 30 + 1 pattern * 50 + 100 boost = 210
        assert score == 210

    def test_keyword_match_score_empty(self):
        score = self.rules.get_keyword_match_score({})
        assert score == 0

    def test_weights_default(self):
        weights = self.rules.get_weights()
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01

    def test_update_weights(self):
        new_weights = {
            "classification": 0.40,
            "high_value_targets": 0.15,
            "actor_reputation": 0.15,
            "freshness": 0.10,
            "sentiment": 0.10,
            "keyword_matches": 0.05,
            "site_reputation": 0.05,
        }
        updated = self.rules.update_weights(new_weights)
        assert updated["classification"] == 0.40
        assert abs(sum(updated.values()) - 1.0) < 0.01

    def test_update_weights_invalid(self):
        with pytest.raises(ValueError, match="must sum to 1.0"):
            self.rules.update_weights({"classification": 0.5})

    def test_sentiment_score(self):
        sentiment = {"threat_intent": 0.8, "hostility": 0.5, "urgency": 0.3}
        score = self.rules.get_sentiment_score(sentiment)
        # 0.8*200 + 0.5*150 + 0.3*100 = 160 + 75 + 30 = 265
        assert score == 265

    def test_sentiment_score_zero(self):
        score = self.rules.get_sentiment_score({})
        assert score == 0

    def test_freshness_score_no_date(self):
        score = self.rules.get_freshness_score(None)
        assert score == 100

    def test_freshness_score_recent(self):
        from datetime import datetime, timedelta
        recent = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        score = self.rules.get_freshness_score(recent)
        assert score == 200

    def test_freshness_score_old(self):
        from datetime import datetime, timedelta
        old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        score = self.rules.get_freshness_score(old)
        assert score == 20

    def test_site_reputation(self):
        assert self.rules.get_site_reputation_score("test", "onion") == 80
        assert self.rules.get_site_reputation_score("test", "i2p") == 100
        assert self.rules.get_site_reputation_score("test", "surface") == 30
        assert self.rules.get_site_reputation_score("test", "unknown") == 50


class TestAlertEngine:
    def setup_method(self):
        self.engine = AlertEngine()

    def test_resolve_field(self):
        scoring = {"score": 750, "severity": "high"}
        analysis = {"classification": {"primary": "ransomware"}}
        meta = {"url": "http://test.onion", "source_type": "onion"}

        val = self.engine._resolve_field("score", scoring, analysis, meta)
        assert val == 750

        val = self.engine._resolve_field("classification.primary", scoring, analysis, meta)
        assert val == "ransomware"

        val = self.engine._resolve_field("nonexistent.field", scoring, analysis, meta)
        assert val is None

    def test_apply_operator(self):
        assert self.engine._apply_operator("ransomware", "in", ["ransomware", "malware"]) is True
        assert self.engine._apply_operator("fraud", "in", ["ransomware", "malware"]) is False
        assert self.engine._apply_operator(["hospital"], "contains_any", ["hospital", "power"]) is True
        assert self.engine._apply_operator(["benign"], "contains_any", ["hospital", "power"]) is False
        assert self.engine._apply_operator(750, "gt", 600) is True
        assert self.engine._apply_operator(500, "gt", 600) is False
        assert self.engine._apply_operator(100, "lt", 200) is True
        assert self.engine._apply_operator(100, "lt", 50) is False
        assert self.engine._apply_operator("high", "eq", "high") is True
        assert self.engine._apply_operator("high", "eq", "low") is False
        assert self.engine._apply_operator("high", "ne", "low") is True

    def test_apply_operator_regex(self):
        assert self.engine._apply_operator("ransomware attack", "regex", r"ransom") is True
        assert self.engine._apply_operator("benign content", "regex", r"ransom") is False

    def test_apply_operator_invalid(self):
        assert self.engine._apply_operator(None, "gt", 100) is False

    def test_alert_priority(self):
        alert = {"severity": "critical"}
        assert self.engine._alert_priority(alert) == 5
        alert["severity"] = "informational"
        assert self.engine._alert_priority(alert) == 1
        alert["severity"] = "unknown"
        assert self.engine._alert_priority(alert) == 0


# ─── API Integration Tests ────────────────────────────────────────────────────


class TestAlertsAPI:
    def test_list_alerts_no_auth(self, client):
        """Test listing alerts without authentication."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/alerts")
        assert response.status_code in (401, 403)

    def test_list_alerts_authenticated(self, client, admin_auth_headers, mock_mongodb, sample_alert):
        """Test listing alerts with authentication."""
        response = client.get("/v1/alerts", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    def test_get_alert_by_id(self, client, admin_auth_headers, sample_alert):
        """Test getting a specific alert by ID."""
        alert_id = sample_alert["_id"]
        response = client.get(f"/v1/alerts/{alert_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert_id
        assert data["title"] == "Test Ransomware Alert"

    def test_get_alert_not_found(self, client, admin_auth_headers):
        """Test getting a non-existent alert."""
        response = client.get("/v1/alerts/nonexistent_id", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_update_alert_status(self, client, admin_auth_headers, sample_alert):
        """Test updating alert status."""
        alert_id = sample_alert["_id"]
        response = client.patch(
            f"/v1/alerts/{alert_id}",
            json={"status": "acknowledged", "assignee": "investigator1"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "acknowledged"

    def test_update_alert_not_found(self, client, admin_auth_headers):
        """Test updating a non-existent alert."""
        response = client.patch(
            "/v1/alerts/nonexistent",
            json={"status": "acknowledged"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_update_alert_invalid_status(self, client, admin_auth_headers, sample_alert):
        """Test updating with invalid status."""
        alert_id = sample_alert["_id"]
        response = client.patch(
            f"/v1/alerts/{alert_id}",
            json={"status": "invalid_status"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_bulk_update_alerts(self, client, admin_auth_headers, sample_alert):
        """Test bulk updating alerts."""
        response = client.post(
            "/v1/alerts/bulk",
            json={
                "alert_ids": [sample_alert["_id"]],
                "action": "acknowledge",
                "assignee": "investigator1",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "updated_count" in data

    def test_alert_stats(self, client, admin_auth_headers, mock_mongodb, sample_alert):
        """Test getting alert statistics."""
        response = client.get("/v1/alerts/stats", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_severity" in data
        assert "by_status" in data
        assert "trend" in data

    def test_alert_stats_no_auth(self, client):
        """Test stats without auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/alerts/stats")
        assert response.status_code in (401, 403)

    def test_list_alerts_with_filters(self, client, admin_auth_headers, mock_mongodb, sample_alert):
        """Test listing alerts with severity filter."""
        response = client.get("/v1/alerts?severity=high", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_list_alerts_with_pagination(self, client, admin_auth_headers, sample_alert):
        """Test listing alerts with pagination."""
        response = client.get("/v1/alerts?page=1&per_page=10", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 10


class TestAlertRulesAPI:
    def test_list_alert_rules(self, client, admin_auth_headers):
        """Test listing alert rules."""
        response = client.get("/v1/alert-rules", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_create_alert_rule(self, client, admin_auth_headers):
        """Test creating an alert rule."""
        response = client.post(
            "/v1/alert-rules",
            json={
                "name": "Critical Ransomware Rule",
                "description": "Alert on ransomware with high score",
                "severity_threshold": 700,
                "conditions": [
                    {"field": "classification.primary", "operator": "in", "value": ["ransomware"]},
                    {"field": "score", "operator": "gt", "value": 600},
                ],
                "notifications": [
                    {"type": "dashboard_alert"},
                    {"type": "email", "target": "team@example.com"},
                ],
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "Critical Ransomware Rule"

    def test_create_alert_rule_validation(self, client, admin_auth_headers):
        """Test creating alert rule with invalid data."""
        response = client.post(
            "/v1/alert-rules",
            json={"name": ""},  # Empty name
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_update_alert_rule(self, client, admin_auth_headers, mock_mongodb):
        """Test updating an alert rule."""
        import asyncio
        import uuid
        rule_id = str(uuid.uuid4())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(mock_mongodb.alert_rules.insert_one({
            "_id": rule_id,
            "name": "Old Rule",
            "description": "Old description",
            "enabled": True,
            "severity_threshold": 400,
            "conditions": [],
            "notifications": [],
        }))
        loop.close()

        response = client.put(
            f"/v1/alert-rules/{rule_id}",
            json={"name": "Updated Rule", "severity_threshold": 600},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == rule_id

    def test_delete_alert_rule(self, client, admin_auth_headers, mock_mongodb):
        """Test deleting an alert rule."""
        import asyncio
        import uuid
        rule_id = str(uuid.uuid4())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(mock_mongodb.alert_rules.insert_one({
            "_id": rule_id,
            "name": "Rule to Delete",
            "enabled": True,
        }))
        loop.close()

        response = client.delete(f"/v1/alert-rules/{rule_id}", headers=admin_auth_headers)
        assert response.status_code == 204


from app.main import app
