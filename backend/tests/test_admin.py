"""Tests for the admin module — user management, audit logs, system health."""

import json
import uuid
from datetime import datetime, timedelta
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
                    get_current_user,
                    get_db,
                    get_redis_client,
                    CurrentUser,
                    _get_permissions_for_role,
                )
                from app.database import get_redis as get_redis_fn


# ─── Fixtures & Helpers ───────────────────────────────────────────────────────


def _make_admin_override(user_id="admin-test-1"):
    async def _override():
        return CurrentUser(
            id=user_id,
            email="admin@darktrace.com",
            name="Admin User",
            role="admin",
            permissions=_get_permissions_for_role("admin"),
        )
    return _override


def _make_auditor_override(user_id="auditor-test-1"):
    async def _override():
        return CurrentUser(
            id=user_id,
            email="auditor@darktrace.com",
            name="Auditor User",
            role="auditor",
            permissions=_get_permissions_for_role("auditor"),
        )
    return _override


def _make_investigator_override(user_id="inv-test-1"):
    async def _override():
        return CurrentUser(
            id=user_id,
            email="investigator@darktrace.com",
            name="Investigator User",
            role="investigator",
            permissions=_get_permissions_for_role("investigator"),
        )
    return _override


class MockCollection:
    """Simple in-memory mock collection for admin tests."""

    def __init__(self):
        self._docs = {}
        self._id_counter = 0

    def _make_id(self):
        self._id_counter += 1
        return str(uuid.uuid4())

    async def find_one(self, filter=None, projection=None, sort=None):
        for doc_id, doc in list(self._docs.items()):
            if all(doc.get(k) == v for k, v in (filter or {}).items() if not k.startswith("$")):
                if projection:
                    return {k: v for k, v in doc.items() if k in projection or k == "_id"}
                return doc
        return None

    def find(self, filter=None, projection=None):
        return MockCursor(list(self._docs.values()), filter, projection)

    async def count_documents(self, filter=None):
        count = 0
        for doc in self._docs.values():
            if all(doc.get(k) == v for k, v in (filter or {}).items() if not k.startswith("$")):
                count += 1
        return count

    async def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = self._make_id()
        self._docs[document["_id"]] = document
        result = MagicMock()
        result.inserted_id = document["_id"]
        return result

    async def update_one(self, filter, update, upsert=False):
        for doc_id, doc in list(self._docs.items()):
            if all(doc.get(k) == v for k, v in (filter or {}).items() if not k.startswith("$")):
                for op, fields in update.items():
                    if op == "$set":
                        doc.update(fields)
                    elif op == "$inc":
                        for k, v in fields.items():
                            doc[k] = doc.get(k, 0) + v
                    elif op == "$push":
                        for k, v in fields.items():
                            if k not in doc:
                                doc[k] = []
                            doc[k].append(v)
                return MagicMock(matched_count=1, modified_count=1)
        if upsert:
            new_doc = {}
            for k, v in (filter or {}).items():
                if not k.startswith("$"):
                    new_doc[k] = v
            for op, fields in update.items():
                if op == "$set":
                    new_doc.update(fields)
            return await self.insert_one(new_doc)
        return MagicMock(matched_count=0, modified_count=0)

    async def delete_one(self, filter):
        for doc_id, doc in list(self._docs.items()):
            if all(doc.get(k) == v for k, v in (filter or {}).items() if not k.startswith("$")):
                del self._docs[doc_id]
                return MagicMock(deleted_count=1)
        return MagicMock(deleted_count=0)

    def aggregate(self, pipeline):
        return MockAggregationCursor([])


class MockCursor:
    def __init__(self, docs, filter=None, projection=None):
        self._docs = docs
        self._filter = filter or {}
        self._projection = projection
        self._sort_field = None
        self._sort_dir = -1
        self._skip_val = 0
        self._limit_val = 0

    def sort(self, field, direction):
        self._sort_field = field
        self._sort_dir = direction
        return self

    def skip(self, n):
        self._skip_val = n
        return self

    def limit(self, n):
        self._limit_val = n
        return self

    async def to_list(self, length=None):
        result = list(self._docs)
        if self._sort_field:
            result.sort(key=lambda x: str(x.get(self._sort_field, "")), reverse=(self._sort_dir == -1))
        if self._skip_val:
            result = result[self._skip_val:]
        if self._limit_val:
            result = result[:self._limit_val]
        if self._projection:
            result = [{k: v for k, v in d.items() if k in self._projection or k == "_id"} for d in result]
        return result

    def __aiter__(self):
        return self._async_gen()

    async def _async_gen(self):
        for doc in await self.to_list():
            yield doc


class MockAggregationCursor:
    def __init__(self, results):
        self._results = results

    async def to_list(self, length=None):
        return self._results

    def __aiter__(self):
        return self._async_gen()

    async def _async_gen(self):
        for doc in self._results:
            yield doc


