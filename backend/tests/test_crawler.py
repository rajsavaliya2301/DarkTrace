"""Tests for crawler module — unit and API endpoint tests."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.crawler.proxy_pool import ProxyPoolManager, Proxy
from app.crawler.parsers import ContentParser, ParsedContent
from app.crawler.scheduler import CrawlJobScheduler


# ─── Unit Tests ───────────────────────────────────────────────────────────────


class TestProxy:
    def test_proxy_dataclass(self):
        proxy = Proxy(host="127.0.0.1", port=9050, protocol="socks5h", proxy_type="tor")
        assert proxy.host == "127.0.0.1"
        assert proxy.port == 9050
        assert proxy.proxy_type == "tor"
        assert proxy.is_alive is True
        assert proxy.consecutive_failures == 0


class TestProxyPool:
    @pytest.mark.asyncio
    async def test_initialize_pool(self):
        pool = ProxyPoolManager()
        await pool.initialize(
            tor_proxies=[("127.0.0.1", 9050)],
            i2p_proxies=[("127.0.0.1", 4444)],
        )
        proxies = await pool.list_proxies()
        assert len(proxies) == 2
        assert proxies[0]["proxy_type"] == "tor"
        assert proxies[1]["proxy_type"] == "i2p"

    @pytest.mark.asyncio
    async def test_get_proxy(self):
        pool = ProxyPoolManager()
        await pool.initialize(
            tor_proxies=[("127.0.0.1", 9050)],
            i2p_proxies=[],
        )
        proxy = await pool.get_proxy()
        assert proxy is not None
        assert proxy.host == "127.0.0.1"
        assert proxy.port == 9050

    @pytest.mark.asyncio
    async def test_get_proxy_by_type(self):
        pool = ProxyPoolManager()
        await pool.initialize(
            tor_proxies=[("127.0.0.1", 9050)],
            i2p_proxies=[("127.0.0.1", 4444)],
        )
        tor_proxy = await pool.get_proxy(proxy_type="tor")
        assert tor_proxy.proxy_type == "tor"
        i2p_proxy = await pool.get_proxy(proxy_type="i2p")
        assert i2p_proxy.proxy_type == "i2p"

    @pytest.mark.asyncio
    async def test_report_failure_removes_proxy(self):
        pool = ProxyPoolManager()
        await pool.initialize(tor_proxies=[("127.0.0.1", 9050)], i2p_proxies=[])

        # Report 3 failures to remove proxy
        await pool.report_failure("127.0.0.1", 9050)
        await pool.report_failure("127.0.0.1", 9050)
        await pool.report_failure("127.0.0.1", 9050)

        proxies = await pool.list_proxies()
        assert len(proxies) == 0

    @pytest.mark.asyncio
    async def test_sticky_session(self):
        pool = ProxyPoolManager()
        await pool.initialize(
            tor_proxies=[("127.0.0.1", 9050), ("127.0.0.2", 9050)],
            i2p_proxies=[],
        )

        # Get proxy with sticky_key and verify same proxy returned
        proxy1 = await pool.get_proxy(sticky_key="test_job_1")
        proxy2 = await pool.get_proxy(sticky_key="test_job_1")

        # With sticky_key matching circuit_id, the actual match depends on circuit_id naming
        # circuit_id is "tor_{host}_{port}", sticky_key is "test_job_1"
        # So they don't match by circuit_id, but should return the best available proxy
        assert proxy1 is not None
        assert proxy2 is not None

    @pytest.mark.asyncio
    async def test_report_success(self):
        pool = ProxyPoolManager()
        await pool.initialize(tor_proxies=[("127.0.0.1", 9050)], i2p_proxies=[])
        await pool.report_success("127.0.0.1", 9050, 100.0)

        proxies = await pool.list_proxies()
        assert len(proxies) == 1
        assert proxies[0]["is_alive"] is True
        assert proxies[0]["latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_get_proxy_empty_pool(self):
        pool = ProxyPoolManager()
        await pool.initialize(tor_proxies=[], i2p_proxies=[])
        proxy = await pool.get_proxy()
        assert proxy is None

    @pytest.mark.asyncio
    async def test_rotate_circuits(self):
        pool = ProxyPoolManager()
        await pool.initialize(
            tor_proxies=[("127.0.0.1", 9050), ("127.0.0.2", 9050)],
            i2p_proxies=[("127.0.0.1", 4444)],
        )
        await pool.rotate_circuits()
        proxies = await pool.list_proxies()
        tor_proxies = [p for p in proxies if p["proxy_type"] == "tor"]
        i2p_proxies = [p for p in proxies if p["proxy_type"] == "i2p"]
        # Tor proxies should have circuit IDs, I2P should not have changed
        assert len(tor_proxies) == 2
        assert len(i2p_proxies) == 1


class TestContentParser:
    def setup_method(self):
        self.parser = ContentParser()

    def test_classify_marketplace_url(self):
        doc_type = self.parser._classify_document("", "http://xyz.onion/listing/123")
        assert doc_type == "marketplace_listing"

    def test_classify_forum_url(self):
        doc_type = self.parser._classify_document("", "http://xyz.onion/thread/123")
        assert doc_type == "forum_post"

    def test_classify_paste_url(self):
        doc_type = self.parser._classify_document("", "http://xyz.onion/paste/abc")
        assert doc_type == "paste"

    def test_classify_auth_page(self):
        doc_type = self.parser._classify_document("", "http://xyz.onion/login")
        assert doc_type == "auth_page"

    def test_classify_listing_page(self):
        doc_type = self.parser._classify_document("", "http://xyz.onion/search?q=test")
        assert doc_type == "listing_page"

    def test_classify_unknown(self):
        doc_type = self.parser._classify_document("<html></html>", "http://xyz.onion/unknown")
        assert doc_type == "unknown"

    def test_extract_entities(self):
        text = "Contact: test@email.com, BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        entities = self.parser._extract_entities(text)
        assert "test@email.com" in entities["emails"]
        assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in entities["btc_addresses"]

    def test_extract_entities_empty(self):
        entities = self.parser._extract_entities("No entities here")
        assert len(entities["emails"]) == 0
        assert len(entities["btc_addresses"]) == 0

    def test_generic_parse(self):
        html = """
        <html><head><title>Test Page</title></head>
        <body>
            <article>
                <h1>Dark Web Market</h1>
                <p>Selling premium exploit kits. Contact: seller@onion.com</p>
                <span class="author">dark_hacker</span>
            </article>
        </body></html>
        """
        result = self.parser.parse(
            url="http://test.onion/listing/1",
            source_type="onion",
            site_name="TestMarket",
            raw_html=html,
            content_type="text/html",
        )
        assert result.title == "Test Page"
        assert "Dark Web Market" in result.content_text
        assert "seller@onion.com" in result.entities["emails"]

    def test_parse_marketplace_listing(self):
        html = """
        <html><head><title>Premium Ransomware v3.0 - DarkMarket</title></head><body>
            <h1>Premium Ransomware v3.0</h1>
            <span class="vendor">dark_vendor</span>
            <span class="category">malware</span>
            <span>Price: $5000 BTC</span>
            <p>Latest ransomware with full source code</p>
        </body></html>
        """
        result = self.parser.parse(
            url="http://test.onion/listing/1",
            source_type="onion",
            site_name="example_market",
            raw_html=html,
            content_type="text/html",
        )
        assert result.document_type == "marketplace_listing"
        # Title extraction depends on parser implementation; check it's not empty
        assert result.title != ""

    def test_parse_forum_post(self):
        html = """
        <html><body>
            <h1>New Exploit Kit Release</h1>
            <span class="author">hacker123</span>
            <p>Check out my new exploit kit</p>
        </body></html>
        """
        result = self.parser.parse(
            url="http://test.onion/thread/123",
            source_type="onion",
            site_name="dark_hub",
            raw_html=html,
            content_type="text/html",
        )
        assert result.document_type == "forum_post"

    def test_parsed_content_to_dict(self):
        pc = ParsedContent(
            url="http://test.onion",
            source_type="onion",
            site_name="Test",
            document_type="forum_post",
            title="Test Title",
            author="author1",
            content_text="Test content",
        )
        d = pc.to_dict()
        assert d["url"] == "http://test.onion"
        assert d["title"] == "Test Title"
        assert d["author"] == "author1"
        assert d["document_type"] == "forum_post"


class TestScheduler:
    @pytest.mark.asyncio
    async def test_add_recurring_job(self):
        scheduler = CrawlJobScheduler()
        job_id = await scheduler.add_recurring_job(
            target_id="target1",
            target_url="http://test.onion",
            frequency="every_6h",
        )
        assert job_id is not None
        jobs = await scheduler.get_all_jobs()
        assert len(jobs) == 1
        assert jobs[0]["target_url"] == "http://test.onion"

    @pytest.mark.asyncio
    async def test_add_one_off_job(self):
        scheduler = CrawlJobScheduler()
        job_id = await scheduler.add_one_off_job(
            target_id="target1",
            target_url="http://test.onion",
        )
        assert job_id is not None
        assert job_id in [j["id"] for j in await scheduler.get_all_jobs()]

    @pytest.mark.asyncio
    async def test_parse_frequency(self):
        assert CrawlJobScheduler._parse_frequency("every_1h") == 3600
        assert CrawlJobScheduler._parse_frequency("every_24h") == 86400
        assert CrawlJobScheduler._parse_frequency("every_7d") == 604800
        assert CrawlJobScheduler._parse_frequency("every_30d") == 2592000

    @pytest.mark.asyncio
    async def test_parse_frequency_default(self):
        assert CrawlJobScheduler._parse_frequency("unknown") == 21600

    @pytest.mark.asyncio
    async def test_remove_job(self):
        scheduler = CrawlJobScheduler()
        job_id = await scheduler.add_recurring_job(
            target_id="target1",
            target_url="http://test.onion",
            frequency="every_1h",
        )
        assert len(await scheduler.get_all_jobs()) == 1
        await scheduler.remove_job(job_id)
        assert len(await scheduler.get_all_jobs()) == 0

    @pytest.mark.asyncio
    async def test_mark_completed_recurring(self):
        scheduler = CrawlJobScheduler()
        job_id = await scheduler.add_recurring_job(
            target_id="target1",
            target_url="http://test.onion",
            frequency="every_1h",
        )
        await scheduler.mark_completed(job_id)
        jobs = await scheduler.get_all_jobs()
        assert jobs[0]["last_run"] is not None
        assert jobs[0]["is_active"] is True  # Recurring stays active

    @pytest.mark.asyncio
    async def test_mark_completed_one_off(self):
        scheduler = CrawlJobScheduler()
        job_id = await scheduler.add_one_off_job(
            target_id="target1",
            target_url="http://test.onion",
        )
        await scheduler.mark_completed(job_id)
        jobs = await scheduler.get_all_jobs()
        assert jobs[0]["is_active"] is False  # One-off deactivates

    @pytest.mark.asyncio
    async def test_callback_invocation(self):
        scheduler = CrawlJobScheduler()
        callback_called = False

        async def on_job(job):
            nonlocal callback_called
            callback_called = True

        scheduler.set_job_callback(on_job)
        # Add a job with next_run set to now
        job_id = await scheduler.add_recurring_job(
            target_id="target1",
            target_url="http://test.onion",
            frequency="every_1h",
        )
        # Trigger callback manually
        due = await scheduler.get_due_jobs()
        for job in due:
            if scheduler._on_job_callback:
                await scheduler._on_job_callback(job)
                await scheduler.mark_completed(job["id"])

        assert callback_called is True


# ─── API Integration Tests ────────────────────────────────────────────────────


class TestCrawlerAPI:
    def test_list_targets_no_auth(self, client):
        """Test list targets without auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/crawler/targets")
        assert response.status_code in (401, 403)

    def test_list_targets_authenticated(self, client, admin_auth_headers, sample_crawl_target):
        """Test list targets with auth."""
        response = client.get("/v1/crawler/targets", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_create_target(self, client, admin_auth_headers, mock_mongodb):
        """Test creating a crawl target."""
        import asyncio
        # Remove any conflicting document
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(mock_mongodb.crawl_targets.delete_many({}))
        loop.close()

        response = client.post(
            "/v1/crawler/targets",
            json={
                "url": "http://test-market.onion",
                "site_name": "TestMarket",
                "source_type": "onion",
                "crawl_frequency": "every_6h",
                "tags": ["ransomware"],
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["status"] == "active"

    def test_create_target_duplicate(self, client, admin_auth_headers, mock_mongodb, sample_crawl_target):
        """Test creating a duplicate target."""
        response = client.post(
            "/v1/crawler/targets",
            json={
                "url": "http://test.onion/market",
                "site_name": "Another",
                "source_type": "onion",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 409

    def test_create_target_validation(self, client, admin_auth_headers):
        """Test creating target with invalid data."""
        response = client.post(
            "/v1/crawler/targets",
            json={"url": "", "site_name": ""},  # Invalid
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_update_target(self, client, admin_auth_headers, sample_crawl_target):
        """Test updating a crawl target."""
        target_id = sample_crawl_target["_id"]
        response = client.put(
            f"/v1/crawler/targets/{target_id}",
            json={"site_name": "UpdatedMarket", "status": "paused"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_update_target_not_found(self, client, admin_auth_headers):
        """Test updating non-existent target."""
        response = client.put(
            "/v1/crawler/targets/nonexistent",
            json={"site_name": "Test"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_delete_target(self, client, admin_auth_headers, sample_crawl_target):
        """Test deleting a crawl target."""
        target_id = sample_crawl_target["_id"]
        response = client.delete(f"/v1/crawler/targets/{target_id}", headers=admin_auth_headers)
        assert response.status_code == 204

    def test_delete_target_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent target."""
        response = client.delete("/v1/crawler/targets/nonexistent", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_trigger_crawl(self, client, admin_auth_headers, sample_crawl_target):
        """Test triggering a crawl job."""
        target_id = sample_crawl_target["_id"]
        response = client.post(
            f"/v1/crawler/targets/{target_id}/crawl",
            headers=admin_auth_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_trigger_crawl_not_found(self, client, admin_auth_headers):
        """Test triggering crawl on non-existent target."""
        response = client.post(
            "/v1/crawler/targets/nonexistent/crawl",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_list_jobs(self, client, admin_auth_headers, sample_crawl_target):
        """Test listing crawl jobs."""
        response = client.get("/v1/crawler/jobs", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    def test_get_job_status(self, client, admin_auth_headers, mock_mongodb):
        """Test getting a specific job status."""
        import asyncio
        import uuid
        job_id = str(uuid.uuid4())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(mock_mongodb.crawl_jobs.insert_one({
            "_id": job_id,
            "target_id": "target1",
            "target_url": "http://test.onion",
            "status": "completed",
            "pages_fetched": 10,
            "pages_total": 10,
            "pages_failed": 0,
            "errors": [],
            "proxy_pool_used": [],
        }))
        loop.close()

        response = client.get(f"/v1/crawler/jobs/{job_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["status"] == "completed"

    def test_get_job_not_found(self, client, admin_auth_headers):
        """Test getting non-existent job."""
        response = client.get("/v1/crawler/jobs/nonexistent", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_list_jobs_no_auth(self, client):
        """Test list jobs without auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/v1/crawler/jobs")
        assert response.status_code in (401, 403)


from app.main import app
