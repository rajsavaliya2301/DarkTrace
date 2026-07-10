#!/usr/bin/env bash
echo "=== With == at end ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"BqkwYUIslu5lAGw9iJDtVg=="}'

echo ""
echo "=== Without == at end ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"BqkwYUIslu5lAGw9iJDtVg"}'

echo ""
echo "=== With original .local ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.com","password":"BqkwYUIslu5lAGw9iJDtVg=="}'
