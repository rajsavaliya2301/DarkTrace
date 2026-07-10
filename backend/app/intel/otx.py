"""AlienVault OTX (Open Threat Exchange) API v1 Integration.

Free tier: generous usage limits. Community-contributed threat intelligence
covering IPs, domains, URLs, file hashes, and more.

API key registration: https://otx.alienvault.com/api
"""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class OTXClient:
    """Async client for AlienVault OTX API v1.

    Provides threat-intelligence lookups against the Open Threat Exchange
    community dataset including pulses, indicators, and reputation data.

    Returns ``None`` when the API key is not configured or on failure.
    """

    BASE_URL = "https://otx.alienvault.com/api/v1"

    def __init__(self, api_key: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.OTX_API_KEY

    # ── Public helpers ─────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """Whether the client has a configured API key."""
        return bool(self.api_key)

    # ── IP ─────────────────────────────────────────────────────────────────

    async def check_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Return threat intelligence for an IP address.

        Includes Geo data, pulse count, reputation, and related indicators.
        """
        return await self._get(f"/indicators/IPv4/{ip}/general")

    async def check_ip_passive_dns(self, ip: str) -> Optional[Dict[str, Any]]:
        """Return passive DNS resolutions for an IP."""
        return await self._get(f"/indicators/IPv4/{ip}/passive_dns")

    async def check_ip_malware(self, ip: str) -> Optional[Dict[str, Any]]:
        """Return malware samples associated with an IP."""
        return await self._get(f"/indicators/IPv4/{ip}/malware")

    async def check_ip_url_list(self, ip: str) -> Optional[Dict[str, Any]]:
        """Return URLs associated with an IP."""
        return await self._get(f"/indicators/IPv4/{ip}/url_list")

    # ── Domain ─────────────────────────────────────────────────────────────

    async def check_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Return threat intelligence for a domain."""
        return await self._get(f"/indicators/domain/{domain}/general")

    async def check_domain_passive_dns(
        self, domain: str
    ) -> Optional[Dict[str, Any]]:
        """Return passive DNS data for a domain."""
        return await self._get(f"/indicators/domain/{domain}/passive_dns")

    async def check_domain_malware(
        self, domain: str
    ) -> Optional[Dict[str, Any]]:
        """Return malware samples associated with a domain."""
        return await self._get(f"/indicators/domain/{domain}/malware")

    async def check_domain_url_list(
        self, domain: str
    ) -> Optional[Dict[str, Any]]:
        """Return URLs associated with a domain."""
        return await self._get(f"/indicators/domain/{domain}/url_list")

    # ── URL ────────────────────────────────────────────────────────────────

    async def check_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Return threat intelligence for a URL."""
        # OTX requires URL-encoded URLs
        import urllib.parse

        encoded = urllib.parse.quote(url, safe="")
        return await self._get(f"/indicators/url/{encoded}/general")

    # ── File Hash ──────────────────────────────────────────────────────────

    async def check_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Return threat intelligence for a file hash (MD5/SHA-1/SHA-256)."""
        return await self._get(f"/indicators/file/{file_hash}/general")

    async def check_hash_analysis(
        self, file_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Return analysis results for a file hash."""
        return await self._get(f"/indicators/file/{file_hash}/analysis")

    # ── Pulses ─────────────────────────────────────────────────────────────

    async def get_pulses(
        self, limit: int = 20, page: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Return recent OTX pulses (threat intelligence collections)."""
        params = {"limit": min(limit, 50), "page": page}
        return await self._get("/pulses/subscribed", params=params)

    async def get_pulse(self, pulse_id: str) -> Optional[Dict[str, Any]]:
        """Return a single OTX pulse by ID."""
        return await self._get(f"/pulses/{pulse_id}")

    # ── Internal ───────────────────────────────────────────────────────────

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        if not self.available:
            logger.debug("OTX: skipped %s (no API key)", path)
            return None
        url = f"{self.BASE_URL}{path}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    headers=self._headers(),
                    params=params or {},
                )
            if resp.status_code == 404:
                logger.info("OTX: 404 on %s — no results", path)
                return {"data": None, "error": "not_found"}
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
            logger.debug("OTX: %s returned %s", path, resp.status_code)
            return data
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "OTX HTTP error %s on %s: %s",
                exc.response.status_code,
                path,
                exc.response.text[:200],
            )
            return None
        except httpx.RequestError as exc:
            logger.warning("OTX request failed for %s: %s", path, exc)
            return None

    def _headers(self) -> Dict[str, str]:
        return {
            "X-OTX-API-KEY": self.api_key,
            "Accept": "application/json",
        }


# ── Convenience helpers ────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_otx_client() -> OTXClient:
    """Return a cached singleton OTXClient."""
    return OTXClient()
