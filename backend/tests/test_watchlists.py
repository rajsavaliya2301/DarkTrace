"""Tests for watchlists module — unit and API endpoint tests."""

import pytest
from datetime import datetime

from app.watchlists.models import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    RegexPattern,
    new_watchlist_document,
)


# ─── Unit Tests ───────────────────────────────────────────────────────────────


class TestWatchlistModels:
    def test_regex_pattern(self):
        pattern = RegexPattern(pattern=r"\b[A-Z]{5}\d{4}[A-Z]\b", label="PAN", case_sensitive=True)
        assert pattern.pattern == r"\b[A-Z]{5}\d{4}[A-Z]\b"
        assert pattern.label == "PAN"
        assert pattern.case_sensitive is True

    def test_watchlist_create(self):
        wl = WatchlistCreate(
            name="Ransomware Watchlist",
            description="Track ransomware keywords",
            keywords=["ransomware", "lockbit", "blackcat"],
            entities=["btc_addresses"],
            severity_boost=200,
        )
        assert wl.name == "Ransomware Watchlist"
        assert len(wl.keywords) == 3
        assert wl.severity_boost == 200
        assert wl.is_active is True

    def test_watchlist_create_with_regex(self):
        wl = WatchlistCreate(
            name="PII Watchlist",
            keywords=["ssn", "aadhaar"],
            regex_patterns=[
                RegexPattern(pattern=r"\b\d{3}-\d{2}-\d{4}\b", label="SSN"),
            ],
            severity_boost=150,
        )
        assert len(wl.regex_patterns) == 1
        assert wl.regex_patterns[0].label == "SSN"

    def test_new_watchlist_document(self):
        body = WatchlistCreate(
            name="Test Watchlist",
            keywords=["keyword1", "keyword2"],
            entities=["btc_addresses"],
        )
        doc = new_watchlist_document(body, "user123")
        assert doc["name"] == "Test Watchlist"
        assert doc["created_by"] == "user123"
        assert doc["match_count"] == 0
        assert doc["is_active"] is True
        assert "_id" in doc

    def test_watchlist_update(self):
        update = WatchlistUpdate(
            name="Updated Name",
            keywords=["newkeyword"],
            severity_boost=300,
            is_active=False,
        )
        assert update.name == "Updated Name"
        assert update.is_active is False
        assert update.severity_boost == 300


class TestWatchlistDocument:
    def test_document_keywords(self):
        body = WatchlistCreate(
            name="Test",
            keywords=["kw1", "kw2", "kw3"],
        )
        doc = new_watchlist_document(body, "user1")
        assert doc["keywords"] == ["kw1", "kw2", "kw3"]

    def test_document_entities(self):
        body = WatchlistCreate(
            name="Test",
            keywords=[],
            entities=["btc_addresses", "emails"],
        )
        doc = new_watchlist_document(body, "user1")
        assert "btc_addresses" in doc["entities"]
        assert "emails" in doc["entities"]

    def test_document_timestamps(self):
        from datetime import datetime
        body = WatchlistCreate(name="Test", keywords=[])
        doc = new_watchlist_document(body, "user1")
        assert isinstance(doc["created_at"], datetime)
        assert isinstance(doc["updated_at"], datetime)


# ─── API Integration Tests ────────────────────────────────────────────────────


class TestWatchlistsAPI:
    def test_list_watchlists_no_auth(self, client):
        """Test list watchlists without auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/watchlists")
        assert response.status_code in (401, 403)

    def test_list_watchlists_authenticated(self, client, admin_auth_headers):
        """Test list watchlists with auth."""
        response = client.get("/v1/watchlists", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_create_watchlist(self, client, admin_auth_headers):
        """Test creating a watchlist."""
        response = client.post(
            "/v1/watchlists",
            json={
                "name": "Critical Threats",
                "description": "Monitor critical threats",
                "keywords": ["ransomware", "lockbit", "data breach"],
                "entities": ["btc_addresses", "emails"],
                "severity_boost": 250,
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "Critical Threats"

    def test_create_watchlist_with_regex(self, client, admin_auth_headers):
        """Test creating a watchlist with regex patterns."""
        response = client.post(
            "/v1/watchlists",
            json={
                "name": "PII Watchlist",
                "keywords": ["ssn", "credit card"],
                "regex_patterns": [
                    {"pattern": r"\b\d{3}-\d{2}-\d{4}\b", "label": "SSN"},
                    {"pattern": r"\b[A-Z]{5}\d{4}[A-Z]\b", "label": "PAN"},
                ],
                "severity_boost": 300,
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    def test_create_watchlist_validation(self, client, admin_auth_headers):
        """Test creating watchlist with invalid data."""
        response = client.post(
            "/v1/watchlists",
            json={"name": ""},  # Empty name
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_get_watchlist(self, client, admin_auth_headers, sample_watchlist):
        """Test getting a specific watchlist."""
        watchlist_id = sample_watchlist["_id"]
        response = client.get(f"/v1/watchlists/{watchlist_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == watchlist_id
        assert data["name"] == "Ransomware Watchlist"

    def test_get_watchlist_not_found(self, client, admin_auth_headers):
        """Test getting non-existent watchlist."""
        response = client.get("/v1/watchlists/nonexistent", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_update_watchlist(self, client, admin_auth_headers, sample_watchlist):
        """Test updating a watchlist."""
        watchlist_id = sample_watchlist["_id"]
        response = client.put(
            f"/v1/watchlists/{watchlist_id}",
            json={"name": "Updated Watchlist", "severity_boost": 500},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == watchlist_id

    def test_update_watchlist_not_found(self, client, admin_auth_headers):
        """Test updating non-existent watchlist."""
        response = client.put(
            "/v1/watchlists/nonexistent",
            json={"name": "Test"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_delete_watchlist(self, client, admin_auth_headers, sample_watchlist):
        """Test deleting a watchlist."""
        watchlist_id = sample_watchlist["_id"]
        response = client.delete(f"/v1/watchlists/{watchlist_id}", headers=admin_auth_headers)
        assert response.status_code == 204

    def test_delete_watchlist_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent watchlist."""
        response = client.delete("/v1/watchlists/nonexistent", headers=admin_auth_headers)
        assert response.status_code == 404


from app.main import app
