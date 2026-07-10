"""Trigger crawls for high-priority clearnet targets and verify pipeline."""
import asyncio
import httpx
import json

BASE = "http://localhost:8000/v1"

async def main():
    async with httpx.AsyncClient() as client:
        # Login
        resp = await client.post(f"{BASE}/auth/login", json={
            "email": "admin@darktrace.com",
            "password": "raj@123"
        })
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Logged in successfully")

        # Step 1: Get all targets
        resp = await client.get(f"{BASE}/crawler/targets", headers=headers)
        targets = resp.json().get("data", [])
        print(f"Total targets: {len(targets)}")

        # Priority categories (clearnet sources most likely to return text)
        priority_categories = [
            "vulnerability", "ip_reputation", "security_blog",
            "government_cert", "threat_intel", "osint_cti",
        ]

        priority_targets = [
            t for t in targets
            if t.get("category") in priority_categories
            and not t.get("use_tor", False)
            and t.get("status") != "disabled"
        ]
        print(f"Priority clearnet targets: {len(priority_targets)}")
        for t in priority_targets[:10]:
            print(f"  [{t.get('category','?')}] {t.get('site_name','?')[:50]} | {t.get('url','?')[:70]}")

        # Step 2: Trigger crawls for 15 targets
        crawl_count = min(15, len(priority_targets))
        print(f"\nTriggering crawls for {crawl_count} targets...")
        job_ids = []
        for t in priority_targets[:crawl_count]:
            try:
                resp = await client.post(
                    f"{BASE}/crawler/targets/{t['id']}/crawl",
                    headers=headers, timeout=30
                )
                if resp.status_code == 202:
                    jid = resp.json().get("job_id", "?")
                    job_ids.append(jid)
                    print(f"  [OK] {t.get('site_name','?')[:40]} -> job {str(jid)[:12]}")
                else:
                    print(f"  [FAIL {resp.status_code}] {t.get('site_name','?')[:40]}: {resp.text[:80]}")
            except Exception as e:
                print(f"  [ERROR] {t.get('site_name','?')[:40]}: {e}")

        print(f"\nTriggered {len(job_ids)} jobs. Monitoring for 120s...")

        # Step 3: Monitor progress with search endpoint
        for i in range(12):
            await asyncio.sleep(10)
            
            # Search for any processed content
            resp = await client.get(f"{BASE}/search", params={"q": "exploit OR CVE OR malware OR compromised OR vulnerability", "page": 1, "per_page": 5}, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                total = data.get("pagination", {}).get("total", 0)
                docs = data.get("data", [])
                print(f"  [{i+1}/12] Search total={total}")
                for d in docs[:3]:
                    print(f"    [{d.get('id','?')[:12]}] {str(d.get('title','') or d.get('snippet',''))[:60]}")
                    if data.get('facets'):
                        cats = {k: [b.get('value','') for b in v[:3]] for k,v in data['facets'].items() if v}
                        print(f"    Facets: {json.dumps(cats)}")
            elif resp.status_code == 502:
                print(f"  [{i+1}/12] Search: 502 (aggregation error - need to wait for data)")
            else:
                print(f"  [{i+1}/12] Search: {resp.status_code} {resp.text[:100]}")

            # Check jobs
            if job_ids and i % 2 == 0:
                for jid in job_ids[:3]:
                    resp = await client.get(f"{BASE}/crawler/jobs/{jid}", headers=headers, timeout=10)
                    if resp.status_code == 200:
                        j = resp.json()
                        print(f"    Job {str(jid)[:12]}: status={j.get('status','?')} pages={j.get('pages_fetched',0)} errors={j.get('errors',0)}")

        # Step 4: Final summary
        print("\n=== FINAL SUMMARY ===")
        for q in ["exploit", "CVE", "malware", "compromised", "vulnerability"]:
            resp = await client.get(f"{BASE}/search", params={"q": q, "page": 1, "per_page": 3}, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                print(f"Search '{q}': {data['pagination']['total']} hits")
                for r in data.get('data', [])[:2]:
                    print(f"  [{r.get('id','?')[:12]}] {str(r.get('title','') or r.get('snippet',''))[:50]} | score={r.get('score',0)}")
                if data.get('facets'):
                    for k, v in data['facets'].items():
                        if v:
                            print(f"  {k}: {[b.get('value','') for b in v[:5]]}")
        else:
            print(f"Search FAILED: {resp.status_code} {resp.text[:200]}")

if __name__ == "__main__":
    asyncio.run(main())
