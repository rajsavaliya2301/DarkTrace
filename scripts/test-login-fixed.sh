#!/usr/bin/env bash
# Test login after fixing admin email

echo "=== Login with fixed email: admin@darktrace.io ==="
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darktrace.io","password":"BqkwYUIslu5lAGw9iJDtVg"}'

echo ""
echo ""
echo "=== Check MongoDB for admin user ==="
docker exec darktrace-mongodb mongosh --quiet -u darktrace -p darktrace_pass --authenticationDatabase admin --eval 'db.getSiblingDB("darktrace").users.find().pretty()' 2>&1
