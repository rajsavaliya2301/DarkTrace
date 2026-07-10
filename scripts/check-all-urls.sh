#!/usr/bin/env bash
# Comprehensive URL check in the frontend bundle

JS_FILE="/usr/share/nginx/html/assets/index-BFgkdGaK.js"

echo "=== All ws:// URLs ==="
grep -oE 'ws://[^"'"'"',;]+' "$JS_FILE" 2>/dev/null | sort -u

echo ""
echo "=== All http:// URLs (excluding common CDNs) ==="
grep -oE 'http://[^"'"'"',;]+' "$JS_FILE" 2>/dev/null | grep -vE 'w3\.org|opensource|en\.wikipedia|engelschall|fb\.me|example\.onion' | sort -u

echo ""
echo "=== All https:// URLs (excluding common CDNs) ==="
grep -oE 'https://[^"'"'"',;]+' "$JS_FILE" 2>/dev/null | grep -vE 'github|w3\.org|fonts\.googleapis|reactjs|jquery|date-fns|tldrlegal' | sort -u

echo ""
echo "=== Any reference to :8000 ==="
grep -oE '[^"'"'"',;]*8000[^"'"'"',;]*' "$JS_FILE" 2>/dev/null | sort -u

echo ""
echo "=== Any reference to localhost: ==="
grep -oE 'localhost:[0-9]+' "$JS_FILE" 2>/dev/null | sort -u

echo ""
echo "=== Any reference to /api/ ==="
grep -oE '/api/[a-zA-Z0-9_/]+' "$JS_FILE" 2>/dev/null | sort -u

echo ""
echo "=== Is VITE_API_BASE_URL or VITE_WS_BASE_URL in bundle? ==="
grep -oE 'VITE_[A-Z_]+' "$JS_FILE" 2>/dev/null | sort -u
