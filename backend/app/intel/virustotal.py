"""VirusTotal API v3 Integration.

Free tier limits: 4 requests / minute, 500 requests / day.
API key registration: https://www.virustotal.com/gui/join-us
"""

import logging
import time
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# ─── Rate Limiting ──────────────────────────────────────────────────────────
# Free tier: 4 requests per minute → 15 seconds between requests
VT_RATE_LIMIT_SECONDS = 15.0


class VirusTotalClient:
    """Async client for VirusTotal API v3.

    Supports IP, domain, URL, and file-hash lookups.  Returns
    ``None`` when the API key is not configured or when a request fails.
    """

    BASE_URL = "https://www.virustotal.com/api/v3"

    def __init__(self, api_key: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.VIRUSTOTAL_API_KEY
        self._last_request_time: float = 0.0

    # ── Public helpers ─────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """Whether the client has a configured API key."""
        return bool(self.api_key)

    # ── IP ─────────────────────────────────────────────────────────────────

    async def check_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Look up an IP address in VirusTotal."""
        return await self._get(f"/ip_addresses/{ip}")

    # ── Domain ─────────────────────────────────────────────────────────────

    async def check_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Look up a domain in VirusTotal."""
        return await self._get(f"/domains/{domain}")

    # ── URL ────────────────────────────────────────────────────────────────

    async def check_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Look up a URL (must be base64-urlsafe encoded)."""
        import base64

        encoded = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        return await self._get(f"/urls/{encoded}")

    async def submit_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Submit a URL for scanning and return the analysis ID."""
        return await self._post("/urls", data={"url": url})

    async def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the result of a URL / file analysis."""
        return await self._get(f"/analyses/{analysis_id}")

    # ── File Hash ──────────────────────────────────────────────────────────

    async def check_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Look up a file hash (MD5, SHA-1, or SHA-256) in VirusTotal."""
        return await self._get(f"/files/{file_hash}")

    # ── Internal ───────────────────────────────────────────────────────────

    async def _get(self, path: str) -> Optional[Dict[str, Any]]:
        if not self.available:
            logger.debug("VirusTotal: skipped %s (no API key)", path)
            return None
        await self._throttle()
        url = f"{self.BASE_URL}{path}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url, headers=self._headers(), params=None
                )
            if resp.status_code == 404:
                logger.info("VirusTotal: 404 on %s — no results", path)
                return {"data": None, "error": "not_found"}
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
            logger.debug("VirusTotal: %s returned %s", path, resp.status_code)
            return data
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "VirusTotal HTTP error %s on %s: %s",
                exc.response.status_code,
                path,
                exc.response.text[:200],
            )
            return None
        except httpx.RequestError as exc:
            logger.warning("VirusTotal request failed for %s: %s", path, exc)
            return None

    async def _post(
        self, path: str, data: dict
    ) -> Optional[Dict[str, Any]]:
        if not self.available:
            logger.debug("VirusTotal: skipped POST %s (no API key)", path)
            return None
        await self._throttle()
        url = f"{self.BASE_URL}{path}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    url, headers=self._headers(), data=data
                )
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
            logger.debug("VirusTotal POST %s -> %s", path, resp.status_code)
            return data
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "VirusTotal POST HTTP error %s on %s: %s",
                exc.response.status_code,
                path,
                exc.response.text[:200],
            )
            return None
        except httpx.RequestError as exc:
            logger.warning(
                "VirusTotal POST request failed for %s: %s", path, exc
            )
            return None

    def _headers(self) -> Dict[str, str]:
        return {"x-apikey": self.api_key, "Accept": "application/json"}

    async def _throttle(self) -> None:
        """Enforce free-tier rate limit (4 req/min)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < VT_RATE_LIMIT_SECONDS:
            wait = VT_RATE_LIMIT_SECONDS - elapsed
            logger.debug("VirusTotal: throttling %.1fs", wait)
            await _async_sleep(wait)
        self._last_request_time = time.time()


async def _async_sleep(seconds: float) -> None:
    """Sleep without blocking the event loop."""
    import asyncio

    await asyncio.sleep(seconds)


# ── Convenience helpers ────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_vt_client() -> VirusTotalClient:
    """Return a cached singleton VirusTotalClient."""
    return VirusTotalClient()
