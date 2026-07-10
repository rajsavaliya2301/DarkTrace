#!/usr/bin/env bash

echo "=== Test 1: admin@darktrace.com (original) ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.com","password":"BqkwYUIslu5lAGw9iJDtVg"}'

echo ""
echo "=== Test 2: admin@darktrace.test ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.test","password":"BqkwYUIslu5lAGw9iJDtVg"}'

echo ""
echo "=== Test 3: admin@darktrace.io ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"BqkwYUIslu5lAGw9iJDtVg"}'  

echo ""
echo "=== Test 4: Check /v1/auth/register endpoint ==="
curl -s -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"BqkwYUIslu5lAGw9iJDtVg","name":"Admin"}'
