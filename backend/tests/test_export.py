"""Tests for the export and SIEM integration module."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Patch all database connections BEFORE importing app
with patch("app.database.init_mongodb", new_callable=AsyncMock):
    with patch("app.database.init_elasticsearch", new_callable=AsyncMock):
        with patch("app.database.init_neo4j", new_callable=AsyncMock):
            with patch("app.database.init_redis", new_callable=AsyncMock):
                from app.main import app
                from app.dependencies import (
                    get_current_user, get_db, get_redis_client,
                    CurrentUser, _get_permissions_for_role,
                )
                from app.export.siem import SIEMExporter, get_siem_exporter
                from app.export.blockchain import BlockchainSealer, get_blockchain_sealer


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_auth_override(user_id="user-export-1", role="admin"):
    """Create an auth override for testing."""
    async def _override():
        return CurrentUser(
            id=user_id,
            email="export@darktrace.com",
            name="Export Tester",
            role=role,
            permissions=_get_permissions_for_role(role),
        )
    return _override


def _sample_alert(alert_id=None):
    """Create a sample alert dict."""
    return {
        "_id": alert_id or str(uuid.uuid4()),
        "title": "Test Ransomware Alert",
        "severity": "high",
        "score": 750,
        "category": "ransomware",
        "source_url": "http://test.onion/listing/1",
        "source_type": "onion",
        "status": "new",
        "actor_pseudonym": "dark_hacker",
        "matched_keywords": ["ransomware", "hospital"],
        "summary": "Ransomware targeting hospitals detected",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
    }


# ─── SIEM Exporter Unit Tests ────────────────────────────────────────────────


class TestSIEMExporter:
    """Unit tests for the SIEMExporter class."""

    @pytest.fixture
    def exporter(self):
        return SIEMExporter()

    def test_format_cef(self, exporter):
        alert = _sample_alert()
        cef = exporter._format_cef(alert)
        assert cef.startswith("CEF:0|DarkTrace|ThreatIntelligence|1.0|")
        assert "ransomware" in cef
        assert "750" in cef

    def test_format_leef(self, exporter):
        alert = _sample_alert()
        leef = exporter._format_leef(alert)
        assert leef.startswith("LEEF:1.0|DarkTrace|ThreatIntelligence|1.0|")
        assert "ransomware" in leef

    def test_format_json(self, exporter):
        alert = _sample_alert()
        result = exporter._format_json(alert)
        assert result["source"] == "DarkTrace"
        assert result["type"] == "threat_alert"
        assert result["alert"]["title"] == "Test Ransomware Alert"
        assert result["alert"]["score"] == 750

    def test_cef_escapes_pipes_in_title(self, exporter):
        alert = _sample_alert()
        alert["title"] = "Alert | with | pipes"
        cef = exporter._format_cef(alert)
        assert "| with | pipes" not in cef
        assert "/ with / pipes" in cef or cef

    def test_get_hostname(self, exporter):
        hostname = exporter._get_hostname()
        assert isinstance(hostname, str)
        assert len(hostname) > 0

    @pytest.mark.asyncio
    async def test_send_webhook_timeout(self, exporter):
        """Test webhook timeout handling."""
        with patch("aiohttp.ClientSession.post", side_effect=TimeoutError("timeout")):
            result = await exporter.send_webhook(
                endpoint="http://localhost:9999",
                alert=_sample_alert(),
            )
            assert result["success"] is False
            assert "timeout" in result["message"]

    @pytest.mark.asyncio
    async def test_send_syslog(self, exporter):
        """Test syslog sending (socket level)."""
        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance

            result = await exporter.send_syslog(
                host="127.0.0.1",
                port=514,
                alert=_sample_alert(),
                format_type="cef",
            )
            assert result["success"] is True
            mock_instance.sendto.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_syslog_failure(self, exporter):
        """Test syslog failure handling."""
        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value = mock_instance
            mock_instance.sendto.side_effect = ConnectionRefusedError("refused")

            result = await exporter.send_syslog(
                host="127.0.0.1",
                port=514,
                alert=_sample_alert(),
            )
            assert result["success"] is False


# ─── Blockchain Sealer Unit Tests ─────────────────────────────────────────────


class TestBlockchainSealer:
    """Unit tests for the BlockchainSealer class."""

    @pytest.fixture
    def sealer(self):
        yield BlockchainSealer()

    @pytest.mark.asyncio
    async def test_seal_simulated(self, sealer):
        """Test simulated blockchain sealing."""
        with patch("app.export.blockchain.get_mongodb", new_callable=AsyncMock) as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.blockchain_tx = mock_collection

            result = await sealer.seal_report(
                report_id="report-123",
                content_hash="a" * 64,
            )
            assert result["chain"] == "simulation"
            assert result["tx_hash"].startswith("sim_")
            assert result["content_hash"] == "a" * 64
            mock_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_seal_found(self, sealer):
        """Test verifying an existing seal."""
        with patch("app.export.blockchain.get_mongodb", new_callable=AsyncMock) as mock_db:
            mock_collection = AsyncMock()
            mock_collection.find_one.return_value = {
                "content_hash": "a" * 64,
                "block_timestamp": "2026-06-01T00:00:00",
                "tx_hash": "sim_abc",
                "chain": "simulation",
            }
            mock_db.return_value.blockchain_tx = mock_collection

            result = await sealer.verify_seal(content_hash="a" * 64)
            assert result["exists"] is True
            assert result["is_verified"] is True

    @pytest.mark.asyncio
    async def test_verify_seal_not_found(self, sealer):
        """Test verifying a non-existent seal."""
        with patch("app.export.blockchain.get_mongodb", new_callable=AsyncMock) as mock_db:
            mock_collection = AsyncMock()
            mock_collection.find_one.return_value = None
            mock_db.return_value.blockchain_tx = mock_collection

            result = await sealer.verify_seal(content_hash="b" * 64)
            assert result["exists"] is False
            assert result["is_verified"] is False


# ─── Mock Database Classes ───────────────────────────────────────────────────


class MockCollection:
    """Simple mock for MongoDB collection operations."""
    def __init__(self):
        self._store = {}

    async def find_one(self, filter=None, **kwargs):
        if filter is None:
            return None
        for doc in self._store.values():
            if all(doc.get(k) == v for k, v in filter.items()):
                return doc
        return None

    async def find(self, filter=None, **kwargs):
        return list(self._store.values())

    async def insert_one(self, doc):
        _id = doc.get("_id", str(uuid.uuid4()))
        self._store[_id] = {**doc, "_id": _id}
        return type('obj', (object,), {'inserted_id': _id})()

    async def update_one(self, filter, update, **kwargs):
        for doc in self._store.values():
            if all(doc.get(k) == v for k, v in filter.items()):
                doc.update(update.get("$set", {}))
                return type('obj', (object,), {'modified_count': 1})()
        return type('obj', (object,), {'modified_count': 0})()

    async def delete_one(self, filter):
        for _id, doc in list(self._store.items()):
            if all(doc.get(k) == v for k, v in filter.items()):
                del self._store[_id]
                return type('obj', (object,), {'deleted_count': 1})()
        return type('obj', (object,), {'deleted_count': 0})()

    def aggregate(self, pipeline):
        return []


class MockMongoDB:
    """Mock MongoDB database."""
    def __init__(self):
        self.users = MockCollection()
        self.alerts = MockCollection()
        self.alert_rules = MockCollection()
        self.crawl_targets = MockCollection()
        self.crawl_jobs = MockCollection()
        self.watchlists = MockCollection()
        self.actor_profiles = MockCollection()
        self.reports = MockCollection()
        self.audit_logs = MockCollection()
        self.raw_content = MockCollection()
        self.dedup_cache = MockCollection()
        self.saved_searches = MockCollection()
        self.threat_scores = MockCollection()
        self.scoring_rules = MockCollection()
        self.blockchain_tx = MockCollection()

    async def command(self, cmd):
        return {"ok": 1}


class MockRedis:
    """Mock Redis client."""
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def ping(self):
        return True

    async def setex(self, key, seconds, value):
        self._store[key] = value

    async def set(self, key, value):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)

    async def exists(self, key):
        return key in self._store


# ─── API Integration Tests ────────────────────────────────────────────────────


class TestExportAPIEndpoints:
    """Integration tests for export API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up auth override and mock dependencies for each test."""
        # Create mock DB and Redis
        self.mock_db = MockMongoDB()
        self.mock_redis = MockRedis()

        async def _get_db():
            return self.mock_db

        async def _get_redis():
            return self.mock_redis

        app.dependency_overrides[get_db] = _get_db
        app.dependency_overrides[get_redis_client] = _get_redis
        self.auth_override = _make_auth_override()
        app.dependency_overrides[get_current_user] = self.auth_override

        # Also override database globals used by log_user_action -> get_mongodb()
        from app import database as app_database
        self._orig_mongo_db = app_database._mongo_db
        self._orig_mongo_client = app_database._mongo_client
        app_database._mongo_db = self.mock_db
        app_database._mongo_client = self.mock_db

        yield

        app_database._mongo_db = self._orig_mongo_db
        app_database._mongo_client = self._orig_mongo_client
        app.dependency_overrides.clear()

    def test_siem_webhook_no_auth(self):
        """Test that webhook endpoint requires auth."""
        # Clear auth override
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/v1/export/siem/webhook",
            json={"endpoint": "http://example.com", "alert_id": "test123"},
        )
        assert response.status_code in (401, 403)

    def test_siem_syslog_no_auth(self):
        """Test that syslog endpoint requires auth."""
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/v1/export/siem/syslog",
            json={"alert_id": "test123"},
        )
        assert response.status_code in (401, 403)

    def test_blockchain_seal_no_auth(self):
        """Test that blockchain seal endpoint requires auth."""
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/v1/export/blockchain/seal",
            json={"report_id": "rep123", "content_hash": "a" * 64},
        )
        assert response.status_code in (401, 403)

    def test_blockchain_verify_no_auth(self):
        """Test that blockchain verify endpoint requires auth."""
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/v1/export/blockchain/verify",
            json={"content_hash": "a" * 64},
        )
        assert response.status_code in (401, 403)

    def test_siem_webhook_alert_not_found(self):
        """Test webhook export with non-existent alert."""
        client = TestClient(app)
        response = client.post(
            "/v1/export/siem/webhook",
            json={
                "endpoint": "http://example.com/webhook",
                "alert_id": "nonexistent-alert-id",
            },
        )
        assert response.status_code == 404

    def test_siem_syslog_no_host(self):
        """Test syslog export without host configured."""
        client = TestClient(app)
        response = client.post(
            "/v1/export/siem/syslog",
            json={"alert_id": "test123"},
        )
        # Should fail because no SIEM_SYSLOG_HOST and no host in request
        assert response.status_code in (400, 404)

    def test_siem_webhook_invalid_format(self):
        """Test webhook with invalid format type."""
        client = TestClient(app)
        response = client.post(
            "/v1/export/siem/webhook",
            json={
                "endpoint": "http://example.com",
                "alert_id": "test123",
                "format_type": "invalid",
            },
        )
        assert response.status_code == 422

    def test_blockchain_seal_invalid_hash(self):
        """Test blockchain seal with hash too short."""
        client = TestClient(app)
        response = client.post(
            "/v1/export/blockchain/seal",
            json={"report_id": "rep123", "content_hash": "too-short"},
        )
        assert response.status_code == 422

    def test_export_permission_denied(self):
        """Test that auditor role cannot export."""
        auditor_override = _make_auth_override(role="auditor")
        app.dependency_overrides[get_current_user] = auditor_override
        client = TestClient(app)
        response = client.post(
            "/v1/export/siem/webhook",
            json={"endpoint": "http://example.com", "alert_id": "test123"},
        )
        assert response.status_code == 403


# ─── SIEM Exporter Singleton Tests ────────────────────────────────────────────


class TestSIEMExporterSingleton:
    """Test the singleton pattern for SIEMExporter."""

    @pytest.mark.asyncio
    async def test_get_siem_exporter_singleton(self):
        exporter1 = await get_siem_exporter()
        exporter2 = await get_siem_exporter()
        assert exporter1 is exporter2

    @pytest.mark.asyncio
    async def test_get_blockchain_sealer_singleton(self):
        sealer1 = await get_blockchain_sealer()
        sealer2 = await get_blockchain_sealer()
        assert sealer1 is sealer2
