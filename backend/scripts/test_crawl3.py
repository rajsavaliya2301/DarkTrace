"""Trigger a crawl and monitor with minimal file changes."""
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
    print(f"Crawling: {target_url} ({target_id})")

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
    print(f"Queued: {r3.read().decode()[:200]}")

    # Wait and check
    for i in range(6):
        time.sleep(5)
        try:
            req4 = urllib.request.Request(
                f"{BASE}/v1/crawler/jobs?page=1&per_page=1",
                headers={"Authorization": f"Bearer {token}"},
            )
            r4 = urllib.request.urlopen(req4)
            jr = json.loads(r4.read())
            jobs = jr.get("data", [])
            if jobs:
                j = jobs[0]
                status = j.get("status", "?")
                pf = j.get("pages_fetched", 0)
                err = j.get("errors", 0)
                print(f"  [{i*5}s] status={status} pages={pf} errors={err}")
                if status in ("completed", "failed"):
                    # Check events
                    for ch in ["dashboard", "content"]:
                        try:
                            r5 = urllib.request.urlopen(f"{BASE}/events/poll?channel={ch}&limit=3")
                            pd = json.loads(r5.read())
                            if pd["count"] > 0:
                                print(f"  -> Poll '{ch}': {pd['count']} events!")
                                for ev in pd["events"][:1]:
                                    print(f"     {json.dumps(ev, default=str)[:120]}")
                        except:
                            pass
                    break
        except Exception as e:
            print(f"  [{i*5}s] Error: {e}")

    # Also check the job detail via direct DB query
    print("\nChecking backend logs directly...")
    try:
        req5 = urllib.request.Request(
            f"{BASE}/v1/crawler/jobs?page=1&per_page=1",
            headers={"Authorization": f"Bearer {token}"},
        )
        r5 = urllib.request.urlopen(req5)
        jr2 = json.loads(r5.read())
        jobs2 = jr2.get("data", [])
        if jobs2:
            j2 = jobs2[0]
            jid = j2.get("id", "")
            # Get job detail
            req6 = urllib.request.Request(
                f"{BASE}/v1/crawler/jobs/{jid}",
                headers={"Authorization": f"Bearer {token}"},
            )
            r6 = urllib.request.urlopen(req6)
            detail = json.loads(r6.read())
            print(f"Full detail keys: {list(detail.keys()) if isinstance(detail, dict) else '?'}")
            if isinstance(detail, dict):
                for k in ["status", "pages_fetched", "pages_failed", "errors", "started_at", "completed_at", "error_message"]:
                    if k in detail:
                        print(f"  {k}: {detail[k]}")
    except Exception as e:
        print(f"Detail error: {e}")

print("\nDone")
