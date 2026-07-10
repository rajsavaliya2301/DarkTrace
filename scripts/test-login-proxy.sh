#!/usr/bin/env bash
# Test login through nginx proxy
echo "=== Login through nginx proxy with 5s timeout ==="
curl -v --max-time 5 -X POST http://localhost:80/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "Host: localhost:3000" \
  -d '{"email":"admin@darktrace.io","password":"admin@123"}' 2>&1

echo ""
echo "=== Exit code: $? ==="
