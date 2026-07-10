"""Pytest fixtures for DarkTrace backend tests."""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set TESTING flag BEFORE importing app
import os
os.environ["TESTING"] = "true"

# ─── Helper: concrete async mock classes for Python 3.12+ ───────────


class _MockNeo4jResult:
    """Concrete mock for Neo4j query result (works with async for and await)."""

    def __init__(self, records=None):
        self._records = records or []
        self._index = 0

    async def single(self):
        return self._records[0] if self._records else None

    def __aiter__(self):
        return self._async_gen()

    async def _async_gen(self):
        for r in self._records:
            yield r


class _MockNeo4jSession:
    """Concrete mock for Neo4j session that works with async with."""

    def __init__(self):
        self._result = _MockNeo4jResult()

    async def run(self, cypher, **params):
        return self._result

    async def close(self):
        pass


class _MockNeo4jAsyncContextManager:
    """Async context manager that returns a mock session."""

    def __init__(self, session=None):
        self._session = session or _MockNeo4jSession()

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *args):
        pass


class _MockNeo4jDriver:
    """Concrete mock for Neo4j driver."""

    def __init__(self):
        self._session = _MockNeo4jSession()

    def session(self, database="neo4j"):
        return _MockNeo4jAsyncContextManager(self._session)

    async def close(self):
        pass


# Patch all database connections BEFORE importing app
with patch("app.database.init_mongodb", new_callable=AsyncMock):
    with patch("app.database.init_elasticsearch", new_callable=AsyncMock):
        with patch("app.database.init_redis", new_callable=AsyncMock):

            # For Neo4j, use concrete mock classes that work with Python 3.12+
            _mock_neo4j_driver = _MockNeo4jDriver()

            async def _mock_init_neo4j():
                return _mock_neo4j_driver

            async def _mock_get_neo4j():
                return _mock_neo4j_driver

            with patch("app.database.init_neo4j", side_effect=_mock_init_neo4j):
                with patch("app.database.get_neo4j", side_effect=_mock_get_neo4j):
                    from app.main import app
                    from app.dependencies import get_db, get_es, get_redis_client, get_neo4j_db, CurrentUser
                    from app.auth.jwt import create_access_token


# ─── Mock Collections ─────────────────────────────────────────────────────────


