"""Tests for search module — API endpoint tests."""

import pytest
from unittest.mock import AsyncMock, patch


# ─── API Integration Tests ────────────────────────────────────────────────────


class TestSearchAPI:
    def test_search_no_query(self, client):
        """Test search without query parameter."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/search")
        # Without auth, it fails with 401 before validation
        assert response.status_code in (401, 422)

    def test_search_no_auth(self, client):
        """Test search without authentication."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/search?q=ransomware")
        assert response.status_code in (401, 403)

    def test_search_authenticated(self, client, admin_auth_headers):
        """Test search with authentication."""
        response = client.get("/v1/search?q=ransomware", headers=admin_auth_headers)
        assert response.status_code in (200, 502)  # 502 if ES fails

    def test_search_with_filters(self, client, admin_auth_headers):
        """Test search with filters."""
        response = client.get(
            "/v1/search?q=test&source_type=onion&category=ransomware",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_with_pagination(self, client, admin_auth_headers):
        """Test search with pagination parameters."""
        response = client.get(
            "/v1/search?q=test&page=1&per_page=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_with_date_filters(self, client, admin_auth_headers):
        """Test search with date range filters."""
        response = client.get(
            "/v1/search?q=test&date_from=2024-01-01&date_to=2024-12-31",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_with_author_filter(self, client, admin_auth_headers):
        """Test search with author filter."""
        response = client.get(
            "/v1/search?q=test&author=dark_hacker",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_with_language_filter(self, client, admin_auth_headers):
        """Test search with language filter."""
        response = client.get(
            "/v1/search?q=test&language=en",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_with_entity_filter(self, client, admin_auth_headers):
        """Test search with entity filter."""
        response = client.get(
            "/v1/search?q=test&has_entities=btc",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_sort_by_date(self, client, admin_auth_headers):
        """Test search sorted by date."""
        response = client.get(
            "/v1/search?q=test&sort_by=date",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_sort_by_score(self, client, admin_auth_headers):
        """Test search sorted by score."""
        response = client.get(
            "/v1/search?q=test&sort_by=score",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_long_query(self, client, admin_auth_headers):
        """Test search with a very specific query."""
        response = client.get(
            "/v1/search?q=ransomware+exploit+kit+selling+bitcoin",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 502)

    def test_search_invalid_page(self, client, admin_auth_headers):
        """Test search with invalid page number."""
        response = client.get(
            "/v1/search?q=test&page=0",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 422, 502)

    def test_search_excessive_per_page(self, client, admin_auth_headers):
        """Test search with excessive per_page value."""
        response = client.get(
            "/v1/search?q=test&per_page=200",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 422, 502)


from app.main import app


# ─── Saved Search Tests ────────────────────────────────────────────────────────


class TestSavedSearchAPI:
    """Tests for saved search CRUD and report generation endpoints."""

    def test_list_saved_searches_no_auth(self, client):
        """Test listing saved searches requires auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/search/saved")
        assert response.status_code in (401, 403)

    def test_list_saved_searches_authenticated(self, client, admin_auth_headers):
        """Test listing saved searches with auth."""
        response = client.get("/v1/search/saved", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_create_saved_search(self, client, admin_auth_headers):
        """Test creating a saved search."""
        response = client.post(
            "/v1/search/saved",
            json={
                "name": "Ransomware Tracker",
                "query": "ransomware leak site:onion",
                "filters": {"source_type": "onion", "category": "ransomware"},
                "notify_on_new": True,
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "Ransomware Tracker"
        assert data["query"] == "ransomware leak site:onion"
        assert "id" in data

    def test_create_saved_search_validation(self, client, admin_auth_headers):
        """Test saved search validation (empty name)."""
        response = client.post(
            "/v1/search/saved",
            json={"name": "", "query": "test"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_get_saved_search(self, client, admin_auth_headers):
        """Test getting a specific saved search."""
        # Create first
        create_resp = client.post(
            "/v1/search/saved",
            json={"name": "Test Get", "query": "test query"},
            headers=admin_auth_headers,
        )
        search_id = create_resp.json()["data"]["id"]

        # Get
        response = client.get(f"/v1/search/saved/{search_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == search_id
        assert data["name"] == "Test Get"

    def test_get_saved_search_not_found(self, client, admin_auth_headers):
        """Test getting a non-existent saved search."""
        response = client.get("/v1/search/saved/nonexistent-id", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_update_saved_search(self, client, admin_auth_headers):
        """Test updating a saved search."""
        # Create
        create_resp = client.post(
            "/v1/search/saved",
            json={"name": "Original", "query": "original query"},
            headers=admin_auth_headers,
        )
        search_id = create_resp.json()["data"]["id"]

        # Update
        response = client.put(
            f"/v1/search/saved/{search_id}",
            json={"name": "Updated Name"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Name"

    def test_delete_saved_search(self, client, admin_auth_headers):
        """Test deleting a saved search."""
        # Create
        create_resp = client.post(
            "/v1/search/saved",
            json={"name": "To Delete", "query": "delete me"},
            headers=admin_auth_headers,
        )
        search_id = create_resp.json()["data"]["id"]

        # Delete
        response = client.delete(f"/v1/search/saved/{search_id}", headers=admin_auth_headers)
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f"/v1/search/saved/{search_id}", headers=admin_auth_headers)
        assert get_resp.status_code == 404

    def test_generate_report_from_saved_search(self, client, admin_auth_headers):
        """Test generating a report from a saved search."""
        # Create saved search
        create_resp = client.post(
            "/v1/search/saved",
            json={"name": "Report Gen", "query": "ransomware"},
            headers=admin_auth_headers,
        )
        search_id = create_resp.json()["data"]["id"]

        # Generate report
        response = client.post(
            f"/v1/search/saved/{search_id}/generate-report",
            json={"format": "json", "include_evidence": False},
            headers=admin_auth_headers,
        )
        # May fail with 502 if ES is not available, but should not be 401/403/404
        assert response.status_code in (200, 201, 202, 502)
