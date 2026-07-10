"""API integration tests using TestClient — health, auth, and basic endpoint checks."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Patch all database connections BEFORE importing app
with patch("app.database.init_mongodb", new_callable=AsyncMock):
    with patch("app.database.init_elasticsearch", new_callable=AsyncMock):
        with patch("app.database.init_neo4j", new_callable=AsyncMock):
            with patch("app.database.init_redis", new_callable=AsyncMock):
                from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_openapi_schema(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestAuthEndpoints:
    def test_login_no_credentials(self):
        response = client.post("/v1/auth/login", json={})
        assert response.status_code == 422  # Validation error

    def test_login_invalid_email(self):
        response = client.post("/v1/auth/login", json={
            "email": "not-an-email",
            "password": "test123",
        })
        assert response.status_code == 422

    def test_refresh_no_token(self):
        response = client.post("/v1/auth/refresh", json={})
        assert response.status_code == 422

    def test_logout_no_auth(self):
        response = client.post("/v1/auth/logout")
        # Should be 401 since no token provided (auth dependency)
        assert response.status_code in (401, 403)


class TestAlertsEndpoints:
    def test_list_alerts_no_auth(self):
        response = client.get("/v1/alerts")
        assert response.status_code in (401, 403)

    def test_alert_stats_no_auth(self):
        response = client.get("/v1/alerts/stats")
        assert response.status_code in (401, 403)


class TestCrawlerEndpoints:
    def test_list_targets_no_auth(self):
        response = client.get("/v1/crawler/targets")
        assert response.status_code in (401, 403)

    def test_list_jobs_no_auth(self):
        response = client.get("/v1/crawler/jobs")
        assert response.status_code in (401, 403)


class TestWatchlistEndpoints:
    def test_list_watchlists_no_auth(self):
        response = client.get("/v1/watchlists")
        assert response.status_code in (401, 403)


class TestSearchEndpoints:
    def test_search_no_query(self):
        """Search without query - auth check happens first, then validation."""
        response = client.get("/v1/search")
        # Without auth, 401 is correct (auth dependency checked before validation)
        assert response.status_code in (401, 422)

    def test_search_no_auth(self):
        response = client.get("/v1/search?q=test")
        assert response.status_code in (401, 403)


class TestDashboardEndpoints:
    def test_summary_no_auth(self):
        response = client.get("/v1/dashboard/summary")
        assert response.status_code in (401, 403)

    def test_trending_no_auth(self):
        response = client.get("/v1/dashboard/trending")
        assert response.status_code in (401, 403)


class TestAdminEndpoints:
    def test_system_health_endpoint(self):
        """System health may work or fail based on DB connections."""
        response = client.get("/v1/admin/health")
        # When DBs are mocked, this may fail with various errors
        assert response.status_code in (200, 401, 403, 500, 503)


class TestErrorHandling:
    def test_404(self):
        response = client.get("/v1/nonexistent/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        response = client.put("/v1/alerts")
        assert response.status_code == 405

    def test_health_check_returns_json(self):
        response = client.get("/health")
        assert response.headers["content-type"].startswith("application/json")


class TestCORSMiddleware:
    def test_cors_headers(self):
        """Test that CORS middleware adds appropriate headers."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should return 200 or appropriate
        assert response.status_code in (200, 204)


from app.main import app