class MockCollection:
    """In-memory mock for MongoDB collections."""

    def __init__(self):
        self._docs: Dict[str, dict] = {}
        self._id_counter = 0

    def _make_id(self) -> str:
        self._id_counter += 1
        return str(uuid.uuid4())

    async def find_one(self, filter: dict, projection: Optional[dict] = None, sort: Optional[list] = None):
        for doc in self._docs.values():
            if self._matches(doc, filter):
                if projection:
                    return {k: v for k, v in doc.items() if k in projection or k == "_id"}
                return doc
        return None

    def find(self, filter: dict = None, projection: Optional[dict] = None):
        return MockCursor(self._docs, filter, projection, self)

    async def count_documents(self, filter: dict = None) -> int:
        count = 0
        for doc in self._docs.values():
            if self._matches(doc, filter):
                count += 1
        return count

    async def insert_one(self, document: dict):
        if "_id" not in document:
            document["_id"] = self._make_id()
        self._docs[document["_id"]] = document
        result = MagicMock()
        result.inserted_id = document["_id"]
        return result

    async def update_one(self, filter: dict, update: dict, upsert: bool = False):
        for doc_id, doc in self._docs.items():
            if self._matches(doc, filter):
                self._apply_update(doc, update)
                result = MagicMock()
                result.modified_count = 1
                result.matched_count = 1
                return result
        if upsert:
            new_doc = {k.replace("$", ""): v for k, v in filter.items()}
            for op, fields in update.items():
                if op.startswith("$"):
                    for fk, fv in fields.items():
                        new_doc[fk] = fv
            await self.insert_one(new_doc)
        result = MagicMock()
        result.modified_count = 0
        result.matched_count = 0
        return result

    async def update_many(self, filter: dict, update: dict):
        count = 0
        for doc_id, doc in self._docs.items():
            if self._matches(doc, filter):
                self._apply_update(doc, update)
                count += 1
        result = MagicMock()
        result.modified_count = count
        return result

    async def delete_one(self, filter: dict):
        for doc_id, doc in list(self._docs.items()):
            if self._matches(doc, filter):
                del self._docs[doc_id]
                return MagicMock(deleted_count=1)
        return MagicMock(deleted_count=0)

    async def delete_many(self, filter: dict = None):
        to_delete = []
        for doc_id, doc in self._docs.items():
            if self._matches(doc, filter):
                to_delete.append(doc_id)
        for doc_id in to_delete:
            del self._docs[doc_id]
        result = MagicMock()
        result.deleted_count = len(to_delete)
        return result

    def aggregate(self, pipeline: List[dict]):
        return MockAggregationCursor(self._docs, pipeline)

    def _matches(self, doc: dict, filter: dict = None) -> bool:
        if not filter:
            return True
        for key, value in filter.items():
            if key == "_id":
                if str(doc.get("_id")) != str(value):
                    return False
            elif key.startswith("$"):
                continue
            elif isinstance(value, dict):
                if "$gte" in value or "$lte" in value or "$gt" in value or "$lt" in value:
                    doc_val = doc.get(key)
                    if doc_val is None:
                        return False
                    if "$gte" in value and not (doc_val >= value["$gte"] if hasattr(doc_val, '__ge__') else False if isinstance(value["$gte"], (datetime, int, float)) and isinstance(doc_val, (datetime, int, float)) else str(doc_val) >= str(value["$gte"])):
                        return False
                    # Simplified: just check isinstance
                    if "$gte" in value:
                        try:
                            if doc_val < value["$gte"]:
                                return False
                        except (TypeError, ValueError):
                            if str(doc_val) < str(value["$gte"]):
                                return False
                    if "$lte" in value:
                        try:
                            if doc_val > value["$lte"]:
                                return False
                        except (TypeError, ValueError):
                            if str(doc_val) > str(value["$lte"]):
                                return False
                elif "$in" in value:
                    if doc.get(key) not in value["$in"]:
                        return False
                elif "$ne" in value:
                    if doc.get(key) == value["$ne"]:
                        return False
                else:
                    # Nested field matching (e.g., {"refresh_tokens.token_hash": hash})
                    sub_key = list(value.keys())[0] if value else None
                    if sub_key:
                        sub_value = value[sub_key]
                        doc_arr = doc.get(key, [])
                        if isinstance(doc_arr, list):
                            found = False
                            for item in doc_arr:
                                if isinstance(item, dict) and item.get(sub_key) == sub_value:
                                    found = True
                                    break
                            if not found:
                                return False
            else:
                if doc.get(key) != value:
                    return False
        return True

    def _apply_update(self, doc: dict, update: dict):
        for op, fields in update.items():
            if op == "$set":
                for k, v in fields.items():
                    doc[k] = v
            elif op == "$inc":
                for k, v in fields.items():
                    doc[k] = doc.get(k, 0) + v
            elif op == "$push":
                for k, v in fields.items():
                    if k not in doc:
                        doc[k] = []
                    if isinstance(v, dict) and "$each" in v:
                        doc[k] = v["$each"] + doc[k]
                        if "$slice" in v and v["$slice"] > 0:
                            doc[k] = doc[k][:v["$slice"]]
                    else:
                        doc[k].append(v)
            elif op == "$pull":
                for k, v in fields.items():
                    if k in doc and isinstance(doc[k], list):
                        doc[k] = [item for item in doc[k] if item != v]
            elif op == "$addToSet":
                for k, v in fields.items():
                    if k not in doc:
                        doc[k] = []
                    if isinstance(v, list):
                        for item in v:
                            if item not in doc[k]:
                                doc[k].append(item)
                    elif v not in doc[k]:
                        doc[k].append(v)
        doc["_id"] = doc.get("_id", self._make_id())


