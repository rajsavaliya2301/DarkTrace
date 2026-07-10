#!/usr/bin/env bash
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"BqkwYUIslu5lAGw9iJDtVg=="}'
echo ""
