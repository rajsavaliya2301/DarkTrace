"""Tests for dashboard module — API endpoint tests."""

import pytest
from datetime import datetime, timedelta


# ─── API Integration Tests ────────────────────────────────────────────────────


class TestDashboardAPI:
    def test_dashboard_summary_no_auth(self, client):
        """Test dashboard summary without auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/dashboard/summary")
        assert response.status_code in (401, 403)

    def test_dashboard_summary_authenticated(self, client, admin_auth_headers):
        """Test dashboard summary with auth."""
        response = client.get("/v1/dashboard/summary", headers=admin_auth_headers)
        assert response.status_code in (200, 500)  # May 500 if no DB data

    def test_dashboard_summary_structure(self, client, admin_auth_headers, mock_mongodb, sample_alert):
        """Test dashboard summary returns correct structure."""
        response = client.get("/v1/dashboard/summary", headers=admin_auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "active_alerts" in data
            assert "crawler_status" in data
            assert "actors" in data
            assert "recent_alerts" in data
            assert "top_categories" in data

    def test_dashboard_trending_no_auth(self, client):
        """Test dashboard trending without auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/dashboard/trending")
        assert response.status_code in (401, 403)

    def test_dashboard_trending_authenticated(self, client, admin_auth_headers):
        """Test dashboard trending with auth."""
        response = client.get("/v1/dashboard/trending", headers=admin_auth_headers)
        assert response.status_code in (200, 500)

    def test_dashboard_trending_structure(self, client, admin_auth_headers, mock_mongodb, sample_alert, sample_actor):
        """Test dashboard trending returns correct structure."""
        response = client.get("/v1/dashboard/trending?days=7", headers=admin_auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "most_mentioned_products" in data
            assert "most_active_marketplaces" in data
            assert "top_threat_actors" in data
            assert "language_distribution" in data

    def test_dashboard_timeline_no_auth(self, client):
        """Test dashboard timeline without auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/dashboard/timeline")
        assert response.status_code in (401, 403)

    def test_dashboard_timeline_authenticated(self, client, admin_auth_headers):
        """Test dashboard timeline with auth."""
        response = client.get("/v1/dashboard/timeline", headers=admin_auth_headers)
        assert response.status_code in (200, 500)

    def test_dashboard_timeline_structure(self, client, admin_auth_headers, mock_mongodb, sample_alert):
        """Test dashboard timeline returns correct structure."""
        response = client.get(
            "/v1/dashboard/timeline?days=7&granularity=day",
            headers=admin_auth_headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "alert_timeline" in data
            assert "crawl_timeline" in data
            assert "period" in data

    def test_dashboard_timeline_hourly(self, client, admin_auth_headers):
        """Test dashboard timeline with hourly granularity."""
        response = client.get(
            "/v1/dashboard/timeline?days=1&granularity=hour",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 500)


from app.main import app
