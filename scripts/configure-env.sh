#!/usr/bin/env bash
set -euo pipefail

cd /home/darktrace

# Generate a secure SECRET_KEY
SECRET_KEY=$(openssl rand -hex 64)
echo "Generated SECRET_KEY: $SECRET_KEY"

# Update .env with secure values
sed -i "s|SECRET_KEY=change-this-to-a-strong-random-secret-in-production|SECRET_KEY=${SECRET_KEY}|" .env

# Ensure Tor proxy settings are correct (points to container)
sed -i 's|TOR_PROXY_HOST=.*|TOR_PROXY_HOST=tor-proxy|' .env
sed -i 's|TOR_PROXY_PORT=.*|TOR_PROXY_PORT=9050|' .env

# Generate a random admin password
ADMIN_PASS=$(openssl rand -base64 16)
sed -i "s|DEFAULT_ADMIN_PASSWORD=changeme_admin_password|DEFAULT_ADMIN_PASSWORD=${ADMIN_PASS}|" .env

# Verify the file
grep -E 'SECRET_KEY=|TOR_PROXY_|DEFAULT_ADMIN_PASSWORD' .env

echo ""
echo ".env configured successfully"
echo "Admin password: ${ADMIN_PASS}"
