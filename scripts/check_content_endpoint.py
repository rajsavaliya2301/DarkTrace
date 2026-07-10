"""Check what content/search endpoints exist."""
import httpx, json

BASE = "http://localhost:8000/v1"
r = httpx.post(f"{BASE}/auth/login", json={"email": "admin@darktrace.com", "password": "raj@123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Check which crawler/job paths exist
paths_to_check = [
    "/crawler/content",
    "/crawler/jobs",
    "/crawler/targets",
    "/search",
    "/alerts",
    "/dashboard",
]

for path in paths_to_check:
    r = httpx.get(f"{BASE}{path}", headers=h)
    print(f"{path}: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        if isinstance(d, dict) and "data" in d:
            print(f"  Items: {len(d['data'])}")
            if d["data"]:
                print(f"  Sample keys: {list(d['data'][0].keys())[:10]}")
