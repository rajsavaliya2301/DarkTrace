#!/usr/bin/env python3
"""
Seed script: creates REAL crawl targets (surface web threat intel feeds)
and triggers immediate crawl jobs.

These are public, crawlable URLs containing cybersecurity threat intelligence
data (IOCs, threat actor info, malware reports) that the DarkTrace pipeline
will process through its enterprise ML models (spaCy TRF, BART zero-shot,
DistilBERT sentiment, 51-language translator).
"""
import json
import sys
import time
import urllib.request
import urllib.error

API_BASE = "http://localhost:8000/v1"
ADMIN_EMAIL = "admin@darktrace.com"
ADMIN_PASS = "raj@123"

# --- REAL CRAWL TARGETS ---
# These are publicly accessible cybersecurity threat intel feeds.
# The crawler fetches them, the NLP pipeline classifies, extracts entities,
# profiles actors, scores threats.
TARGETS = [
    {
        "url": "https://cve.mitre.org/data/downloads/allitems.txt",
        "site_name": "MITRE CVE Database",
        "source_type": "surface",
        "crawl_frequency": "every_24h",
        "parser_type": "generic",
        "notes": "Official MITRE CVE vulnerability database - all published CVEs with descriptions",
        "tags": ["cve", "vulnerability", "threat_intel"],
    },
    {
        "url": "https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
        "site_name": "Emerging Threats Blocklist",
        "source_type": "surface",
        "crawl_frequency": "every_12h",
        "parser_type": "generic",
        "notes": "Emerging Threats (Proofpoint) compromised IP blocklist - actively malicious hosts",
        "tags": ["blocklist", "compromised", "malware", "ips"],
    },
    {
        "url": "https://www.cisa.gov/sites/default/files/csv/known_exploited_vulnerabilities.csv",
        "site_name": "CISA KEV Catalog",
        "source_type": "surface",
        "crawl_frequency": "every_24h",
        "parser_type": "generic",
        "notes": "CISA Known Exploited Vulnerabilities catalog - vulnerabilities exploited in the wild",
        "tags": ["cisa", "kev", "vulnerability", "exploit"],
    },
    {
        "url": "https://otx.alienvault.com/api/v1/indicators/domain/www.google.com/general",
        "site_name": "AlienVault OTX Sample",
        "source_type": "surface",
        "crawl_frequency": "every_24h",
        "parser_type": "generic",
        "notes": "AlienVault OTX threat intelligence sample data",
        "tags": ["otx", "threat_intel", "indicators"],
    },
]


def make_request(method, path, token=None, body=None):
    """Make HTTP request to the API."""
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode()
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else "{}"
        try:
            error_detail = json.loads(error_body)
        except json.JSONDecodeError:
            error_detail = {"detail": error_body}
        print(f"  [WARN] HTTP {e.code}: {error_detail.get('detail', error_body)[:100]}")
        return e.code, error_detail
    except Exception as e:
        print(f"  [WARN] Error: {e}")
        return 0, {}


def main():
    print("=" * 60)
    print("DarkTrace - Real Crawl Target Seeder")
    print("=" * 60)

    # Step 1: Login
    print("\n[1/5] Authenticating as admin...")
    status, result = make_request("POST", "/auth/login", body={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS,
    })
    if status != 200:
        print(f"[FAIL] Login failed: {result.get('detail', 'unknown error')}")
        sys.exit(1)
    token = result.get("access_token")
    print(f"  [OK] Authenticated")

    # Step 2: Check existing targets
    print("\n[2/5] Checking existing targets...")
    status, result = make_request("GET", "/crawler/targets", token=token)
    existing_targets = result.get("results", result if isinstance(result, list) else [])
    print(f"  [OK] Found {len(existing_targets)} existing target(s)")

    # Step 3: Create new targets (skip duplicates)
    print("\n[3/5] Creating REAL crawl targets...")
    created_ids = []
    existing_urls = {t.get("url", "") for t in existing_targets}

    for target in TARGETS:
        if target["url"] in existing_urls:
            print(f"  [SKIP] Already exists: {target['site_name']}")
            continue

        print(f"  [ADD] {target['site_name']} ({target['url'][:60]}...)")
        status, result = make_request("POST", "/crawler/targets", token=token, body=target)

        if status == 201:
            target_id = result.get("id")
            created_ids.append((target_id, target["site_name"], target["url"]))
            print(f"    -> ID: {target_id[:8]}...")
        else:
            print(f"    -> Failed: {result.get('detail', 'unknown')[:80]}")

    if not created_ids:
        print("  [INFO] All targets already exist. Will re-crawl them.")
        for t in existing_targets:
            if t.get("source_type") == "surface" and t.get("status") == "active":
                created_ids.append((t["_id"], t.get("site_name", "unknown"), t.get("url", "")))

    # Step 4: Trigger immediate crawls
    print(f"\n[4/5] Triggering crawl jobs for {len(created_ids)} target(s)...")
    job_ids = []
    for target_id, site_name, url in created_ids:
        print(f"  [CRAWL] {site_name}...")
        status, result = make_request("POST", f"/crawler/targets/{target_id}/crawl", token=token)
        if status == 202:
            job_id = result.get("job_id")
            job_ids.append(job_id)
            print(f"    -> Job: {job_id[:8]}...")
        else:
            print(f"    -> {result.get('detail', 'trigger failed')[:80]}")

    if not job_ids:
        print("  [WARN] No jobs triggered.")
        sys.exit(0)

    # Step 5: Monitor job progress
    print(f"\n[5/5] Monitoring {len(job_ids)} crawl job(s) (checking every 15s)...")
    completed = set()

    for attempt in range(40):  # up to 10 minutes
        if len(completed) == len(job_ids):
            break

        time.sleep(15)

        for job_id in job_ids:
            if job_id in completed:
                continue

            status, result = make_request("GET", f"/crawler/jobs/{job_id}", token=token)
            if status != 200:
                continue

            job_status = result.get("status", "unknown")
            pages = result.get("pages_fetched", 0)
            errors = result.get("errors", [])

            if job_status == "completed":
                completed.add(job_id)
                print(f"  [DONE] {result.get('site_name', 'Job')[:30]:30s} completed ({pages} pages)")
            elif job_status == "failed":
                completed.add(job_id)
                err_msg = errors[0] if errors else "unknown"
                print(f"  [FAIL] {result.get('site_name', 'Job')[:30]:30s}: {str(err_msg)[:80]}")
            elif job_status == "in_progress":
                print(f"  [BUSY] {result.get('site_name', 'Job')[:30]:30s} fetching... ({pages} pages)")
            else:
                print(f"  [WAIT] {result.get('site_name', 'Job')[:30]:30s} {job_status}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Targets:         {len(created_ids)}")
    print(f"  Jobs completed:  {len(completed)}/{len(job_ids)}")
    print(f"  Jobs failed:     {len(job_ids) - len(completed)}")
    print()
    if completed == len(job_ids) and len(job_ids) > 0:
        print("All crawl jobs completed!")
        print("Content was processed through the enterprise ML pipeline:")
        print("  - spaCy en_core_web_trf (transformer NER)")
        print("  - facebook/bart-large-mnli (zero-shot threat classification)")
        print("  - distilbert-base-uncased-sst-2 (sentiment analysis)")
        print("  - 51-language translator with dark web preprocessing")
        print()
        print("Browse results at: http://localhost:80")
    else:
        print(f"{len(job_ids) - len(completed)} job(s) still running.")
        print("Check progress at: http://localhost:80/crawler")
    print()


if __name__ == "__main__":
    main()
