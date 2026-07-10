"""Check job status and poll events."""
import urllib.request
import json

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
print("Logged in")

# Check jobs
req = urllib.request.Request(
    f"{BASE}/v1/crawler/jobs",
    headers={"Authorization": f"Bearer {token}"},
)
try:
    r = urllib.request.urlopen(req)
    jobs_raw = json.loads(r.read())
    if isinstance(jobs_raw, dict):
        jobs = jobs_raw.get("jobs", jobs_raw.get("data", []))
    else:
        jobs = jobs_raw
    print(f"Total jobs: {len(jobs)}")
    for j in jobs[:5]:
        jid = j.get("id", j.get("_id", "?"))
        status = j.get("status", "?")
        url = j.get("target_url", j.get("url", "?"))
        print(f"  Job {jid}: {status} - {url}")
except Exception as e:
    print(f"Jobs error: {e}")

# Check poll events
for ch in ["dashboard", "content", "actor", "alert"]:
    try:
        r = urllib.request.urlopen(f"{BASE}/events/poll?channel={ch}&limit=3")
        data = json.loads(r.read())
        events = data.get("events", [])
        print(f"Poll '{ch}': {data['count']} events")
        for ev in events[:2]:
            print(f"    -> {ev.get('type', '?')}: {json.dumps(ev)[:100]}")
    except Exception as e:
        print(f"Poll '{ch}' error: {e}")