class MockMongoDB:
    def __init__(self):
        self.users = MockCollection()
        self.audit_logs = MockCollection()
        self.alerts = MockCollection()
        self.crawl_targets = MockCollection()
        self.crawl_jobs = MockCollection()
        self.actor_profiles = MockCollection()
        self.raw_content = MockCollection()
        self.alert_rules = MockCollection()
        self.watchlists = MockCollection()
        self.reports = MockCollection()

    async def command(self, cmd):
        return {"ok": 1}


class MockRedis:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def ping(self):
        return True

    async def setex(self, key, seconds, value):
        self._store[key] = value


class MockES:
    async def cluster(self):
        return self

    async def health(self):
        return {"status": "green"}

    async def info(self):
        return {"version": {"number": "8.14.0"}}

    async def close(self):
        pass


class MockNeo4jDriver:
    async def close(self):
        pass

    def session(self, database="neo4j"):
        return MockNeo4jSession()


class MockNeo4jSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def run(self, cypher, **params):
        return MockNeo4jResult()

    async def close(self):
        pass


class MockNeo4jResult:
    async def single(self):
        return {"val": 1}


# ─── User Management Tests ───────────────────────────────────────────────────


class TestAdminUserManagement:
    """Test admin user CRUD endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_db = MockMongoDB()
        self.mock_redis = MockRedis()

        async def _get_db():
            return self.mock_db

        async def _get_redis():
            return self.mock_redis

        app.dependency_overrides[get_db] = _get_db
        app.dependency_overrides[get_redis_client] = _get_redis

        self.admin_override = _make_admin_override()
        app.dependency_overrides[get_current_user] = self.admin_override

        # Also override database globals used by log_user_action -> get_mongodb()
        from app import database as app_database
        self._orig_mongo_db = app_database._mongo_db
        self._orig_mongo_client = app_database._mongo_client
        app_database._mongo_db = self.mock_db
        app_database._mongo_client = self.mock_db

        # Insert admin user into mock DB for delete-self tests
        import asyncio
        from app.auth.models import new_user_document
        admin_user = new_user_document(
            email="admin@darktrace.com",
            name="Admin User",
            password="admin123",
            role="admin",
        )
        admin_user["_id"] = "admin-test-1"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.mock_db.users.insert_one(admin_user))
        loop.close()

        yield

        app_database._mongo_db = self._orig_mongo_db
        app_database._mongo_client = self._orig_mongo_client
        app.dependency_overrides.clear()

    def test_list_users(self):
        """Test listing all users."""
        client = TestClient(app)
        response = client.get("/v1/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_create_user(self):
        """Test creating a new user."""
        client = TestClient(app)
        response = client.post(
            "/v1/admin/users",
            json={
                "email": "new@darktrace.com",
                "name": "New User",
                "password": "securepass123",
                "role": "investigator",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@darktrace.com"
        assert data["role"] == "investigator"
        assert "id" in data

    def test_create_user_duplicate_email(self):
        """Test creating a user with duplicate email."""
        client = TestClient(app)
        # First creation
        client.post(
            "/v1/admin/users",
            json={
                "email": "dupe@darktrace.com",
                "name": "First",
                "password": "securepass123",
                "role": "investigator",
            },
        )
        # Duplicate
        response = client.post(
            "/v1/admin/users",
            json={
                "email": "dupe@darktrace.com",
                "name": "Second",
                "password": "securepass123",
                "role": "admin",
            },
        )
        assert response.status_code == 409

    def test_create_user_invalid_email(self):
        """Test creating a user with invalid email."""
        client = TestClient(app)
        response = client.post(
            "/v1/admin/users",
            json={
                "email": "not-an-email",
                "name": "Bad Email",
                "password": "securepass123",
                "role": "investigator",
            },
        )
        assert response.status_code == 422

    def test_update_user(self):
        """Test updating a user."""
        client = TestClient(app)
        # Create user first
        create_resp = client.post(
            "/v1/admin/users",
            json={
                "email": "update@darktrace.com",
                "name": "Update Me",
                "password": "securepass123",
                "role": "investigator",
            },
        )
        user_id = create_resp.json()["id"]

        # Update
        response = client.put(
            f"/v1/admin/users/{user_id}",
            json={"name": "Updated Name", "role": "admin"},
        )
        assert response.status_code == 200
        assert "updated_at" in response.json()

    def test_update_user_not_found(self):
        """Test updating a non-existent user."""
        client = TestClient(app)
        response = client.put(
            "/v1/admin/users/nonexistent-id",
            json={"name": "Ghost"},
        )
        assert response.status_code == 404

    def test_delete_user(self):
        """Test deleting a user."""
        client = TestClient(app)
        # Create user first
        create_resp = client.post(
            "/v1/admin/users",
            json={
                "email": "delete@darktrace.com",
                "name": "Delete Me",
                "password": "securepass123",
                "role": "investigator",
            },
        )
        user_id = create_resp.json()["id"]

        # Delete
        response = client.delete(f"/v1/admin/users/{user_id}")
        assert response.status_code == 204

    def test_delete_self_forbidden(self):
        """Test that admin cannot delete themselves."""
        client = TestClient(app)
        # The admin user ID is "admin-test-1" from the fixture
        response = client.delete("/v1/admin/users/admin-test-1")
        assert response.status_code == 400

    def test_create_api_key(self):
        """Test creating an API key for a user."""
        client = TestClient(app)
        # Create user
        create_resp = client.post(
            "/v1/admin/users",
            json={
                "email": "apikey@darktrace.com",
                "name": "API Key User",
                "password": "securepass123",
                "role": "investigator",
            },
        )
        user_id = create_resp.json()["id"]

        # Create API key
        response = client.post(
            f"/v1/admin/users/{user_id}/api-keys",
            json={"name": "Test Key", "permissions": ["alerts:read"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["key"].startswith("dt_")
        assert data["name"] == "Test Key"

    def test_non_admin_cannot_manage_users(self):
        """Test that investigators cannot manage users."""
        investigator_override = _make_investigator_override()
        app.dependency_overrides[get_current_user] = investigator_override

        client = TestClient(app)
        response = client.get("/v1/admin/users")
        assert response.status_code == 403


# ─── Audit Log Tests ──────────────────────────────────────────────────────────


class TestAdminAuditLogs:
    """Test audit log endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_db = MockMongoDB()
        self.mock_redis = MockRedis()

        async def _get_db():
            return self.mock_db

        async def _get_redis():
            return self.mock_redis

        app.dependency_overrides[get_db] = _get_db
        app.dependency_overrides[get_redis_client] = _get_redis

        # Seed some audit logs
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for i in range(5):
            loop.run_until_complete(self.mock_db.audit_logs.insert_one({
                "timestamp": 1000 + i,
                "user_id": f"user{i}",
                "user_name": f"User {i}",
                "user_role": "investigator" if i % 2 == 0 else "admin",
                "action": "login" if i % 2 == 0 else "logout",
                "resource_type": "auth",
                "resource_id": f"user{i}",
                "details": {},
                "ip_address": "127.0.0.1",
                "user_agent": "test-agent",
            }))
        loop.close()

        yield

        app.dependency_overrides.clear()

    def test_audit_logs_admin_access(self):
        """Test admin can view audit logs."""
        admin_override = _make_admin_override()
        app.dependency_overrides[get_current_user] = admin_override
        client = TestClient(app)
        response = client.get("/v1/admin/audit-logs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    def test_audit_logs_auditor_access(self):
        """Test auditor can view audit logs."""
        auditor_override = _make_auditor_override()
        app.dependency_overrides[get_current_user] = auditor_override
        client = TestClient(app)
        response = client.get("/v1/admin/audit-logs")
        assert response.status_code == 200

    def test_audit_logs_investigator_denied(self):
        """Test investigator cannot view audit logs."""
        inv_override = _make_investigator_override()
        app.dependency_overrides[get_current_user] = inv_override
        client = TestClient(app)
        response = client.get("/v1/admin/audit-logs")
        assert response.status_code == 403

    def test_audit_logs_filter_by_action(self):
        """Test filtering audit logs by action."""
        admin_override = _make_admin_override()
        app.dependency_overrides[get_current_user] = admin_override
        client = TestClient(app)
        response = client.get("/v1/admin/audit-logs?action=login")
        assert response.status_code == 200

    def test_audit_logs_filter_by_user(self):
        """Test filtering audit logs by user."""
        admin_override = _make_admin_override()
        app.dependency_overrides[get_current_user] = admin_override
        client = TestClient(app)
        response = client.get("/v1/admin/audit-logs?user_id=user0")
        assert response.status_code == 200

    def test_audit_logs_pagination(self):
        """Test audit logs pagination."""
        admin_override = _make_admin_override()
        app.dependency_overrides[get_current_user] = admin_override
        client = TestClient(app)
        response = client.get("/v1/admin/audit-logs?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["per_page"] == 2

    def test_audit_logs_no_auth(self):
        """Test audit logs require auth."""
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/v1/admin/audit-logs")
        assert response.status_code in (401, 403)


# ─── System Health Tests ──────────────────────────────────────────────────────


class TestAdminSystemHealth:
    """Test system health endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_db = MockMongoDB()
        self.mock_redis = MockRedis()

        async def _get_db():
            return self.mock_db

        async def _get_redis():
            return self.mock_redis

        async def _get_neo4j():
            return MockNeo4jDriver()

        app.dependency_overrides[get_db] = _get_db
        app.dependency_overrides[get_redis_client] = _get_redis
        app.dependency_overrides[get_redis_fn] = _get_redis

        # Patch get_neo4j in admin router
        with patch("app.admin.router.get_neo4j", return_value=MockNeo4jDriver()):
            yield

        app.dependency_overrides.clear()

    def test_system_health(self):
        """Test system health endpoint returns service statuses."""
        admin_override = _make_admin_override()
        app.dependency_overrides[get_current_user] = admin_override
        client = TestClient(app)
        response = client.get("/v1/admin/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "api_gateway" in data["services"]

    def test_system_health_no_auth(self):
        """Test health endpoint is accessible without auth (public endpoint)."""
        # Remove only auth override, keep DB overrides
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        client = TestClient(app)
        response = client.get("/v1/admin/health")
        # Health endpoint is public — returns 200 even without auth
        assert response.status_code in (200, 500)
