#!/usr/bin/env bash
# =============================================================================
# DarkTrace - Reset Script
# =============================================================================
# Stops all containers, removes volumes (data), and cleans up.
# WARNING: This will DELETE ALL DATA! Use with caution.
#
# Usage:
#   chmod +x scripts/reset.sh
#   ./scripts/reset.sh          # Interactive (prompts for confirmation)
#   ./scripts/reset.sh --force  # Skip confirmation prompt
#   ./scripts/reset.sh --help   # Show help
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
FORCE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=true; shift ;;
    --help)
      echo "DarkTrace - Reset Script"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --force    Skip confirmation prompt"
      echo "  --help     Show this help message"
      echo ""
      echo "WARNING: This script deletes ALL DATA (volumes)!"
      exit 0
      ;;
    *) error "Unknown option: $1"; exit 1 ;;
  esac
done

echo ""
echo "=============================================="
echo "  DarkTrace - Reset"
echo "=============================================="
echo ""

# ─── Confirmation ────────────────────────────────────────────────────────────
if [ "$FORCE" = false ]; then
  echo -e "${RED}╔══════════════════════════════════════════════════╗${NC}"
  echo -e "${RED}║     WARNING: This will DELETE ALL DATA!         ║${NC}"
  echo -e "${RED}╚══════════════════════════════════════════════════╝${NC}"
  echo ""
  read -r -p "Are you sure you want to continue? [y/N] " response
  case "$response" in
    [yY][eE][sS]|[yY])
      echo ""
      ;;
    *)
      info "Reset cancelled."
      exit 0
      ;;
  esac
fi

# ─── Step 1: Stop and remove containers ──────────────────────────────────────
info "Stopping and removing containers..."
cd "${PROJECT_DIR}"

if docker compose -p darktrace ps &>/dev/null 2>&1; then
  docker compose -p darktrace down --remove-orphans 2>/dev/null || true
  ok "Containers stopped and removed."
else
  warn "No running DarkTrace containers found."
fi

# ─── Step 2: Remove volumes ──────────────────────────────────────────────────
info "Removing Docker volumes..."
VOLUMES=$(docker volume ls --filter "name=darktrace_" --format "{{.Name}}" 2>/dev/null || true)
if [ -n "$VOLUMES" ]; then
  for vol in $VOLUMES; do
    docker volume rm "$vol" 2>/dev/null || warn "Could not remove volume: $vol"
  done
  ok "Docker volumes removed."
else
  warn "No darktrace_ volumes found."
fi

# ─── Step 3: Remove networks ─────────────────────────────────────────────────
info "Removing Docker networks..."
for net in darktrace_frontend darktrace_backend darktrace_data; do
  docker network rm "$net" 2>/dev/null || true
done
ok "Docker networks removed."

# ─── Step 4: Clean up dangling images (optional) ─────────────────────────────
info "Cleaning up dangling images..."
docker image prune -f --filter "label=com.docker.compose.project=darktrace" 2>/dev/null || true
ok "Dangling images cleaned."

# ─── Step 5: Remove local data (optional) ────────────────────────────────────
if [ -d "${PROJECT_DIR}/data" ]; then
  warn "Local 'data/' directory found. Remove it manually if needed."
fi

echo ""
ok "DarkTrace has been fully reset."
echo ""
info "To start fresh, run: ./scripts/setup.sh"
echo ""
