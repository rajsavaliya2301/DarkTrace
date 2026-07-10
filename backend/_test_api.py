"""Quick script to test the running DarkTrace API."""
import urllib.request
import json

BASE = "http://localhost:8000"

# Health
r = urllib.request.urlopen(f"{BASE}/health", timeout=5)
print("=== /health ===")
print(r.read().decode())
print()

# Root
r = urllib.request.urlopen(f"{BASE}/", timeout=5)
print("=== / ===")
print(r.read().decode())
print()

# OpenAPI spec
r = urllib.request.urlopen(f"{BASE}/openapi.json", timeout=5)
spec = json.loads(r.read())
print(f"=== OpenAPI: {spec['info']['title']} v{spec['info']['version']} ===")
print(f"Total endpoints: {len(spec['paths'])}")
print()

# List all routes
for path, methods in sorted(spec['paths'].items()):
    for method in methods:
        print(f"  {method.upper():6s} {path}")
print()

# Test login endpoint
try:
    data = json.dumps({"email": "admin@darktrace.com", "password": "raj@123"}).encode()
    req = urllib.request.Request(f"{BASE}/v1/auth/login", data=data, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=5)
    result = json.loads(r.read())
    print("=== Login Successful ===")
    print(f"User: {result['user']['name']} ({result['user']['role']})")
    print(f"Token: {result['access_token'][:20]}...")
except Exception as e:
    print(f"=== Login Error (expected in testing mode): {e} ===")
