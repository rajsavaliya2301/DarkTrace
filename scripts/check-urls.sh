#!/usr/bin/env bash
echo "=== URLs in JS bundle ==="
docker exec darktrace-frontend grep -oE 'https?://[^"'"'"',;]+' /usr/share/nginx/html/assets/index-BFgkdGaK.js 2>/dev/null | sort -u

echo ""
echo "=== localhost references ==="
docker exec darktrace-frontend grep -oE 'localhost[^"'"'"',;]*' /usr/share/nginx/html/assets/index-BFgkdGaK.js 2>/dev/null | sort -u

echo ""
echo "=== :8000 references ==="
docker exec darktrace-frontend grep -oE '[^"'"'"']*8000[^"'"'"']*' /usr/share/nginx/html/assets/index-BFgkdGaK.js 2>/dev/null | sort -u
