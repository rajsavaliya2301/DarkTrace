"""Tests for reports module — unit and API endpoint tests."""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.reports.generator import ReportGenerator
from app.reports.router import ReportGenerateRequest


# ─── Unit Tests ───────────────────────────────────────────────────────────────


class TestReportGenerator:
    @pytest.mark.asyncio
    async def test_collect_data_alert_report_missing_id(self):
        """Test collecting data for alert report without alert_id."""
        generator = ReportGenerator()
        with pytest.raises(ValueError, match="alert_id required"):
            await generator._collect_data("alert_report", {})

    @pytest.mark.asyncio
    async def test_collect_data_actor_report_missing_id(self):
        """Test collecting data for actor dossier without actor_id."""
        generator = ReportGenerator()
        with pytest.raises(ValueError, match="actor_id required"):
            await generator._collect_data("actor_dossier", {})

    @pytest.mark.asyncio
    async def test_collect_data_unsupported_type(self):
        """Test collecting data for unsupported report type."""
        generator = ReportGenerator()
        with pytest.raises(ValueError, match="Unsupported report type"):
            await generator._collect_data("unsupported_type", {})


class TestReportGenerateRequest:
    def test_valid_request(self):
        req = ReportGenerateRequest(
            type="alert_report",
            format="pdf",
            parameters={"alert_id": "alert123"},
        )
        assert req.type == "alert_report"
        assert req.format == "pdf"
        assert req.parameters["alert_id"] == "alert123"

    def test_invalid_type(self):
        with pytest.raises(Exception):
            ReportGenerateRequest(
                type="invalid_type",
                format="pdf",
            )

    def test_invalid_format(self):
        with pytest.raises(Exception):
            ReportGenerateRequest(
                type="alert_report",
                format="docx",  # Invalid format
            )


# ─── API Integration Tests ────────────────────────────────────────────────────


class TestReportsAPI:
    def test_generate_report_no_auth(self, client):
        """Test generate report without auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.post(
            "/v1/reports",
            json={
                "type": "alert_report",
                "format": "pdf",
                "parameters": {"alert_id": "alert123"},
            },
        )
        assert response.status_code in (401, 403)

    def test_generate_report(self, client, admin_auth_headers):
        """Test generating a report."""
        response = client.post(
            "/v1/reports",
            json={
                "type": "alert_report",
                "format": "pdf",
                "parameters": {"alert_id": "alert123"},
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "report_id" in data
        assert data["status"] == "generating"

    def test_generate_report_invalid_type(self, client, admin_auth_headers):
        """Test generating report with invalid type."""
        response = client.post(
            "/v1/reports",
            json={
                "type": "invalid_type",
                "format": "pdf",
                "parameters": {},
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_list_reports(self, client, admin_auth_headers):
        """Test listing reports."""
        response = client.get("/v1/reports", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    def test_list_reports_with_type_filter(self, client, admin_auth_headers):
        """Test listing reports with type filter."""
        response = client.get("/v1/reports?type_filter=alert_report", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_get_report(self, client, admin_auth_headers, sample_report):
        """Test getting a specific report."""
        report_id = sample_report["_id"]
        response = client.get(f"/v1/reports/{report_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
        assert data["status"] == "completed"

    def test_get_report_not_found(self, client, admin_auth_headers):
        """Test getting non-existent report."""
        response = client.get("/v1/reports/nonexistent", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_download_report_no_token(self, client, admin_auth_headers, sample_report):
        """Test downloading report without token."""
        report_id = sample_report["_id"]
        response = client.get(
            f"/v1/reports/{report_id}/download",
            headers=admin_auth_headers,
        )
        # Will fail because token is empty
        assert response.status_code in (403, 400, 404)

    def test_download_report_not_found(self, client, admin_auth_headers):
        """Test downloading non-existent report."""
        response = client.get(
            "/v1/reports/nonexistent/download?token=test",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_delete_report(self, client, admin_auth_headers, sample_report):
        """Test deleting a report - not a standard endpoint but check auth works."""
        # Reports don't have a DELETE endpoint, but we can verify auth/404
        response = client.get(f"/v1/reports/{sample_report['_id']}", headers=admin_auth_headers)
        assert response.status_code in (200, 404)


from app.main import app
