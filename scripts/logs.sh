#!/usr/bin/env bash
# =============================================================================
# DarkTrace - Logs Script
# =============================================================================
# Tail logs from all DarkTrace services or a specific service.
#
# Usage:
#   ./scripts/logs.sh              # Follow all services
#   ./scripts/logs.sh backend      # Follow specific service
#   ./scripts/logs.sh -n 100       # Show last 100 lines (all services)
#   ./scripts/logs.sh -n 50 backend  # Show last 50 lines of backend
#
# Services:
#   backend, frontend, mongodb, elasticsearch, neo4j, redis,
#   rabbitmq, crawler-worker, nlp-worker
# =============================================================================

set -euo pipefail

# ─── Color output ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE=""
TAIL_LINES=""
FOLLOW=true

# ─── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--lines)
      TAIL_LINES="$2"
      FOLLOW=false
      shift 2
      ;;
    -f|--follow)
      FOLLOW=true
      shift
      ;;
    -h|--help)
      echo "DarkTrace - Logs Viewer"
      echo ""
      echo "Usage: $0 [options] [service]"
      echo ""
      echo "Options:"
      echo "  -n, --lines NUM   Show last NUM lines (default: follow mode)"
      echo "  -f, --follow      Follow log output (default)"
      echo "  -h, --help        Show this help message"
      echo ""
      echo "Services:"
      echo "  backend, frontend, mongodb, elasticsearch, neo4j, redis,"
      echo "  rabbitmq, crawler-worker, nlp-worker"
      echo ""
      echo "Examples:"
      echo "  $0                    # Follow all services"
      echo "  $0 backend            # Follow backend logs"
      echo "  $0 -n 50 backend      # Show last 50 lines of backend"
      echo "  $0 -n 100             # Show last 100 lines of all services"
      exit 0
      ;;
    *)
      if [ -z "$SERVICE" ]; then
        SERVICE="$1"
      else
        error "Unknown argument: $1"
        exit 1
      fi
      shift
      ;;
  esac
done

# ─── Validate Docker Compose is running ──────────────────────────────────────
if ! docker compose -p darktrace ps --services 2>/dev/null | grep -q .; then
  error "No DarkTrace containers running. Start with: ./scripts/setup.sh"
  exit 1
fi

cd "${PROJECT_DIR}"

# ─── Build log arguments ─────────────────────────────────────────────────────
COMPOSE_ARGS=()

if [ -n "$SERVICE" ]; then
  # Validate service exists
  if ! docker compose -p darktrace ps --services 2>/dev/null | grep -q "^${SERVICE}$"; then
    error "Unknown service: '${SERVICE}'"
    echo ""
    echo "Available services:"
    docker compose -p darktrace ps --services 2>/dev/null | while read -r svc; do
      echo "  - $svc"
    done
    exit 1
  fi
  COMPOSE_ARGS+=("$SERVICE")
fi

if [ "$FOLLOW" = true ]; then
  COMPOSE_ARGS+=("--follow")
fi

if [ -n "$TAIL_LINES" ]; then
  COMPOSE_ARGS+=("--tail" "$TAIL_LINES")
fi

# If no specific service, show all
if [ -z "$SERVICE" ]; then
  info "Tailing logs for ALL services..."
  echo "───────────────────────────────────────────────"
  docker compose -p darktrace logs "${COMPOSE_ARGS[@]}"
else
  info "Tailing logs for service: ${SERVICE}"
  echo "───────────────────────────────────────────────"
  docker compose -p darktrace logs "${COMPOSE_ARGS[@]}"
fi
