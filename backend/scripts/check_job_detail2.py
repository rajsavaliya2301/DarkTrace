"""Check job details."""
import urllib.request
import json

BASE = "http://localhost:8000"
req = urllib.request.Request(
    f"{BASE}/v1/auth/login",
    data=json.dumps({"email": "admin@darktrace.com", "password": "raj@123"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
r = urllib.request.urlopen(req)
token = json.loads(r.read())["access_token"]

req2 = urllib.request.Request(
    f"{BASE}/v1/crawler/jobs?page=1&per_page=5",
    headers={"Authorization": f"Bearer {token}"},
)
r2 = urllib.request.urlopen(req2)
res = json.loads(r2.read())
data = res.get("data", [])
for j in data[:3]:
    jid = j.get("id", "?")
    print(f"\n=== Job {jid} ===")
    for k, v in j.items():
        if k in ("errors",):
            print(f"  {k}: {json.dumps(v, default=str)[:300]}")
        elif k in ("status", "pages_fetched", "pages_failed", "started_at", "completed_at", "target_url"):
            print(f"  {k}: {v}")
