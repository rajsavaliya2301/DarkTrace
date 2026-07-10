#!/usr/bin/env bash
echo "=== Test login with admin@123 ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"admin@123"}'
echo ""
echo "=== Test through nginx proxy ==="
curl -s -X POST http://localhost:80/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"admin@123"}'
