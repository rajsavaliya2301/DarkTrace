"""Debug API endpoints."""
import httpx, json

BASE = "http://localhost:8000/v1"

r = httpx.post(f"{BASE}/auth/login", json={"email": "admin@darktrace.com", "password": "raj@123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Check targets
r = httpx.get(f"{BASE}/crawler/targets", headers=h)
data = r.json()
targets = data.get("data", []) if isinstance(data, dict) else data
print(f"Targets: {len(targets)}")
if targets:
    t = targets[0]
    print(f"Keys: {list(t.keys())}")
    # Print category and use_tor info
    for t in targets[:5]:
        print(f"  [{t.get('category','?')}] {t.get('site_name','?')[:40]} use_tor={t.get('use_tor','NOT_FOUND')} tor_config={t.get('tor_config','NOT_FOUND')} proxy={t.get('proxy','NOT_FOUND')}")

# Check content endpoint
for path in ["/content", "/crawler/content", "/search/content"]:
    r = httpx.get(f"{BASE}{path}", headers=h)
    print(f"{path}: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        if isinstance(d, dict):
            print(f"  Keys: {list(d.keys())}")
            dd = d.get("data", d)
            if isinstance(dd, list):
                print(f"  Items: {len(dd)}")

# Check openapi
r = httpx.get("http://localhost:8000/openapi.json", headers=h)
if r.status_code == 200:
    paths = list(r.json().get("paths", {}).keys())
    relevant = [p for p in paths if any(x in p for x in ["content", "crawl", "target"])]
    print(f"\nRelevant API paths: {relevant}")
