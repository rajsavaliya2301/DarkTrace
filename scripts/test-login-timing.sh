#!/usr/bin/env bash
# Test login with timeout
echo "=== Login with 5s timeout ==="
curl -v --max-time 5 -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"admin@123"}' 2>&1

echo ""
echo "=== Exit code: $? ==="
