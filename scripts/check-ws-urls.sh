#!/usr/bin/env bash
echo "=== WebSocket URLs ==="
grep -oE 'ws://[^"'"'"',;]+' /usr/share/nginx/html/assets/index-BFgkdGaK.js 2>/dev/null | sort -u

echo ""
echo "=== All API URLs ==="
grep -oE '[a-z]+://[^"'"'"',;]+' /usr/share/nginx/html/assets/index-BFgkdGaK.js 2>/dev/null | grep -vi 'github\|w3\.org\|reactjs\|jquery\|date-fns\|engelschall\|opensource\|tldrlegal\|wikipedia\|fb\.me\|example\.onion' | sort -u
