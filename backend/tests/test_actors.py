"""Tests for actors module — unit and API endpoint tests."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


# ─── Unit Tests ───────────────────────────────────────────────────────────────


class _MockNeo4jResult:
    """Concrete mock for Neo4j result (async-await compatible, Python 3.12+)."""

    def __init__(self, records=None):
        self._records = records or []

    async def single(self):
        return self._records[0] if self._records else None

    def __aiter__(self):
        return self._async_gen()

    async def _async_gen(self):
        for r in self._records:
            yield r


class _MockNeo4jSession:
    """Concrete mock for Neo4j session."""

    def __init__(self, result=None):
        self._result = result or _MockNeo4jResult()

    async def run(self, cypher, **params):
        return self._result

    async def close(self):
        pass


class _MockNeo4jAsyncCtx:
    """Async context manager wrapping a mock session."""

    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *args):
        pass


class _MockNeo4jDriver:
    """Concrete mock for Neo4j driver."""

    def __init__(self, session=None):
        self._session = session or _MockNeo4jSession()

    def session(self, database="neo4j"):
        return _MockNeo4jAsyncCtx(self._session)

    async def close(self):
        pass


class TestActorGraph:
    """Unit tests for ActorGraph with mocked Neo4j."""

    @pytest.fixture
    def mock_neo4j_session(self):
        """Create a mock Neo4j session that returns empty results."""
        return _MockNeo4jSession()

    @pytest.fixture
    def mock_neo4j_driver(self, mock_neo4j_session):
        """Create a mock Neo4j driver."""
        return _MockNeo4jDriver(mock_neo4j_session)

    @pytest.fixture
    def mock_get_neo4j(self, mock_neo4j_driver):
        """Patch get_neo4j in the actors.graph module."""
        with patch("app.actors.graph.get_neo4j") as mock:
            mock.return_value = mock_neo4j_driver
            yield mock

    @pytest.mark.asyncio
    async def test_search_actors_empty(self, mock_get_neo4j):
        """Test actor search returns empty result when no actors exist."""
        from app.actors.graph import ActorGraph
        graph = ActorGraph()
        result = await graph.search_actors(search_term="test")
        assert "data" in result
        assert "pagination" in result
        assert result["data"] == []
        assert result["pagination"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_actor_profile_nonexistent(self, mock_get_neo4j):
        """Test getting profile for non-existent actor."""
        from app.actors.graph import ActorGraph
        graph = ActorGraph()
        profile = await graph.get_actor_profile("nonexistent")
        assert profile is None

    @pytest.mark.asyncio
    async def test_get_actor_network_graph(self, mock_get_neo4j):
        """Test getting actor network graph returns structure."""
        from app.actors.graph import ActorGraph
        graph = ActorGraph()
        result = await graph.get_actor_network_graph("actor1", max_hops=2)
        assert "nodes" in result
        assert "edges" in result

    @pytest.mark.asyncio
    async def test_create_or_update_actor(self, mock_get_neo4j):
        """Test creating an actor returns a UUID."""
        from app.actors.graph import ActorGraph
        graph = ActorGraph()
        result = await graph.create_or_update_actor({
            "uuid": "test-uuid-123",
            "risk_score": 75,
        })
        assert result is not None

    @pytest.mark.asyncio
    async def test_link_pseudonym(self, mock_get_neo4j):
        """Test linking a pseudonym doesn't raise errors."""
        from app.actors.graph import ActorGraph
        graph = ActorGraph()
        # Should not raise
        await graph.link_pseudonym("actor-uuid", "darkuser", "onion_site", 0.9)

    @pytest.mark.asyncio
    async def test_link_entity(self, mock_get_neo4j):
        """Test linking an entity doesn't raise errors."""
        from app.actors.graph import ActorGraph
        graph = ActorGraph()
        await graph.link_entity("darkuser", "btc_address", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

    @pytest.mark.asyncio
    async def test_link_content(self, mock_get_neo4j):
        """Test linking content doesn't raise errors."""
        from app.actors.graph import ActorGraph
        graph = ActorGraph()
        await graph.link_content("actor-uuid", "content-123", "onion_site")

    @pytest.mark.asyncio
    async def test_link_actor_to_site(self, mock_get_neo4j):
        """Test linking actor to site doesn't raise errors."""
        from app.actors.graph import ActorGraph
        graph = ActorGraph()
        await graph.link_actor_to_site("actor-uuid", "example.onion", "onion")


class TestActorProfiler:
    @pytest.mark.asyncio
    async def test_process_content_no_author(self):
        """Test processing content without author returns None."""
        from app.actors.profiler import ActorProfiler
        profiler = ActorProfiler()
        result = await profiler.process_content(
            content_id="content1",
            author="",
            content_text="some text",
            entities={},
            site_name="TestSite",
            source_type="onion",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_process_content_whitespace_author(self):
        """Test processing content with whitespace-only author returns None."""
        from app.actors.profiler import ActorProfiler
        profiler = ActorProfiler()
        result = await profiler.process_content(
            content_id="content1",
            author="   ",
            content_text="some text",
            entities={},
            site_name="TestSite",
            source_type="onion",
        )
        assert result is None


# ─── API Integration Tests ────────────────────────────────────────────────────


class TestActorsAPI:
    def test_list_actors_no_auth(self, client):
        """Test list actors without auth."""
        from app.dependencies import get_current_user
        app = pytest.importorskip("app.main").app
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/actors")
        assert response.status_code in (401, 403)

    def test_list_actors_authenticated(self, client, admin_auth_headers):
        """Test list actors with auth."""
        response = client.get("/v1/actors", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    def test_list_actors_with_search(self, client, admin_auth_headers):
        """Test list actors with search query."""
        response = client.get("/v1/actors?q=dark", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_actor_detail(self, client, admin_auth_headers, sample_actor):
        """Test getting actor detail."""
        actor_id = sample_actor["_id"]
        response = client.get(f"/v1/actors/{actor_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == actor_id

    def test_get_actor_detail_not_found(self, client, admin_auth_headers):
        """Test getting non-existent actor."""
        response = client.get("/v1/actors/nonexistent", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_get_actor_graph(self, client, admin_auth_headers):
        """Test getting actor graph."""
        # This may return 404 because Neo4j has no data
        response = client.get("/v1/actors/some_id/graph", headers=admin_auth_headers)
        assert response.status_code in (200, 404, 502)

    def test_search_actors_endpoint(self, client, admin_auth_headers):
        """Test actor search endpoint."""
        response = client.get("/v1/actors/search?q=test", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_search_actors_no_auth(self, client):
        """Test actor search without auth."""
        from app.dependencies import get_current_user
        app = pytest.importorskip("app.main").app
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/actors/search?q=test")
        assert response.status_code in (401, 403)


from app.main import app
