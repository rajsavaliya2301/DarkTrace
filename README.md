# 🛡️ DarkTrace — Dark Web Surveillance & Threat Intelligence Tool

> **KANADSHIELD26_P1_02** — Organized by Cyber Crime Branch, Ahmedabad City Police

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-00a393?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🔍 Overview

**DarkTrace** is a comprehensive dark web monitoring platform that automatically crawls, monitors, and analyzes dark web content (.onion sites, I2P, forums, marketplaces, paste sites) to extract potential threats, identify illegal activity, and generate actionable intelligence for law enforcement, cybercrime investigators, and national security agencies.

### Key Features

| Feature | Description |
|---------|-------------|
| 🌐 **Dark Web Crawling** | Automated crawling of .onion domains via Tor/I2P SOCKS5 proxies with proxy rotation |
| 🔍 **Keyword & Pattern Monitoring** | Custom watchlists with keyword, regex, and entity-based threat detection |
| 🧠 **NLP Analysis** | Sentiment analysis, entity extraction, multi-language translation (Hindi, English, Russian, Arabic) |
| 📊 **Threat Intelligence Dashboard** | Real-time visualization of threats, trends, timelines, and network graphs |
| ⚡ **Alerting & Escalation** | Severity-based real-time alerts with multi-channel notifications (email, webhook, SIEM) |
| 🕵️ **Actor Profiling** | Cross-platform pseudonym tracking, stylometry analysis, relationship graph mapping |
| 📋 **Reporting & Export** | PDF/CSV/JSON report generation with SIEM integration (CEF/LEEF formats) |
| 🔗 **Blockchain Evidence** | Optional evidence sealing on blockchain for forensic integrity |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                            │
│  React Dashboard  •  SIEM Integration  •  REST API Clients   │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                   API GATEWAY (FastAPI)                       │
│        JWT Auth  •  Rate Limiting  •  Request Validation     │
└──────┬───────────┬───────────┬───────────┬───────────────────┘
       │           │           │           │
┌──────▼──┐ ┌─────▼─────┐ ┌───▼────┐ ┌───▼──────────┐
│ Crawler │ │   NLP     │ │ Alert  │ │ Export/Report │
│ Service │ │  Engine   │ │ Engine │ │   Service     │
└────┬────┘ └─────┬─────┘ └───┬────┘ └───┬──────────┘
     │            │           │           │
┌────▼────┐ ┌─────▼─────┐ ┌───▼────┐     │
│ Proxy   │ │  Threat   │ │ Actor  │     │
│ Pool    │ │  Scoring  │ │Profile │     │
└─────────┘ └───────────┘ └────────┘     │
     │            │           │           │
     └────────────┼───────────┼───────────┘
                  │           │
          ┌───────▼───────────▼───────┐
          │      RABBITMQ (Events)     │
          └───────┬───────────┬───────┘
                  │           │
     ┌────────────┼───────────┼────────────┐
     │            │           │            │
┌────▼────┐ ┌─────▼────┐ ┌───▼────┐ ┌────▼────┐
│ MongoDB │ │Elastic   │ │ Neo4j  │ │  Redis  │
│ (Docs)  │ │ (Search) │ │(Graph) │ │ (Cache) │
└─────────┘ └──────────┘ └────────┘ └─────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.11+, FastAPI 0.111+ | REST API with async support, auto OpenAPI docs |
| **Crawling** | Scrapy, aiohttp | Web crawling with Tor/I2P proxy support |
| **NLP** | spaCy, NLTK, TextBlob, argos-translate | Entity extraction, sentiment, translation |
| **Frontend** | React 18, TypeScript, Vite | Dashboard UI |
| **UI** | TailwindCSS, Recharts, Cytoscape.js | Styling, charts, network graphs |
| **State** | Zustand, TanStack Query | State management, data fetching |
| **Databases** | MongoDB, Elasticsearch, Neo4j, Redis | Document store, search, graph, caching |
| **Messaging** | RabbitMQ | Async event-driven communication |
| **Auth** | JWT, bcrypt | Authentication & authorization |
| **DevOps** | Docker, Docker Compose, GitHub Actions | Containerization & CI/CD |
| **Monitoring** | Prometheus, Grafana | Metrics & observability |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- Git
- 8GB+ RAM (16GB recommended for production)

