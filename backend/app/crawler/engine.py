"""Scrapy-based crawl engine with Tor/I2P proxy rotation."""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiohttp
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.crawler.proxy_pool import ProxyPoolManager, get_proxy_pool
from app.crawler.parsers import ContentParser
from app.crawler.scheduler import CrawlJobScheduler, get_scheduler
from app.config import get_settings
from app.database import get_mongodb, get_elasticsearch

logger = logging.getLogger(__name__)


class CrawlEngine:
    """Manages crawling operations: fetch pages via proxies, parse, and store."""

    def __init__(self):
        self._parser = ContentParser()
        self._active_jobs: dict = {}
        self._http_sessions: dict = {}

    async def execute_job(self, job: dict) -> dict:
        """Execute a crawl job: fetch pages from the target URL."""
        settings = get_settings()
        job_id = job["id"]
        target_url = job["target_url"]
        source_type = job.get("source_type", "onion")
        proxy_config = job.get("proxy_config", {})

        logger.info("Starting crawl job %s for %s", job_id, target_url)

        # Get proxy pool
        proxy_pool = await get_proxy_pool()
        # Map source type to proxy pool type (onion -> tor)
        proxy_type_key = "tor" if source_type == "onion" else source_type
        proxy = await proxy_pool.get_proxy(proxy_type=proxy_type_key)

        # Create HTTP session with proxy
        session = await self._create_session(proxy)

        try:
            # Fetch the page
            start_time = time.time()
            async with session.get(target_url, timeout=aiohttp.ClientTimeout(total=settings.CRAWL_TIMEOUT)) as response:
                latency = (time.time() - start_time) * 1000
                raw_html = await response.text()
                content_type = response.headers.get("Content-Type", "text/html")
                http_status = response.status

            # Report proxy success
            if proxy:
                await proxy_pool.report_success(proxy.host, proxy.port, latency)

            # Parse content
            parsed = self._parser.parse(
                url=target_url,
                source_type=source_type,
                site_name=job.get("site_name", "unknown"),
                raw_html=raw_html,
                content_type=content_type,
            )

            # Compute content hash
            content_hash = hashlib.sha256(raw_html.encode()).hexdigest()

            # Store in MongoDB
            db = await get_mongodb()
            crawl_id = str(uuid.uuid4())
            content_doc = {
                "_id": crawl_id,
                "crawl_id": job_id,
                "url": target_url,
                "normalized_url": target_url.rstrip("/"),
                "source_type": source_type,
                "site_name": job.get("site_name", "unknown"),
                "fetch_timestamp": datetime.now(timezone.utc),
                "http_status": http_status,
                "response_headers": dict(response.headers),
                "content_type": content_type,
                "raw_html": raw_html,
                "content_hash": content_hash,
                "content_size_bytes": len(raw_html),
                "text_content": parsed.content_text,
                "proxy_used": f"{proxy.host}:{proxy.port}" if proxy else "none",
                "processing_status": "parsed",
                "parsed_at": datetime.now(timezone.utc),
                "analyzed_at": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            await db.raw_content.insert_one(content_doc)

            # Index in Elasticsearch
            try:
                es = await get_elasticsearch()
                await es.index(
                    index="crawled_content",
                    id=crawl_id,
                    body={
                        "id": crawl_id,
                        "crawl_id": job_id,
                        "url": target_url,
                        "source_type": source_type,
                        "site_name": job.get("site_name", "unknown"),
                        "document_type": parsed.document_type,
                        "title": parsed.title,
                        "content_text": parsed.content_text,
                        "author": parsed.author,
                        "published_date": parsed.published_date,
                        "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
                        "language": parsed.language,
                        "entities": parsed.entities,
                        "content_hash": content_hash,
                        "processing_status": "parsed",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    refresh="wait_for",
                )
                logger.debug("Indexed %s in Elasticsearch", crawl_id)
            except Exception as es_error:
                logger.warning("Elasticsearch indexing failed for %s: %s", crawl_id, es_error)

            # Trigger post-processing pipeline (NLP → actors → scoring → alerts)
            try:
                from app.pipeline import process_crawled_content
                asyncio.create_task(process_crawled_content(crawl_id, content_doc))
            except Exception as pipe_err:
                logger.warning("Failed to launch processing pipeline: %s", pipe_err)

            result = {
                "crawl_id": crawl_id,
                "url": target_url,
                "http_status": http_status,
                "pages_crawled": 1,
                "errors": 0,
                "content_hash": content_hash,
                "latency_ms": round(latency, 1),
            }
            return result

        except asyncio.TimeoutError:
            if proxy:
                await proxy_pool.report_failure(proxy.host, proxy.port)
            logger.warning("Timeout crawling %s", target_url)
            return {"crawl_id": None, "url": target_url, "pages_crawled": 0, "errors": 1, "error": "timeout"}

        except aiohttp.ClientError as e:
            if proxy:
                await proxy_pool.report_failure(proxy.host, proxy.port)
            logger.warning("HTTP error crawling %s: %s", target_url, e)
            return {"crawl_id": None, "url": target_url, "pages_crawled": 0, "errors": 1, "error": str(e)}

        except Exception as e:
            if proxy:
                await proxy_pool.report_failure(proxy.host, proxy.port)
            logger.error("Unexpected error crawling %s: %s", target_url, e)
            return {"crawl_id": None, "url": target_url, "pages_crawled": 0, "errors": 1, "error": str(e)}

        finally:
            await self._close_session(session)

    async def execute_job_with_links(self, job: dict, max_pages: int = 10) -> dict:
        """Execute a crawl job with link following (basic spider)."""
        settings = get_settings()
        target_url = job["target_url"]
        source_type = job.get("source_type", "onion")
        proxy_pool = await get_proxy_pool()

        visited = set()
        to_visit = {target_url}
        pages_crawled = []
        errors = 0

        while to_visit and len(visited) < max_pages:
            url = to_visit.pop()
            if url in visited:
                continue

            # Map source type to proxy pool type (onion -> tor)
            proxy_type_key = "tor" if source_type == "onion" else source_type
            proxy = await proxy_pool.get_proxy(proxy_type=proxy_type_key)
            session = await self._create_session(proxy)

            try:
                start = time.time()
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=settings.CRAWL_TIMEOUT)) as response:
                    latency = (time.time() - start) * 1000
                    raw_html = await response.text()

                if proxy:
                    await proxy_pool.report_success(proxy.host, proxy.port, latency)

                visited.add(url)

                # Parse and extract links
                parsed = self._parser.parse(
                    url=url,
                    source_type=source_type,
                    site_name=job.get("site_name", "unknown"),
                    raw_html=raw_html,
                    content_type=response.headers.get("Content-Type", "text/html"),
                )

                # Store
                db = await get_mongodb()
                content_doc = {
                    "_id": str(uuid.uuid4()),
                    "crawl_id": job["id"],
                    "url": url,
                    "source_type": source_type,
                    "fetch_timestamp": datetime.now(timezone.utc),
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type", "text/html"),
                    "raw_html": raw_html,
                    "content_hash": hashlib.sha256(raw_html.encode()).hexdigest(),
                    "text_content": parsed.content_text,
                    "proxy_used": f"{proxy.host}:{proxy.port}" if proxy else "none",
                    "processing_status": "parsed",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
                await db.raw_content.insert_one(content_doc)
                pages_crawled.append(url)

            except Exception as e:
                if proxy:
                    await proxy_pool.report_failure(proxy.host, proxy.port)
                errors += 1
                logger.warning("Error crawling %s: %s", url, e)

            finally:
                await self._close_session(session)

        return {
            "pages_crawled": len(pages_crawled),
            "errors": errors,
            "urls": pages_crawled,
        }

    async def _create_session(self, proxy: Optional["Proxy"] = None) -> aiohttp.ClientSession:
        """Create an aiohttp session with optional SOCKS5 proxy support."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        if proxy:
            try:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(
                    f"{proxy.protocol}://{proxy.host}:{proxy.port}",
                    ssl=False,
                )
                logger.debug("Using SOCKS5 proxy: %s://%s:%s", proxy.protocol, proxy.host, proxy.port)
            except ImportError:
                logger.warning("aiohttp_socks not installed, falling back to HTTP proxy (Tor DNS won't work for .onion)")
                connector = aiohttp.TCPConnector(ssl=False)
            return aiohttp.ClientSession(
                connector=connector,
                headers=headers,
            )
        return aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers)

    async def _close_session(self, session: aiohttp.ClientSession):
        """Close an HTTP session."""
        if not session.closed:
            await session.close()


# Singleton
_crawl_engine: Optional[CrawlEngine] = None


async def get_crawl_engine() -> CrawlEngine:
    """Get or create the singleton crawl engine."""
    global _crawl_engine
    if _crawl_engine is None:
        _crawl_engine = CrawlEngine()
    return _crawl_engine
