#!/usr/bin/env bash
# Test login API through frontend proxy

JSON_DATA='{"email":"admin@darktrace.com","password":"BqkwYUIslu5lAGw9iJDtVg"}'
printf "%s" "$JSON_DATA" > /tmp/login.json

echo "=== Test 1: Direct backend API ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d @/tmp/login.json

echo ""
echo "=== Test 2: Through nginx proxy ==="
curl -s -X POST http://localhost:80/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d @/tmp/login.json

echo ""
echo "=== Test 3: Frontend health check ==="
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:3000/

echo ""
echo "=== Test 4: Backend health check ==="
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8000/health

echo ""
echo "=== Test 5: Tor proxy status ==="
curl -s --socks5-hostname localhost:9050 --max-time 10 https://check.torproject.org/api/ip 2>&1 || echo "Tor not yet ready"

rm -f /tmp/login.json
