#!/usr/bin/env bash

# Test with a normal email domain
echo "=== Login with real domain ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"BqkwYUIslu5lAGw9iJDtVg"}'

echo ""
echo "=== Register if needed ==="
curl -s -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"BqkwYUIslu5lAGw9iJDtVg","name":"Admin"}'

echo ""
echo "=== Check what endpoints exist ==="
curl -s http://localhost:8000/openapi.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('\n'.join(d.get('paths',{}).keys()))" 2>&1 || curl -s http://localhost:8000/openapi.json | python3 -m json.tool 2>/dev/null | head -30

echo ""
echo "=== Try GET /v1/ ==="
curl -s http://localhost:8000/v1/ 2>&1

echo ""
echo "=== Try GET / ==="
curl -s http://localhost:8000/ 2>&1
