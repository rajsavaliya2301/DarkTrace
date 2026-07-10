"""SOCKS5 proxy pool manager for Tor and I2P proxy rotation."""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Represents a single proxy entry."""
    host: str
    port: int
    protocol: str  # "socks5", "socks5h"
    proxy_type: str  # "tor" or "i2p"
    is_alive: bool = True
    latency_ms: float = 0.0
    consecutive_failures: int = 0
    last_checked: float = 0.0
    last_used: float = 0.0
    circuit_id: Optional[str] = None


class ProxyPoolManager:
    """Manages a pool of Tor and I2P SOCKS5 proxies."""

    def __init__(self):
        self._proxies: List[Proxy] = []
        self._lock = asyncio.Lock()
        self._health_check_interval = 60  # seconds
        self._max_consecutive_failures = 3
        self._background_task: Optional[asyncio.Task] = None

    async def initialize(self, tor_proxies: List[Tuple[str, int]], i2p_proxies: List[Tuple[str, int]]):
        """Initialize the proxy pool with given Tor and I2P proxies."""
        async with self._lock:
            for host, port in tor_proxies:
                self._proxies.append(
                    Proxy(
                        host=host,
                        port=port,
                        protocol="socks5h",
                        proxy_type="tor",
                        circuit_id=f"tor_{host}_{port}",
                    )
                )
            for host, port in i2p_proxies:
                self._proxies.append(
                    Proxy(
                        host=host,
                        port=port,
                        protocol="socks5",
                        proxy_type="i2p",
                    )
                )
            logger.info(
                "Proxy pool initialized with %d Tor and %d I2P proxies",
                len(tor_proxies),
                len(i2p_proxies),
            )

        # Start background health checker
        self._background_task = asyncio.create_task(self._health_check_loop())

    async def shutdown(self):
        """Shutdown the proxy pool manager."""
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

    async def get_proxy(self, proxy_type: Optional[str] = None, sticky_key: Optional[str] = None) -> Optional[Proxy]:
        """Get the best available proxy. Optionally filter by type or stickiness."""
        async with self._lock:
            candidates = [p for p in self._proxies if p.is_alive]
            if proxy_type:
                candidates = [p for p in candidates if p.proxy_type == proxy_type]

            if not candidates:
                # Try degraded proxies
                candidates = [p for p in self._proxies if not p.is_alive and p.consecutive_failures < self._max_consecutive_failures]
                if proxy_type:
                    candidates = [p for p in candidates if p.proxy_type == proxy_type]
                if not candidates:
                    return None

            # Sticky session: if we have a key, try to reuse same proxy
            if sticky_key:
                for p in candidates:
                    if p.circuit_id == sticky_key:
                        p.last_used = time.time()
                        return p

            # Pick proxy with lowest latency and least recent use
            candidates.sort(key=lambda p: (p.latency_ms if p.latency_ms > 0 else 9999, p.last_used))
            selected = candidates[0]
            selected.last_used = time.time()
            return selected

    async def report_failure(self, proxy_host: str, proxy_port: int):
        """Report a proxy failure. May lead to proxy being removed from pool."""
        async with self._lock:
            for p in self._proxies:
                if p.host == proxy_host and p.port == proxy_port:
                    p.consecutive_failures += 1
                    p.is_alive = False
                    logger.warning(
                        "Proxy %s:%d failed (%d consecutive)",
                        proxy_host,
                        proxy_port,
                        p.consecutive_failures,
                    )
                    if p.consecutive_failures >= self._max_consecutive_failures:
                        self._proxies.remove(p)
                        logger.warning(
                            "Proxy %s:%d removed from pool after %d failures",
                            proxy_host,
                            proxy_port,
                            p.consecutive_failures,
                        )
                    break

    async def report_success(self, proxy_host: str, proxy_port: int, latency_ms: float):
        """Report a proxy success. Resets failure count and updates latency."""
        async with self._lock:
            for p in self._proxies:
                if p.host == proxy_host and p.port == proxy_port:
                    p.consecutive_failures = 0
                    p.is_alive = True
                    p.latency_ms = (p.latency_ms * 0.7) + (latency_ms * 0.3)  # EMA
                    p.last_checked = time.time()
                    break

    async def list_proxies(self) -> List[dict]:
        """List all proxies with their status."""
        async with self._lock:
            return [
                {
                    "host": p.host,
                    "port": p.port,
                    "protocol": p.protocol,
                    "proxy_type": p.proxy_type,
                    "is_alive": p.is_alive,
                    "latency_ms": round(p.latency_ms, 1),
                    "consecutive_failures": p.consecutive_failures,
                    "last_checked": p.last_checked,
                }
                for p in self._proxies
            ]

    async def rotate_circuits(self):
        """Simulate Tor circuit rotation (NEWNYM signal)."""
        async with self._lock:
            for p in self._proxies:
                if p.proxy_type == "tor":
                    p.circuit_id = f"tor_{p.host}_{p.port}_{random.randint(1, 10000)}"
                    p.latency_ms = 0
            logger.info("Tor circuits rotated for %d proxies", len([p for p in self._proxies if p.proxy_type == "tor"]))

    async def _health_check_loop(self):
        """Background task: periodically check proxy health."""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._check_all_proxies()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error: %s", e)

    async def _check_all_proxies(self):
        """Check health of all proxies."""
        for proxy in self._proxies:
            start = time.time()
            try:
                # Simulated health check: try TCP connect
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(proxy.host, proxy.port),
                    timeout=10,
                )
                writer.close()
                await writer.wait_closed()
                latency = (time.time() - start) * 1000
                await self.report_success(proxy.host, proxy.port, latency)
            except Exception:
                await self.report_failure(proxy.host, proxy.port)


# Singleton instance
_proxy_pool: Optional[ProxyPoolManager] = None


async def get_proxy_pool() -> ProxyPoolManager:
    """Get or create the singleton proxy pool manager."""
    global _proxy_pool
    if _proxy_pool is None:
        from app.config import get_settings
        settings = get_settings()
        _proxy_pool = ProxyPoolManager()
        # Default proxies from settings
        await _proxy_pool.initialize(
            tor_proxies=[(settings.TOR_PROXY_HOST, settings.TOR_PROXY_PORT)],
            i2p_proxies=[(settings.I2P_PROXY_HOST, settings.I2P_PROXY_PORT)],
        )
    return _proxy_pool
