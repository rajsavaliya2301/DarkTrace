"""Test Tor proxy connectivity directly."""
import asyncio
import logging
import sys

logging.basicConfig(level=logging.DEBUG)

async def test():
    # Test 1: Can we connect to Tor proxy?
    print("=== Test 1: Connecting to Tor proxy ===")
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("tor-proxy", 9050),
            timeout=5
        )
        print("Tor proxy TCP connection OK")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Tor proxy connection FAILED: {e}")

    # Test 2: Can we use aiohttp_socks with Tor?
    print("\n=== Test 2: HTTP request via Tor SOCKS5h ===")
    try:
        from aiohttp_socks import ProxyConnector
        import aiohttp
        
        connector = ProxyConnector.from_url("socks5h://tor-proxy:9050")
        async with aiohttp.ClientSession(connector=connector) as session:
            print("Session created, testing connection...")
            try:
                async with session.get(
                    "http://httpbin.org/ip",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    text = await resp.text()
                    print(f"HTTP request OK! Status: {resp.status}, Body: {text[:200]}")
            except Exception as e:
                print(f"HTTP request FAILED: {type(e).__name__}: {e}")
    except ImportError as e:
        print(f"aiohttp_socks import FAILED: {e}")
    except Exception as e:
        print(f"Test 2 FAILED: {type(e).__name__}: {e}")

    # Test 3: Get proxy from pool and try
    print("\n=== Test 3: Proxy pool -> crawl request ===")
    try:
        from app.crawler.proxy_pool import get_proxy_pool
        from app.crawler.engine import get_crawl_engine
        
        pool = await get_proxy_pool()
        print(f"Pool proxies: {len(pool._proxies)}")
        for p in pool._proxies:
            print(f"  - {p.host}:{p.port} ({p.protocol}, type={p.proxy_type}, alive={p.is_alive})")
        
        proxy = await pool.get_proxy(proxy_type="tor")
        if proxy:
            print(f"Got Tor proxy: {proxy.host}:{proxy.port} ({proxy.protocol})")
            
            # Try creating a session with this proxy
            engine = await get_crawl_engine()
            session = await engine._create_session(proxy)
            try:
                async with session.get(
                    "http://ifconfig.me",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    text = await resp.text()
                    print(f"Crawl engine request OK! Status: {resp.status}")
                    print(f"IP: {text[:100]}")
            except Exception as e:
                print(f"Crawl engine request FAILED: {type(e).__name__}: {e}")
            finally:
                await engine._close_session(session)
        else:
            print("No Tor proxy available!")
    except Exception as e:
        print(f"Test 3 FAILED: {type(e).__name__}: {e}")

asyncio.run(test())
