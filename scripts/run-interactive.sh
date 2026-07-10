#!/usr/bin/env bash
# DarkTrace - Interactive Runner
# Run this script and enter 'n' to stop the app

set -euo pipefail

PROJECT_DIR="/home/darktrace"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║          🛡️  DARKTRACE IS RUNNING               ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

echo "  🔗  Dashboard:      http://localhost:3000"
echo "  🔗  API:            http://localhost:8000"
echo "  🔗  API Docs:       http://localhost:8000/docs"
echo "  🔗  RabbitMQ Mgmt:  http://localhost:15672"
echo ""
echo "  👤  Email:    admin@darktrace.io"
echo "  🔑  Password: admin@123"
echo ""

docker ps --format 'table {{.Names}}\t{{.Status}}' | awk 'NR==1{print "  " $0} NR>1{print "  " $0}'

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  App is running. Enter [n] to stop it."
echo "═══════════════════════════════════════════════════════════"
echo ""

while true; do
  printf '  > Enter choice (n to stop, s for status, q to quit but keep running): '
  read -r input
  case "${input}" in
    n|N)
      echo ""
      echo "  Stopping DarkTrace..."
      cd "${PROJECT_DIR}" && docker compose -p darktrace down
      echo "  ✅ DarkTrace stopped."
      break
      ;;
    s|S)
      echo ""
      echo "  Current Status:"
      docker ps --format 'table {{.Names}}\t{{.Status}}' | awk 'NR==1{print "  " $0} NR>1{print "  " $0}'
      echo ""
      ;;
    q|Q)
      echo ""
      echo "  DarkTrace continues running in background."
      echo "  Reconnect with: wsl -d Ubuntu"
      echo "  Stop later with: cd /home/darktrace && docker compose -p darktrace down"
      break
      ;;
    *)
      echo "  Available: n = stop app, s = show status, q = quit (keep running)"
      ;;
  esac
done
