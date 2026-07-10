"""Trigger a fresh crawl and monitor pipeline events."""
import urllib.request
import json
import time
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
print("Logged in")

# Get targets
req2 = urllib.request.Request(
    f"{BASE}/v1/crawler/targets",
    headers={"Authorization": f"Bearer {token}"},
)
r2 = urllib.request.urlopen(req2)
targets_raw = json.loads(r2.read())
targets = targets_raw.get("data", [])
if targets:
    target = targets[0]
    target_id = target.get("id", "")
    target_url = target.get("url", "")
    print(f"Triggering crawl for: {target_url} ({target_id})")

    # Trigger crawl
    req3 = urllib.request.Request(
        f"{BASE}/v1/crawler/targets/{target_id}/crawl",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    r3 = urllib.request.urlopen(req3)
    print(f"Crawl queued: {r3.read().decode()[:200]}")

    # Wait and poll for events
    for i in range(12):
        time.sleep(5)
        
        # Check job status
        try:
            req4 = urllib.request.Request(
                f"{BASE}/v1/crawler/jobs?limit=1",
                headers={"Authorization": f"Bearer {token}"},
            )
            r4 = urllib.request.urlopen(req4)
            jobs_raw = json.loads(r4.read())
            jobs = jobs_raw.get("jobs", jobs_raw.get("data", [jobs_raw]))
            if jobs:
                j = jobs[0] if isinstance(jobs, list) else jobs
                status = j.get("status", "?")
                print(f"  [{i*5}s] Job status: {status}")
                if status == "completed":
                    break
        except Exception as e:
            print(f"  [{i*5}s] Job check error: {e}")

        # Check poll events
        for ch in ["dashboard", "content"]:
            try:
                r5 = urllib.request.urlopen(f"{BASE}/events/poll?channel={ch}&limit=3")
                data = json.loads(r5.read())
                if data["count"] > 0:
                    print(f"  [{i*5}s] Poll '{ch}': {data['count']} events!")
                    for ev in data["events"][:2]:
                        print(f"    --> {ev.get('type', '?')}")
            except Exception as e:
                pass

print("\nDone monitoring")
