# DarkTrace — Run Instructions for Kali Linux

> **Project:** Dark Web Surveillance & Threat Intelligence Tool  
> **Hackathon:** KANADSHIELD26 (Cyber Crime Branch, Ahmedabad City Police)  
> **Last Updated:** 2026-06-03

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure Overview](#2-project-structure-overview)
3. [Quick Start (Docker — Recommended)](#3-quick-start-docker--recommended)
4. [Manual Setup (Without Docker)](#4-manual-setup-without-docker)
5. [Configuring Tor Proxy for Dark Web Crawling](#5-configuring-tor-proxy-for-dark-web-crawling)
6. [Verifying the Installation](#6-verifying-the-installation)
7. [Accessing the Dashboard](#7-accessing-the-dashboard)
8. [Running Tests](#8-running-tests)
9. [Troubleshooting](#9-troubleshooting)
10. [Security Notes](#10-security-notes)

---

## 1. Prerequisites

### Required on Kali Linux

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# 1. Docker & Docker Compose
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# ⚠️ Log out and back in for group changes to take effect

# 2. Verify Docker
docker --version            # Should show 24+
docker compose version      # Should show v2+

# 3. Python 3.11+ (for manual setup only)
python3 --version           # Kali 2024+ has Python 3.11+
sudo apt install -y python3.11-venv python3.11-dev

# 4. Node.js 20+ (for frontend manual setup only)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install -y nodejs
node --version              # Should show v20+

# 5. Git
sudo apt install -y git

# 6. Tor (for dark web proxy)
sudo apt install -y tor
sudo systemctl enable --now tor
```

### Hardware Requirements

| Setup | RAM | Disk | CPU |
|-------|-----|------|-----|
| **Minimal (Docker)** | 8 GB | 20 GB free | 4 cores |
| **Recommended** | 16 GB | 50 GB free | 8 cores |

---

## 2. Project Structure Overview

```
darktrace/
├── backend/                 # FastAPI Python backend
│   ├── app/                 # Application source (10 modules)
│   │   ├── main.py          # Entry point
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB connections
│   │   ├── auth/            # JWT authentication
│   │   ├── crawler/         # Dark web crawling engine
│   │   ├── nlp/             # NLP pipeline (entity extraction, sentiment, translation)
│   │   ├── alerts/          # Alert engine
│   │   ├── watchlists/      # Keyword/pattern watchlists
│   │   ├── actors/          # Threat actor profiling
│   │   ├── reports/         # Report generation (PDF/CSV/JSON)
│   │   ├── export/          # SIEM export & blockchain
│   │   ├── dashboard/       # Dashboard API
│   │   ├── search/          # Full-text search
│   │   ├── admin/           # User management & audit
│   │   └── threat_scoring/  # Scoring engine
│   ├── tests/               # 275 pytest tests
│   └── Dockerfile
│
├── frontend/                # React + TypeScript dashboard
│   ├── src/
│   │   ├── pages/           # 12 page components
│   │   ├── components/      # 42 reusable components
│   │   ├── hooks/           # 8 data-fetching hooks
│   │   ├── api/             # API client functions
│   │   └── store/           # Zustand state management
│   ├── Dockerfile
│   └── nginx.conf
│
├── docs/                    # Full documentation (11 files)
│   ├── architecture/        # 6 architecture design docs
│   ├── api-reference.md     # Complete REST API reference
│   ├── user-guide.md        # Investigator/analyst user guide
│   ├── deployment-guide.md  # Production deployment guide
│   ├── ai-model-details.md  # NLP/AI model documentation
│   └── security/            # Security audit report
│
├── monitoring/              # Prometheus + Grafana config
├── scripts/                 # Utility scripts (setup, reset, logs)
├── .github/workflows/       # CI/CD pipelines
├── docker-compose.yml       # 9-service deployment
└── .env.example             # Environment config template
```

---

## 3. Quick Start (Docker — Recommended)

This is the fastest way to get DarkTrace running on Kali Linux. All services run in isolated containers.

### Step 1: Extract and Enter the Project

```bash
# If you received a zip file:
unzip darktrace.zip -d ~/darktrace
cd ~/darktrace

# Or if you cloned from git:
# git clone <repo-url> darktrace
# cd darktrace
```

### Step 2: Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with strong passwords (IMPORTANT for production)
# At minimum, change these:
#   SECRET_KEY           — Use: openssl rand -hex 64
#   DEFAULT_ADMIN_PASSWORD
#   MONGODB_* passwords
#   ELASTICSEARCH_PASSWORD
#   NEO4J_PASSWORD
#   REDIS_PASSWORD
nano .env
```

### Step 3: Start All Services

```bash
# Start all 9 services in the background
docker compose up -d

# Monitor startup progress
docker compose logs -f
# Press Ctrl+C when you see all services are healthy
```

### Step 4: Verify All Services Are Healthy

```bash
docker compose ps
```

Expected output (all services should show `healthy`):

```
NAME                          SERVICE             STATUS              PORTS
darktrace-backend             backend             healthy             8000
darktrace-frontend            frontend            healthy             8080
darktrace-mongodb             mongodb             healthy             27017
darktrace-elasticsearch       elasticsearch       healthy             9200
darktrace-neo4j               neo4j               healthy             7474,7687
darktrace-redis               redis               healthy             6379
darktrace-rabbitmq            rabbitmq            healthy             5672,15672
darktrace-crawler-worker      crawler-worker      healthy
darktrace-nlp-worker          nlp-worker          healthy
```

### Step 5: Access DarkTrace

- **Dashboard:** http://localhost:8080
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Grafana:** http://localhost:3001 (admin/admin)

### Step 6: Login with Default Credentials

> **⚠️ CHANGE THESE IMMEDIATELY for any non-local deployment**

- Email: `admin@darktrace.local`
- Password: `changeme_admin_password` (or whatever you set in `.env`)

### Useful Docker Commands

```bash
# Stop all services
docker compose down

# Stop and delete all data volumes
docker compose down -v

# Restart a specific service
docker compose restart backend

# View logs for a specific service
docker compose logs -f backend

# Rebuild and restart
docker compose up -d --build

# Run a single service
docker compose up -d mongodb redis
```

---

## 4. Manual Setup (Without Docker)

Use this if you want to run the backend and frontend natively on Kali (for development or if Docker is not available).

### Step 1: Start Required Databases

You need MongoDB, Elasticsearch, Neo4j, and Redis running locally or remotely.

```bash
# Install databases on Kali
sudo apt install -y mongodb elasticsearch neo4j redis-server

# Start services
sudo systemctl start mongodb elasticsearch neo4j redis-server
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
python3 -m spacy download en_core_web_sm

# Copy and configure environment
cp ../.env.example .env
# Edit .env to point to your local databases
# Change: MONGODB_URI=mongodb://localhost:27017/darktrace
#         ELASTICSEARCH_HOSTS=http://localhost:9200
#         NEO4J_URI=bolt://localhost:7687
#         REDIS_URI=redis://localhost:6379/0
#         RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Run the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Frontend Setup (in a separate terminal)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev -- --host 0.0.0.0 --port 3000
```

### Step 4: Access

- **Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:8000

---

## 5. Configuring Tor Proxy for Dark Web Crawling

DarkTrace crawls `.onion` sites through Tor. You need a running Tor service.

### Option A: Using Kali's Built-in Tor (Recommended for Testing)

```bash
# Install and start Tor
sudo apt install -y tor
sudo systemctl start tor

# Default SOCKS5 proxy: 127.0.0.1:9050
# Verify it's working:
curl --socks5-hostname 127.0.0.1:9050 http://check.torproject.org/api/ip
```

### Option B: Using Docker Tor Container (Recommended for Production)

The docker-compose.yml includes a Tor proxy configuration. In `.env` set:

```env
TOR_PROXY_HOST=tor-proxy
TOR_PROXY_PORT=9050
```

Then uncomment/add the `tor-proxy` service in your docker-compose.yml:

```yaml
tor-proxy:
  image: dperson/torproxy:latest
  networks:
    - backend
  restart: unless-stopped
```

### Testing Tor Connectivity

```bash
# From the backend container
docker exec darktrace-backend curl --socks5-hostname tor-proxy:9050 \
  http://check.torproject.org/api/ip
```

---

## 6. Verifying the Installation

### Health Check Endpoints

```bash
# General health
curl http://localhost:8000/health

# Detailed health (requires auth)
curl -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@darktrace.local","password":"changeme_admin_password"}' | \
  python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')" \
  http://localhost:8000/v1/admin/health
```

### Expected Health Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "mongodb": {"status": "connected"},
    "elasticsearch": {"status": "connected"},
    "neo4j": {"status": "connected"},
    "redis": {"status": "connected"}
  }
}
```

---

## 7. Accessing the Dashboard

### Default Login

1. Open **http://localhost:8080** (Docker) or **http://localhost:3000** (manual)
2. Login with:
   - Email: `admin@darktrace.local`
   - Password: `changeme_admin_password` (or as set in `.env`)

### Dashboard Pages

| Page | URL | Description |
|------|-----|-------------|
| **Dashboard** | `/dashboard` | Summary cards, charts, trending threats |
| **Alerts** | `/alerts` | Filterable alert list, bulk actions |
| **Alert Detail** | `/alerts/:id` | Full alert details, evidence, notes |
| **Crawler** | `/crawler` | Target management, crawl jobs |
| **Watchlists** | `/watchlists` | Keyword/pattern watchlist management |
| **Actors** | `/actors` | Threat actor profiles, network graphs |
| **Actor Detail** | `/actors/:id` | Full actor dossier |
| **Search** | `/search` | Full-text search with facets |
| **Reports** | `/reports` | Generate/download PDF/CSV/JSON |
| **Admin** | `/admin` | User management, audit logs, health |

### API Documentation

Once the backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 8. Running Tests

### Backend Tests (275 tests)

```bash
cd backend

# Activate virtual environment (if manual setup)
source venv/bin/activate

# Set testing mode
export TESTING=true

# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=term

# Run specific test file
python -m pytest tests/test_nlp.py -v

# Run tests matching a keyword
python -m pytest tests/ -k "alert" -v
```

### Frontend Type Check & Build

```bash
cd frontend

# TypeScript type check
npx tsc --noEmit

# Production build
npm run build
```

---

## 9. Troubleshooting

### Common Issues on Kali Linux

#### Docker Permission Denied

```bash
# Add your user to docker group
sudo usermod -aG docker $USER
# Log out and back in, then:
docker ps
```

#### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000
# Or
ss -tulpn | grep 8000

# Stop the conflicting service or change the port in .env
```

#### Elasticsearch Won't Start (Memory)

```bash
# Elasticsearch requires vm.max_map_count
sudo sysctl -w vm.max_map_count=262144

# Make permanent
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

#### Backend Can't Connect to Databases

```bash
# Check if database containers are running
docker compose ps

# Check database logs
docker compose logs mongodb
docker compose logs elasticsearch

# If using manual setup, verify services:
sudo systemctl status mongodb
sudo systemctl status elasticsearch
```

#### Tor Proxy Connection Refused

```bash
# Check Tor is running
sudo systemctl status tor

# Test the SOCKS proxy
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip

# In Docker, ensure the tor-proxy container is on the same network
```

#### Docker Compose v2 Not Found

```bash
# On older Kali versions, install docker-compose-plugin
sudo apt install -y docker-compose-plugin
# Or use the legacy command:
docker-compose up -d
# Instead of: docker compose up -d
```

#### Internet/Network Issues

```bash
# Check DNS resolution
nslookup google.com

# Check Tor connectivity (for onion sites)
curl --socks5-hostname 127.0.0.1:9050 http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion
```

### Service Logs Reference

```bash
# Backend logs
docker compose logs backend

# Database health
docker exec darktrace-mongodb mongosh --eval "db.runCommand({ping:1})"
docker exec darktrace-elasticsearch curl -s localhost:9200
docker exec darktrace-redis redis-cli ping

# Queue status
docker exec darktrace-rabbitmq rabbitmqctl list_queues

# Resource usage
docker stats
```

---

## 10. Security Notes

> **⚠️ CRITICAL: DarkTrace is a law enforcement tool. Follow these security practices.**

### Before Using in Production

1. **Change ALL default passwords** in `.env`:
   ```bash
   # Generate strong passwords
   openssl rand -base64 32   # For database passwords
   openssl rand -hex 64       # For SECRET_KEY
   ```

2. **Enable HTTPS** with a reverse proxy (nginx + Let's Encrypt)

3. **Restrict network access**:
   - Bind services to `127.0.0.1` or use a firewall
   - Never expose MongoDB/Elasticsearch/Neo4j directly to the internet

4. **Review the security audit** report at `docs/security/security-audit-report.md`

### Kali-Specific Security

- Run DarkTrace in an isolated network namespace or VM when handling real threats
- Use `iptables` or `ufw` to restrict access to DarkTrace services:
  ```bash
  sudo ufw allow 8080/tcp    # Dashboard
  sudo ufw allow 8000/tcp    # API (restrict to trusted IPs)
  sudo ufw deny 27017         # MongoDB - no external access
  sudo ufw deny 9200          # Elasticsearch - no external access
  ```
- Never store real credentials in plaintext files accessible to other users
- Use `chmod 600 .env` to restrict the env file

### Legal & Ethical Use

- Only use DarkTrace on networks and systems you are authorized to monitor
- Comply with all applicable laws and regulations regarding digital surveillance
- This tool is designed for lawful investigations by authorized law enforcement personnel
- Document all investigative actions in the provided audit log system

---

## Quick Reference Card

```bash
# ─── First Time ──────────────────────────────
cp .env.example .env
# Edit .env with strong passwords
docker compose up -d
# Access: http://localhost:8080

# ─── Daily ───────────────────────────────────
docker compose ps                      # Check health
docker compose logs -f backend         # Monitor backend

# ─── Rebuild ─────────────────────────────────
docker compose up -d --build

# ─── Stop ────────────────────────────────────
docker compose down

# ─── Reset (deletes all data) ────────────────
docker compose down -v

# ─── Run Tests ───────────────────────────────
cd backend && export TESTING=true && python -m pytest tests/ -v
```

> For full documentation, see the `docs/` directory:
> - `docs/user-guide.md` — End-user guide for investigators
> - `docs/api-reference.md` — Complete REST API reference
> - `docs/deployment-guide.md` — Production deployment details
> - `docs/ai-model-details.md` — NLP/AI pipeline documentation
> - `docs/architecture/` — Architecture design documents (6 files)
> - `docs/security/security-audit-report.md` — Security audit findings
