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
    status = j.get("status", "?")
    errors = j.get("errors", [])
    pages = j.get("pages_fetched", 0)
    print(f"Job {jid}: status={status} pages_fetched={pages}")
    if errors:
        for e in errors[:3]:
            if isinstance(e, dict):
                print(f"  Error: {e.get('message', str(e))[:200]}")
            else:
                print(f"  Error: {str(e)[:200]}")
