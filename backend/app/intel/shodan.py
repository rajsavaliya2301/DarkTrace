"""Shodan API Integration.

Free tier limits: 1 request / second, 100 query credits / month.
API key registration: https://account.shodan.io/register
"""

import logging
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# ─── Rate Limiting ──────────────────────────────────────────────────────────
SHODAN_RATE_LIMIT_SECONDS = 1.0


class ShodanClient:
    """Async client for the Shodan API.

    Provides methods to look up IP addresses (host services, banners,
    vulnerabilities) and execute search queries against Shodan's database
    of exposed internet-connected devices.

    Returns ``None`` when the API key is not configured or on failure.
    """

    BASE_URL = "https://api.shodan.io"

    def __init__(self, api_key: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.SHODAN_API_KEY
        self._last_request_time: float = 0.0

    # ── Public helpers ─────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """Whether the client has a configured API key."""
        return bool(self.api_key)

    # ── IP ─────────────────────────────────────────────────────────────────

    async def lookup_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Return all known services and banners for an IP address.

        This is the richest Shodan endpoint — returns open ports,
        service banners, hostnames, operating system, vulnerability
        CVEs, and geographic information.
        """
        return await self._get(f"/shodan/host/{ip}")

    # ── Domain ─────────────────────────────────────────────────────────────

    async def resolve_dns(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Resolve a hostname to an IP via Shodan's DNS resolver."""
        return await self._get(
            "/dns/resolve", params={"hostnames": hostname}
        )

    async def reverse_dns(self, ip: str) -> Optional[Dict[str, Any]]:
        """Reverse DNS lookup via Shodan."""
        return await self._get("/dns/reverse", params={"ips": ip})

    # ── Search ─────────────────────────────────────────────────────────────

    async def search(
        self, query: str, page: int = 1, limit: int = 100
    ) -> Optional[Dict[str, Any]]:
        """Search Shodan's device database.

        Query syntax: https://help.shodan.io/the-basics/search-query-fundamentals
        """
        params = {"query": query, "page": page, "limit": min(limit, 100)}
        return await self._get("/shodan/host/search", params=params)

    async def search_count(self, query: str) -> Optional[int]:
        """Return the number of results for a search query (consumes 1 credit)."""
        data = await self._get(
            "/shodan/host/count", params={"query": query}
        )
        if data is None:
            return None
        return int(data.get("total", 0))

    # ── Account / Status ───────────────────────────────────────────────────

    async def api_info(self) -> Optional[Dict[str, Any]]:
        """Return current API plan info including remaining credits."""
        return await self._get("/api-info")

    # ── Internal ───────────────────────────────────────────────────────────

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        if not self.available:
            logger.debug("Shodan: skipped %s (no API key)", path)
            return None
        await self._throttle()
        url = f"{self.BASE_URL}{path}"
        query_params = dict(params or {})
        query_params["key"] = self.api_key
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params=query_params)
            if resp.status_code == 404:
                logger.info("Shodan: 404 on %s — no results", path)
                return {"data": None, "error": "not_found"}
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
            logger.debug("Shodan: %s returned %s", path, resp.status_code)
            return data
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Shodan HTTP error %s on %s: %s",
                exc.response.status_code,
                path,
                exc.response.text[:200],
            )
            return None
        except httpx.RequestError as exc:
            logger.warning("Shodan request failed for %s: %s", path, exc)
            return None

    async def _throttle(self) -> None:
        """Enforce free-tier rate limit (1 req/sec)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < SHODAN_RATE_LIMIT_SECONDS:
            wait = SHODAN_RATE_LIMIT_SECONDS - elapsed
            logger.debug("Shodan: throttling %.1fs", wait)
            import asyncio
            await asyncio.sleep(wait)
        self._last_request_time = time.time()


# ── Convenience helpers ────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_shodan_client() -> ShodanClient:
    """Return a cached singleton ShodanClient."""
    return ShodanClient()
