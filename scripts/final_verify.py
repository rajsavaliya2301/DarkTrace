"""Final verification of the complete system."""
import httpx, json

BASE = "http://localhost:8000/v1"
r = httpx.post(f"{BASE}/auth/login", json={"email": "admin@darktrace.com", "password": "raj@123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

print("=== 1. JOBS STATUS ===")
r = httpx.get(f"{BASE}/crawler/jobs", params={"status_filter": "completed", "per_page": 20}, headers=h)
if r.status_code == 200:
    jobs = r.json().get("data", [])
    print(f"Completed jobs: {len(jobs)}")
    for j in jobs:
        print(f"  {j['id'][:12]}: pages={j['pages_fetched']} errors={j['errors']} url={j['target_url'][:50]}")

r = httpx.get(f"{BASE}/crawler/jobs", params={"status_filter": "in_progress", "per_page": 20}, headers=h)
if r.status_code == 200:
    jobs = r.json().get("data", [])
    print(f"In-progress jobs: {len(jobs)}")
    for j in jobs:
        print(f"  {j['id'][:12]}: url={j['target_url'][:50]}")

r = httpx.get(f"{BASE}/crawler/jobs", params={"status_filter": "failed", "per_page": 20}, headers=h)
if r.status_code == 200:
    jobs = r.json().get("data", [])
    print(f"Failed jobs: {len(jobs)}")
    for j in jobs:
        print(f"  {j['id'][:12]}: url={j['target_url'][:50]}")

print("\n=== 2. SEARCH RESULTS ===")
queries = [
    ("exploit", "exploit"),
    ("CVE", "CVE"),
    ("malware", "malware"),
    ("compromised", "compromised"),
    ("vulnerability", "vulnerability"),
    ("ransomware", "ransomware"),
]
for q, label in queries:
    r = httpx.get(f"{BASE}/search", params={"q": q, "per_page": 5}, headers=h)
    if r.status_code == 200:
        d = r.json()
        print(f"'{q}': {d['pagination']['total']} hits")
        if d.get('facets'):
            for k, v in d['facets'].items():
                if v:
                    vals = [f"{b['value']}({b['count']})" for b in v[:5]]
                    print(f"  {k}: {', '.join(vals)}")

print("\n=== 3. TARGETS SUMMARY ===")
r = httpx.get(f"{BASE}/crawler/targets", headers=h)
targets = r.json().get("data", [])
categories = {}
tor_count = 0
for t in targets:
    cats = t.get("category", "unknown")
    categories[cats] = categories.get(cats, 0) + 1
    if t.get("use_tor", False):
        tor_count += 1

print(f"Total targets: {len(targets)} ({tor_count} Tor, {len(targets)-tor_count} clearnet)")
for c, n in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {c}: {n}")

print("\n=== 4. SYSTEM HEALTH ===")
r = httpx.get("http://localhost:8000/health", headers=h)
if r.status_code == 200:
    print(f"Backend: {r.json()}")
else:
    print(f"Backend: {r.status_code}")

print("\n✅ Verification complete!")