class MockCursor:
    """Mock for MongoDB async cursor."""

    def __init__(self, docs: dict, filter: dict, projection: Optional[dict], collection: MockCollection):
        self._docs = docs
        self._filter = filter
        self._projection = projection
        self._collection = collection
        self._skip_val = 0
        self._limit_val = 0
        self._sort_field = None
        self._sort_dir = -1

    def sort(self, field: str, direction: int):
        self._sort_field = field
        self._sort_dir = direction
        return self

    def skip(self, n: int):
        self._skip_val = n
        return self

    def limit(self, n: int):
        self._limit_val = n
        return self

    async def to_list(self, length: Optional[int] = None):
        matching = [doc for doc in self._docs.values() if self._collection._matches(doc, self._filter)]

        if self._sort_field:
            def sort_key(d):
                val = d.get(self._sort_field)
                if val is None:
                    return ""
                if hasattr(val, 'timestamp'):
                    return val.timestamp()
                return str(val) if not isinstance(val, (int, float)) else val
            matching.sort(key=sort_key, reverse=(self._sort_dir == -1))

        if self._skip_val:
            matching = matching[self._skip_val:]
        if self._limit_val:
            matching = matching[:self._limit_val]

        if self._projection:
            matching = [
                {k: v for k, v in d.items() if k in self._projection or k == "_id"}
                for d in matching
            ]
        return matching

    def __aiter__(self):
        return self._async_generator()

    async def _async_generator(self):
        for doc in await self.to_list():
            yield doc


class MockAggregationCursor:
    """Mock for MongoDB aggregation cursor."""

    def __init__(self, docs: dict, pipeline: List[dict]):
        self._docs = docs
        self._pipeline = pipeline
        self._results = None

    async def to_list(self, length=None):
        if self._results is not None:
            return self._results

        # Simple aggregation: $match + $group + $sort + $limit
        data = list(self._docs.values())
        result = []

        for stage in self._pipeline:
            if "$match" in stage:
                match_filter = stage["$match"]
                # Dummy match - accept all for mock
                data = [d for d in data if all(k in d or k.startswith("$") for k in match_filter)]
            elif "$group" in stage:
                group_id = stage["$group"]["_id"]
                accumulators = {k: v for k, v in stage["$group"].items() if k != "_id"}

                groups = {}
                for d in data:
                    if group_id == "$severity" or group_id == "$category" or group_id == "$status":
                        key = d.get(group_id.replace("$", ""), "unknown")
                    elif isinstance(group_id, dict) and "$dateToString" in group_id:
                        date_field = group_id["$dateToString"]["date"].replace("$", "")
                        dt = d.get(date_field, datetime.now(timezone.utc))
                        key = dt.isoformat()[:10] if hasattr(dt, 'isoformat') else str(dt)[:10]
                    else:
                        key = "all"

                    if key not in groups:
                        groups[key] = {"_id": key}
                        for acc_key, acc_val in accumulators.items():
                            if acc_val.get("$sum") == 1:
                                groups[key][acc_key] = 0
                            elif "$sum" in acc_val:
                                groups[key][acc_key] = 0
                            elif "$cond" in acc_val:
                                groups[key][acc_key] = 0

                    for acc_key, acc_val in accumulators.items():
                        if isinstance(acc_val, dict) and "$sum" in acc_val:
                            sum_val = acc_val["$sum"]
                            if isinstance(sum_val, dict):
                                # Handle $cond inside $sum
                                if "$cond" in sum_val:
                                    condition = sum_val["$cond"]
                                    if isinstance(condition, list) and len(condition) >= 2:
                                        if isinstance(condition[1], dict) and "$eq" in condition[1]:
                                            if_eq = condition[1]["$eq"]
                                            if isinstance(if_eq, list) and len(if_eq) >= 2:
                                                lhs_field = if_eq[0].replace("$", "")
                                                rhs_val = if_eq[1]
                                                if d.get(lhs_field) == rhs_val:
                                                    groups[key][acc_key] += 1
                            elif sum_val == 1:
                                groups[key][acc_key] += 1
                            elif isinstance(sum_val, str):
                                field_ref = sum_val.replace("$", "")
                                groups[key][acc_key] += d.get(field_ref, 0) if isinstance(d.get(field_ref), (int, float)) else 0
                        elif "$cond" in acc_val:
                            condition = acc_val["$cond"]
                            if_eq = condition[1]["$eq"] if isinstance(condition[1], dict) and "$eq" in condition[1] else None
                            if if_eq:
                                lhs_field = if_eq[0].replace("$", "")
                                rhs_val = if_eq[1]
                                if d.get(lhs_field) == rhs_val:
                                    groups[key][acc_key] += 1

                result = list(groups.values())

            elif "$sort" in stage:
                sort_field = list(stage["$sort"].keys())[0]
                sort_dir = stage["$sort"][sort_field]
                result.sort(key=lambda x: str(x.get(sort_field, "")), reverse=(sort_dir == -1))

            elif "$limit" in stage:
                result = result[:stage["$limit"]]

        self._results = result
        return result

    def __aiter__(self):
        return self._async_generator()

    async def _async_generator(self):
        for doc in await self.to_list():
            yield doc


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

    async def command(self, cmd):
        return {"ok": 1}