### Setup (5 minutes)

```bash
# 1. Clone the repository
git clone <repo-url> darktrace
cd darktrace

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings (passwords, secrets, etc.)

# 3. Start all services
docker compose up -d

# 4. Verify deployment
docker compose ps
# All 9 services should show "healthy" status

# 5. Access the dashboard
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Development Setup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev -- --port 3000
```

---

## 📁 Project Structure

```
darktrace/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py          # App entry point
│   │   ├── config.py        # Settings (12-factor)
│   │   ├── database.py      # DB connections
│   │   ├── auth/            # JWT auth, user management
│   │   ├── crawler/         # Crawl engine, proxy pool, parsers
│   │   ├── nlp/             # NLP pipeline, entities, sentiment
│   │   ├── alerts/          # Alert engine & management
│   │   ├── watchlists/      # Watchlist CRUD
│   │   ├── actors/          # Actor profiling & graph
│   │   ├── reports/         # Report generation
│   │   ├── export/          # SIEM & blockchain integration
│   │   ├── dashboard/       # Dashboard summary API
│   │   ├── search/          # Full-text search
│   │   ├── admin/           # Admin & audit
│   │   └── threat_scoring/  # Threat scoring engine
│   ├── tests/               # Test suite (275 tests)
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                # React dashboard
│   ├── src/
│   │   ├── api/             # API client & endpoint functions
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # React Query hooks
│   │   ├── store/           # Zustand state
│   │   ├── types/           # TypeScript interfaces
│   │   └── utils/           # Utility functions
│   ├── Dockerfile
│   └── nginx.conf
│
├── docs/                    # Documentation
│   ├── architecture/        # Architecture design docs (6 files)
│   ├── security/            # Security audit report
│   ├── api-reference.md     # REST API reference
│   ├── user-guide.md        # User guide for analysts
│   ├── deployment-guide.md  # Production deployment guide
│   └── ai-model-details.md  # NLP/AI model documentation
│
├── monitoring/              # Prometheus & Grafana config
├── scripts/                 # Utility scripts
├── .github/workflows/       # CI/CD pipelines
├── docker-compose.yml       # Main deployment
└── docker-compose.override.yml  # Development overrides
```

---

## 🧪 Testing

```bash
# Backend tests (275 tests)
cd backend
pip install -r requirements.txt pytest pytest-asyncio httpx
$env:TESTING="true"
python -m pytest tests/ -v

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend build
npm run build
```

---

## 🔐 Security

A comprehensive security audit has been conducted. See [`docs/security/security-audit-report.md`](docs/security/security-audit-report.md) for full details.

**Key findings addressed:**
- ✅ SSRF protection in crawler (URL validation)
- ✅ JWT with short TTL + refresh rotation
- ✅ Password hashing with bcrypt (12 rounds)
- ✅ Rate limiting on all endpoints
- ✅ CORS restricted to allowed origins
- ✅ Audit logging with tamper-evident chain
- ✅ Input validation via Pydantic models
- ✅ Non-root containers in Docker
- ✅ Network segmentation (frontend/backend/data)

---

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| **Login** | Secure authentication portal |
| **Dashboard** | Summary cards, severity chart, alert trends, trending threats, activity timeline |
| **Alerts** | Filterable table with severity badges, bulk actions, detail view |
| **Crawler** | Target management (add/edit/delete), job monitoring |
| **Watchlists** | Keyword & pattern watchlists with tag input |
| **Actors** | Threat actor profiles with relationship network graphs |
| **Search** | Full-text search across crawled content, alerts, actors |
| **Reports** | Generate & download PDF/CSV/JSON reports |
| **Admin** | User management, audit logs, system health |

---

## 🤝 Integration

### SIEM Integration
- Syslog (RFC 5424) with CEF/LEEF format
- Webhook with HMAC authentication
- Compatible with Splunk, ELK, QRadar, ArcSight

### API Integration
- REST API with JWT authentication
- API key support for programmatic access
- OpenAPI 3.0 documentation at `/docs`

---

## 📄 License

This project is developed for the KANADSHIELD26 hackathon organized by the Cyber Crime Branch, Ahmedabad City Police.

---

## 👥 Team

Built with ❤️ by the DarkTrace team for KANADSHIELD26.
