"""Test the search endpoint."""
import httpx
import json

BASE = "http://localhost:8000/v1"

def main():
    # Login with correct password
    resp = httpx.post(f"{BASE}/auth/login", json={"email": "admin@darktrace.com", "password": "raj@123"})
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        return
    token = resp.json()["access_token"]
    print(f"Got token: {token[:30]}...")

    # Test search
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE}/search", params={"q": "exploit", "page": 1, "per_page": 5}, headers=headers)
    print(f"Search status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total hits: {data['pagination']['total']}")
        for r in data['data'][:3]:
            print(f"  [{r['id'][:12]}]{str(r.get('title','?'))[:60]} | score={r['score']} | category={r.get('category','?')}")
        print(f"Facets: {json.dumps(data['facets'], indent=2)}")
    elif resp.status_code == 503:
        print(f"Search unavailable: {resp.text}")
    else:
        print(f"Search error: {resp.status_code} {resp.text}")

    # Test search for emerging threats
    resp2 = httpx.get(f"{BASE}/search", params={"q": "compromised", "page": 1, "per_page": 5}, headers=headers)
    print(f"\nSearch 'compromised' status: {resp2.status_code}")
    if resp2.status_code == 200:
        data2 = resp2.json()
        print(f"Total hits: {data2['pagination']['total']}")
        for r in data2['data'][:3]:
            print(f"  [{r['id'][:12]}]{str(r.get('title','?'))[:60]} | score={r['score']}")

if __name__ == "__main__":
    main()