class MockElasticsearch:
    """Mock Elasticsearch client."""

    def __init__(self):
        self.indices = MockESIndices()
        self._docs = {}

    async def info(self):
        return {"version": {"number": "8.14.0"}}

    async def search(self, index="", body=None, **kwargs):
        return {
            "hits": {
                "total": {"value": 0},
                "hits": [],
            },
            "aggregations": {
                "categories": {"buckets": []},
                "source_types": {"buckets": []},
                "languages": {"buckets": []},
            },
        }

    async def index(self, index="", id="", body=None, **kwargs):
        self._docs[id] = body
        return {"_id": id, "result": "created"}

    async def update(self, index="", id="", body=None, **kwargs):
        if id in self._docs:
            self._docs[id].update(body.get("doc", {}))
        return {"_id": id, "result": "updated"}

    async def close(self):
        pass


class MockESIndices:
    async def create(self, *args, **kwargs):
        return {"acknowledged": True}


class MockRedis:
    """Mock Redis client."""

    def __init__(self):
        self._store = {}
        self._expiry = {}

    async def get(self, key):
        self._purge_expired()
        return self._store.get(key)

    async def setex(self, key, seconds, value):
        self._store[key] = value
        self._expiry[key] = time.time() + seconds

    async def set(self, key, value):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)
        self._expiry.pop(key, None)

    async def ping(self):
        return True

    async def close(self):
        pass

    def pipeline(self):
        return MockRedisPipeline(self)

    def _purge_expired(self):
        now = time.time()
        expired = [k for k, v in self._expiry.items() if v <= now]
        for k in expired:
            self._store.pop(k, None)
            self._expiry.pop(k, None)


class MockRedisPipeline:
    def __init__(self, redis):
        self._redis = redis
        self._commands = []

    def zremrangebyscore(self, key, min_val, max_val):
        self._commands.append(("zremrangebyscore", key, min_val, max_val))
        return self

    def zcard(self, key):
        self._commands.append(("zcard", key))
        return self

    def zadd(self, key, mapping):
        self._commands.append(("zadd", key, mapping))
        return self

    def expire(self, key, seconds):
        self._commands.append(("expire", key, seconds))
        return self

    async def execute(self):
        results = []
        for cmd in self._commands:
            if cmd[0] == "zcard":
                results.append(0)
            elif cmd[0] == "zremrangebyscore":
                results.append(0)
            elif cmd[0] == "zadd":
                results.append(1)
            elif cmd[0] == "expire":
                results.append(True)
            else:
                results.append(None)
        return results


class MockNeo4jResult:
    """Mock Neo4j query result that works with async/await in Python 3.12+."""

    def __init__(self, records=None):
        self._records = records or []

    async def single(self):
        return self._records[0] if self._records else None

    def __aiter__(self):
        return self._async_gen()

    async def _async_gen(self):
        for r in self._records:
            yield r


class MockNeo4jSession:
    """Mock Neo4j session that works with async context manager protocol."""

    def __init__(self, result=None):
        self._result = result or MockNeo4jResult()

    async def run(self, cypher, **params):
        return self._result

    async def close(self):
        pass


class MockNeo4jAsyncCtx:
    """Async context manager wrapper for Neo4j sessions."""

    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *args):
        pass


class MockNeo4jDriver:
    """Mock Neo4j driver."""

    def __init__(self):
        self._default_session = MockNeo4jSession()

    async def close(self):
        pass

    def session(self, database="neo4j"):
        return MockNeo4jAsyncCtx(self._default_session)


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_mongodb():
    """Create a fresh mock MongoDB for each test."""
    return MockMongoDB()


