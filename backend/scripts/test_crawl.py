"""Test end-to-end crawl flow."""
import urllib.request
import json
import sys

BASE = "http://localhost:8000"

# Login
req = urllib.request.Request(
    f"{BASE}/v1/auth/login",
    data=json.dumps({"email": "admin@darktrace.com", "password": "raj@123"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
r = urllib.request.urlopen(req)
token = json.loads(r.read())["access_token"]
print("Login OK, got token")

# Check crawl targets
req2 = urllib.request.Request(
    f"{BASE}/v1/crawler/targets",
    headers={"Authorization": f"Bearer {token}"},
)
r2 = urllib.request.urlopen(req2)
targets_raw = json.loads(r2.read())
print(f"Raw response keys: {list(targets_raw.keys()) if isinstance(targets_raw, dict) else 'list'}")
if isinstance(targets_raw, dict):
    targets = targets_raw.get("targets", targets_raw.get("data", []))
else:
    targets = targets_raw
print(f"Found {len(targets)} crawl targets")
if targets:
    print(f"First target full keys: {list(targets[0].keys())}")
for t in targets[:3]:
    tid = t.get("_id", t.get("id", "?"))
    url = t.get("url", "?")
    typ = t.get("type", t.get("source_type", "?"))
    print(f"  - {tid}: {url} (type: {typ})")

# Try to trigger a crawl
if targets:
    target = targets[0]
    target_id = target.get("id", "")
    target_url = target.get("url", "")
    print(f"\nTriggering crawl for: {target_url} (id: {target_id})")

    req3 = urllib.request.Request(
        f"{BASE}/v1/crawler/targets/{target_id}/crawl",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        r3 = urllib.request.urlopen(req3)
        print(f"Crawl response ({r3.status}): {r3.read().decode()[:500]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Crawl error ({e.code}): {body[:500]}")

# Check poll events
print("\nChecking poll events...")
r4 = urllib.request.urlopen(f"{BASE}/events/poll?channel=dashboard&limit=5")
print(f"Poll dashboard: {r4.read().decode()}")

r5 = urllib.request.urlopen(f"{BASE}/events/poll?channel=content&limit=5")
print(f"Poll content: {r5.read().decode()}")
