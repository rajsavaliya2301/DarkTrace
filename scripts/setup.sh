#!/usr/bin/env bash
# =============================================================================
# DarkTrace - Initial Setup Script
# =============================================================================
# This script performs the initial project setup:
#   1. Creates necessary directories
#   2. Copies .env.example to .env if not exists
#   3. Installs backend Python dependencies
#   4. Installs frontend Node.js dependencies
#   5. Builds and starts all Docker containers
#
# Usage:
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh
#
# Options:
#   --no-docker    Skip Docker build/start (useful for CI)
#   --dev          Install dev dependencies and start with hot-reload
#   --help         Show this help message
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

# ─── Parse arguments ─────────────────────────────────────────────────────────
SKIP_DOCKER=false
DEV_MODE=false
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-docker) SKIP_DOCKER=true; shift ;;
    --dev)       DEV_MODE=true; shift ;;
    --help)
      echo "DarkTrace - Setup Script"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --no-docker    Skip Docker build/start (useful for CI)"
      echo "  --dev          Install dev dependencies and start with hot-reload"
      echo "  --help         Show this help message"
      exit 0
      ;;
    *) error "Unknown option: $1"; exit 1 ;;
  esac
done

echo ""
echo "=============================================="
echo "  DarkTrace - Initial Setup"
echo "=============================================="
echo ""

# ─── Step 1: Create necessary directories ────────────────────────────────────
info "Creating project directories..."
mkdir -p "${PROJECT_DIR}"/{scripts,monitoring/grafana-dashboards,.github/workflows}
mkdir -p "${PROJECT_DIR}"/backend/{app,tests}
mkdir -p "${PROJECT_DIR}"/frontend/src
ok "Directories created."

# ─── Step 2: Copy .env.example to .env ───────────────────────────────────────
if [ ! -f "${PROJECT_DIR}/.env" ]; then
  info "Creating .env from .env.example..."
  cp "${PROJECT_DIR}/.env.example" "${PROJECT_DIR}/.env"
  warn "Please edit .env with your configuration values before proceeding."
  warn "At minimum, change: SECRET_KEY, database passwords, admin credentials."
else
  ok ".env file already exists."
fi

# ─── Step 3: Install backend dependencies (optional) ─────────────────────────
if command -v python3 &>/dev/null; then
  info "Installing Python dependencies..."
  cd "${PROJECT_DIR}/backend"
  if [ -f "requirements.txt" ]; then
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    ok "Python dependencies installed."
  elif [ -f "pyproject.toml" ]; then
    if command -v poetry &>/dev/null; then
      poetry install --no-root
      ok "Python (poetry) dependencies installed."
    else
      warn "poetry not found. Install with: pip install poetry"
    fi
  else
    warn "No requirements.txt or pyproject.toml found. Skipping Python deps."
  fi
  cd "${PROJECT_DIR}"
else
  warn "Python3 not found. Skipping backend dependency installation."
fi

# ─── Step 4: Install frontend dependencies (optional) ────────────────────────
if command -v node &>/dev/null; then
  if [ -f "${PROJECT_DIR}/frontend/package.json" ]; then
    info "Installing Node.js dependencies..."
    cd "${PROJECT_DIR}/frontend"
    npm install
    ok "Node.js dependencies installed."
    cd "${PROJECT_DIR}"
  fi
else
  warn "Node.js not found. Skipping frontend dependency installation."
fi

# ─── Step 5: Build and start Docker containers ───────────────────────────────
if [ "$SKIP_DOCKER" = false ]; then
  if command -v docker &>/dev/null; then
    info "Building and starting Docker containers..."

    COMPOSE_ARGS="--env-file ${PROJECT_DIR}/.env -p darktrace up -d"

    if [ "$DEV_MODE" = true ]; then
      info "Starting in DEVELOPMENT mode (hot reload enabled)..."
      docker compose -f "${PROJECT_DIR}/docker-compose.yml" \
        -f "${PROJECT_DIR}/docker-compose.override.yml" \
        ${COMPOSE_ARGS} --build
    else
      info "Starting in PRODUCTION mode..."
      docker compose -f "${PROJECT_DIR}/docker-compose.yml" \
        ${COMPOSE_ARGS} --build
    fi

    ok "Docker containers started."
    echo ""
    echo "=============================================="
    echo "  DarkTrace is running!"
    echo "=============================================="
    echo ""
    echo "  Frontend:  http://localhost:80"
    echo "  API:       http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "  MongoDB:   localhost:27017"
    echo "  ES:        http://localhost:9200"
    echo "  Neo4j:     http://localhost:7474"
    echo "  Redis:     localhost:6379"
    echo "  RabbitMQ:  http://localhost:15672"
    echo ""
    echo "  To view logs:  docker compose -p darktrace logs -f"
    echo "  To stop:       docker compose -p darktrace down"
    echo ""
  else
    error "Docker not found. Please install Docker Desktop or Docker Engine."
    exit 1
  fi
else
  info "Skipping Docker setup (--no-docker flag detected)."
fi

ok "DarkTrace setup complete!"