@pytest.fixture
def mock_es():
    """Create a mock Elasticsearch client."""
    return MockElasticsearch()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    return MockRedis()


@pytest.fixture
def mock_neo4j():
    """Create a mock Neo4j driver."""
    return MockNeo4jDriver()


@pytest.fixture
def override_deps(mock_mongodb, mock_es, mock_redis, mock_neo4j):
    """Override FastAPI dependencies with mocks."""

    async def _get_db_override():
        return mock_mongodb

    async def _get_es_override():
        return mock_es

    async def _get_redis_override():
        return mock_redis

    async def _get_neo4j_override():
        return mock_neo4j

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_es] = _get_es_override
    app.dependency_overrides[get_redis_client] = _get_redis_override
    app.dependency_overrides[get_neo4j_db] = _get_neo4j_override

    # Also ensure app.database globals point to our mocks so that
    # log_user_action() -> get_mongodb() returns our mock MongoDB
    from app import database as app_database
    app_database._mongo_db = mock_mongodb
    app_database._mongo_client = mock_mongodb
    app_database._es_client = mock_es
    app_database._redis_client = mock_redis
    app_database._neo4j_driver = mock_neo4j

    yield

    app.dependency_overrides.clear()
    # Reset database globals to None so subsequent tests get fresh state
    app_database._mongo_db = None
    app_database._mongo_client = None
    app_database._es_client = None
    app_database._redis_client = None
    app_database._neo4j_driver = None


@pytest.fixture
def client(override_deps):
    """Create a FastAPI TestClient with overridden dependencies."""
    with TestClient(app) as c:
        yield c


def make_current_user_override(user_id="user123", email="test@test.com", name="Test User",
                                role="admin", permissions=None):
    """Create an override for get_current_user dependency."""
    if permissions is None:
        from app.dependencies import _get_permissions_for_role
        permissions = _get_permissions_for_role(role)

    current_user = CurrentUser(
        id=user_id,
        email=email,
        name=name,
        role=role,
        permissions=permissions,
    )

    async def _override():
        return current_user

    return _override, current_user


@pytest.fixture
def auth_headers(client, mock_mongodb):
    """Create authentication headers with a valid JWT."""
    from app.dependencies import get_current_user

    # Create a user in mock DB
    from app.auth.models import new_user_document
    user_doc = new_user_document(
        email="admin@darktrace.com",
        name="Admin",
        password="admin123",
        role="admin",
    )
    # Store the user_id for token creation
    user_id = user_doc["_id"]

    # Add a user document that the get_current_user dependency will find
    async def _setup_user():
        await mock_mongodb.users.insert_one(user_doc)
        return user_doc

    # Run insertion
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_setup_user())
    loop.close()

    # Create token
    token = create_access_token(user_id, "admin@darktrace.com", "admin")

    # Override the get_current_user dependency to resolve properly
    from app.dependencies import get_current_user
    from app.dependencies import _get_permissions_for_role

    async def _auth_override():
        return CurrentUser(
            id=user_id,
            email="admin@darktrace.com",
            name="Admin",
            role="admin",
            permissions=_get_permissions_for_role("admin"),
        )

    app.dependency_overrides[get_current_user] = _auth_override

    return {"Authorization": f"Bearer {token}", "X-Request-ID": "test-req-123"}


@pytest.fixture
def admin_auth_headers(client, mock_mongodb):
    """Fixture for admin auth headers with full permissions."""
    # Use auth_headers logic inline
    from app.dependencies import get_current_user, _get_permissions_for_role
    from app.auth.models import new_user_document
    import asyncio

    user_doc = new_user_document(
        email="admin@darktrace.com",
        name="Admin User",
        password="admin123",
        role="admin",
    )
    user_id = user_doc["_id"]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mock_mongodb.users.insert_one(user_doc))
    loop.close()

    token = create_access_token(user_id, "admin@darktrace.com", "admin")

    async def _auth_override():
        return CurrentUser(
            id=user_id,
            email="admin@darktrace.com",
            name="Admin User",
            role="admin",
            permissions=_get_permissions_for_role("admin"),
        )

    app.dependency_overrides[get_current_user] = _auth_override

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_auth_headers(client, mock_mongodb):
    """Fixture for viewer (non-admin) auth headers with limited permissions."""
    from app.dependencies import get_current_user, _get_permissions_for_role
    from app.auth.models import new_user_document
    import asyncio

    user_doc = new_user_document(
        email="viewer@darktrace.com",
        name="Viewer User",
        password="viewer123",
        role="viewer",
    )
    user_id = user_doc["_id"]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mock_mongodb.users.insert_one(user_doc))
    loop.close()

    token = create_access_token(user_id, "viewer@darktrace.com", "viewer")

    async def _auth_override():
        return CurrentUser(
            id=user_id,
            email="viewer@darktrace.com",
            name="Viewer User",
            role="viewer",
            permissions=_get_permissions_for_role("viewer"),
        )

    app.dependency_overrides[get_current_user] = _auth_override

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_alert(mock_mongodb):
    """Create a sample alert in the mock database."""
    from app.alerts.models import new_alert_document
    alert = new_alert_document(
        title="Test Ransomware Alert",
        severity="high",
        score=750,
        category="ransomware",
        source_url="http://test.onion/listing/1",
        source_type="onion",
        content_id="content123",
        matched_keywords=["ransomware", "hospital"],
        summary="Ransomware targeting hospitals detected",
    )
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mock_mongodb.alerts.insert_one(alert))
    loop.close()
    return alert


@pytest.fixture
def sample_crawl_target(mock_mongodb):
    """Create a sample crawl target."""
    target = {
        "_id": str(uuid.uuid4()),
        "url": "http://test.onion/market",
        "site_name": "TestMarket",
        "source_type": "onion",
        "status": "active",
        "crawl_frequency": "every_6h",
        "parser_type": "generic",
        "notes": "Test target",
        "tags": ["ransomware"],
        "added_by": "user123",
        "added_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "politeness_config": {"crawl_delay": 5.0, "max_concurrent": 4, "max_depth": 2},
    }
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mock_mongodb.crawl_targets.insert_one(target))
    loop.close()
    return target


@pytest.fixture
def sample_watchlist(mock_mongodb):
    """Create a sample watchlist."""
    from app.watchlists.models import WatchlistCreate, RegexPattern, new_watchlist_document
    body = WatchlistCreate(
        name="Ransomware Watchlist",
        description="Track ransomware keywords",
        keywords=["ransomware", "lockbit", "blackcat"],
        regex_patterns=[RegexPattern(pattern=r"\b[A-Z]{5}\d{4}[A-Z]\b", label="PAN")],
        entities=["btc_addresses"],
        severity_boost=200,
    )
    doc = new_watchlist_document(body, "user123")
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mock_mongodb.watchlists.insert_one(doc))
    loop.close()
    return doc


@pytest.fixture
def sample_actor(mock_mongodb):
    """Create a sample actor profile."""
    actor = {
        "_id": str(uuid.uuid4()),
        "pseudonyms": ["dark_hacker", "ghost"],
        "risk_score": 650,
        "first_seen": datetime.now(timezone.utc) - timedelta(days=30),
        "last_seen": datetime.now(timezone.utc),
        "total_posts": 42,
        "active_platforms": ["DarkMarket", "AlphaBay"],
        "linked_entities": {
            "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
            "emails": ["dark@protonmail.com"],
        },
        "top_categories": ["ransomware", "exploit"],
        "recent_activity": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mock_mongodb.actor_profiles.insert_one(actor))
    loop.close()
    return actor


@pytest.fixture
def sample_report(mock_mongodb):
    """Create a sample report document."""
    report = {
        "_id": str(uuid.uuid4()),
        "type": "alert_report",
        "format": "pdf",
        "status": "completed",
        "parameters": {"alert_id": "alert123"},
        "file_path": None,
        "file_size_bytes": 1024,
        "content_hash": "abc123",
        "download_token": "tok_abc123",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
        "download_count": 0,
        "created_by": "user123",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mock_mongodb.reports.insert_one(report))
    loop.close()
    return report
