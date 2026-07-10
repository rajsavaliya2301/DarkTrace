# DarkTrace — Complete Project Documentation

> **KANADSHIELD26_P1_02** | Organized by Cyber Crime Branch, Ahmedabad City Police
> **Repository:** [github.com/rajsavaliya2301/DarkTrace](https://github.com/rajsavaliya2301/DarkTrace)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Features](#2-key-features)
3. [Tech Stack](#3-tech-stack)
4. [Architecture](#4-architecture)
5. [Project Structure](#5-project-structure)
6. [Backend — Complete Details](#6-backend--complete-details)
7. [Frontend — Complete Details](#7-frontend--complete-details)
8. [Database Design](#8-database-design)
9. [Docker & Deployment](#9-docker--deployment)
10. [CI/CD Pipeline](#10-cicd-pipeline)
11. [Security](#11-security)
12. [Monitoring & Alerting](#12-monitoring--alerting)
13. [API Reference](#13-api-reference)
14. [Dashboard Pages](#14-dashboard-pages)
15. [Testing](#15-testing)
16. [Configuration](#16-configuration)
17. [Quick Start Guide](#17-quick-start-guide)
18. [File Statistics](#18-file-statistics)
19. [Environment Variables](#19-environment-variables)
20. [Credits](#20-credits)

---

## 1. Project Overview

**DarkTrace** is a comprehensive dark web monitoring platform that automatically crawls, monitors, and analyzes dark web content (.onion sites, I2P, forums, marketplaces, paste sites) to extract potential threats, identify illegal activity, and generate actionable intelligence for law enforcement, cybercrime investigators, and national security agencies.

### Problem Statement

Dark web spaces host illegal marketplaces, forums, and communication channels used by threat actors. Manual monitoring is impossible at scale. DarkTrace automates the entire intelligence pipeline — from crawling to analysis to actionable alerts.

### Solution

A full-stack platform with 10 microservices orchestrated via Docker Compose, featuring automated Tor/I2P crawling, NLP-powered threat analysis, real-time alerting, actor profiling with graph relationships, and a React dashboard for investigators.

---

## 2. Key Features

| Feature | Description |
|---------|-------------|
| Dark Web Crawling | Automated crawling of .onion domains via Tor/I2P SOCKS5 proxies with proxy rotation |
| Keyword & Pattern Monitoring | Custom watchlists with keyword, regex, and entity-based threat detection |
| NLP Analysis | Sentiment analysis, entity extraction, multi-language translation (Hindi, English, Russian, Arabic) |
| Threat Intelligence Dashboard | Real-time visualization of threats, trends, timelines, and network graphs |
| Alerting & Escalation | Severity-based real-time alerts with multi-channel notifications (email, webhook, SIEM) |
| Actor Profiling | Cross-platform pseudonym tracking, stylometry analysis, relationship graph mapping |
| Reporting & Export | PDF/CSV/JSON report generation with SIEM integration (CEF/LEEF formats) |
| Blockchain Evidence | Optional evidence sealing on blockchain for forensic integrity |
| External Threat Intel | VirusTotal, Shodan, AlienVault OTX integration |
| Full-text Search | Elasticsearch-powered search across crawled content, alerts, and actors |
| WebSocket Real-time | Live updates for alerts and crawler status |
| Audit Logging | Tamper-evident hash-chained audit trail for all actions |

---

## 3. Tech Stack

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ (running 3.12) | Core language |
| FastAPI | 0.111+ | REST API framework with async support |
| Uvicorn | 0.29+ | ASGI server |
| Pydantic | 2.7+ | Data validation and settings |
| Motor | 3.4+ | Async MongoDB driver |
| Elasticsearch | 8.14+ (async) | Full-text search engine |
| Neo4j | 5.21+ | Graph database for actor networks |
| Redis | 5.0+ | Caching, rate limiting, session store, token blacklist |
| RabbitMQ | via pika | Async event-driven messaging |
| spaCy | 3.7+ | NLP entity extraction and analysis |
| spaCy Transformers | 1.3+ | Transformer-based NER |
| HuggingFace Transformers | 4.35+ | Zero-shot classification, sentiment analysis |
| TextBlob | 0.18+ | Sentiment analysis |
| NLTK | 3.8+ | Natural language processing toolkit |
| aiohttp | 3.9+ | Async HTTP client for crawling |
| aiohttp-socks | 0.8+ | SOCKS5 proxy support (Tor/I2P) |
| BeautifulSoup4 | 4.12+ | HTML parsing |
| ReportLab | 4.1+ | PDF report generation |
| Web3.py | 7.0+ | Blockchain evidence sealing |
| PyJWT | 2.8+ | JWT token management |
| bcrypt | 4.1+ | Password hashing (12 rounds) |
| scikit-learn | 1.3+ | Fallback ML classification |
| httpx | 0.27+ | HTTP client |
| tenacity | 8.3+ | Retry logic |

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.3 | UI framework |
| TypeScript | 5.5 | Type-safe JavaScript |
| Vite | 5.4 | Build tool and dev server |
| React Router | 6.26 | Client-side routing |
| TanStack React Query | 5.56 | Server state management and data fetching |
| Zustand | 4.5 | Client state management |
| Axios | 1.7 | HTTP client |
| Recharts | 2.12 | Charts and visualizations |
| Cytoscape.js | 3.30 | Network/graph visualizations |
| React Hook Form | 7.53 | Form management |
| Zod | 3.23 | Schema validation |
| TailwindCSS | 3.4 | Utility-first CSS |
| Lucide React | 0.441 | Icon library |
| react-hot-toast | 2.4 | Toast notifications |
| date-fns | 3.6 | Date formatting |

### Infrastructure

| Technology | Version | Purpose |
|-----------|---------|---------|
| Docker | 29.5+ | Containerization |
| Docker Compose | 5.1+ | Multi-service orchestration |
| MongoDB | 7.0 | Document store |
| Elasticsearch | 8.14 | Search and analytics |
| Neo4j | 5.21 | Graph database |
| Redis | 7.2 | Cache and sessions |
| RabbitMQ | 3.13 | Message broker |
| Tor Proxy | dperson/torproxy | Dark web access |
| Nginx | 1.27 | Frontend reverse proxy |
| Prometheus | latest | Metrics collection |
| Grafana | latest | Metrics visualization |

---

## 4. Architecture

### System Architecture

```
+------------------------------------------------------------------+
|                       CLIENT LAYER                                 |
|  React Dashboard  |  SIEM Integration  |  REST API Clients        |
+----------------------------------+-------------------------------+
                                   |
+----------------------------------v-------------------------------+
|                   API GATEWAY (FastAPI)                           |
|        JWT Auth  |  Rate Limiting  |  Request Validation          |
+-------+----------+----------+----------+-------------------------+
        |          |          |          |
+-------v--+ +----v----+ +---v---+ +---v-----------+
| Crawler  | |  NLP    | | Alert | | Export/Report |
| Service  | | Engine  | | Engine| |   Service     |
+----+-----+ +----+----+ +---+---+ +---+-----------+
     |           |          |          |
+----v----+ +----v----+ +---v---+     |
| Proxy   | | Threat  | | Actor |     |
| Pool    | | Scoring | |Profile|     |
+---------+ +---------+ +-------+     |
     |           |          |          |
     +-----------+----------+----------+
                 |          |
         +-------v----------v-------+
         |      RABBITMQ (Events)   |
         +-------+----------+-------+
                 |          |
     +-----------+----------+------------+
     |          |          |            |
+----v---+ +----v----+ +---v---+ +----v----+
|MongoDB | |Elastic- | | Neo4j | |  Redis  |
| (Docs) | |search   | |(Graph)| | (Cache) |
+--------+ | (Search)| +-------+ +---------+
           +---------+
```

### Network Architecture

| Network | Subnet | Purpose | Isolation |
|---------|--------|---------|-----------|
| `frontend` | 172.20.0.0/24 | Public-facing services (frontend, backend API) | Bridge |
| `backend` | 172.20.1.0/24 | Internal service communication | Internal |
| `data` | 172.20.2.0/24 | Database and storage tier | Internal |

### Data Flow

1. **Crawling:** Crawler Worker connects through Tor Proxy -> fetches .onion pages -> parses HTML -> stores raw content in MongoDB
2. **Indexing:** Raw content is indexed into Elasticsearch for full-text search
3. **NLP Processing:** NLP Worker picks up content from RabbitMQ queue -> runs entity extraction, sentiment analysis, threat classification -> stores results back in MongoDB
4. **Threat Scoring:** Threat scoring engine computes composite scores based on classification, freshness, keyword matches, and actor reputation
5. **Alerting:** Alert engine evaluates content against watchlist rules -> generates alerts with severity levels -> stores in MongoDB
6. **Graph Building:** Actor profiler extracts pseudonyms and relationships -> stores in Neo4j for network analysis
7. **Dashboard:** React frontend queries FastAPI backend -> displays real-time data via REST + WebSocket

---

## 5. Project Structure

```
darktrace/
|-- backend/                          # FastAPI backend (10,357 lines)
|   |-- app/
|   |   |-- main.py                   # App entry point (263 lines)
|   |   |-- config.py                 # Settings - 60 config keys (142 lines)
|   |   |-- database.py               # DB connection managers (222 lines)
|   |   |-- dependencies.py           # DI: auth, DB, rate limiting (343 lines)
|   |   |-- pipeline.py               # Processing pipeline
|   |   |-- seed.py                   # Database seeding
|   |   |-- ws.py                     # WebSocket support
|   |   |-- auth/                     # JWT auth, user management
|   |   |   |-- router.py             # Login, refresh, logout, register
|   |   |   |-- jwt.py                # Token creation/verification
|   |   |   |-- models.py             # User models, password hashing
|   |   |-- crawler/                  # Crawl engine, proxy pool, parsers
|   |   |   |-- router.py             # Target CRUD, job management
|   |   |   |-- engine.py             # Async crawl engine with Tor/I2P
|   |   |   |-- scheduler.py          # Crawl job scheduler
|   |   |   |-- parsers.py            # HTML/content parsers
|   |   |   |-- proxy_pool.py         # Tor/I2P proxy rotation
|   |   |-- nlp/                      # NLP pipeline (10 files)
|   |   |   |-- router.py             # NLP analysis endpoints
|   |   |   |-- analyzer.py           # Main NLP orchestrator
|   |   |   |-- classifier.py         # Rule-based threat classification
|   |   |   |-- ml_classifier.py      # ML zero-shot classification
|   |   |   |-- entities.py           # Named entity extraction (spaCy)
|   |   |   |-- sentiment.py          # Sentiment analysis
|   |   |   |-- ml_sentiment.py       # ML-based sentiment
|   |   |   |-- keyword_matcher.py    # Watchlist keyword matching
|   |   |   |-- translator.py         # Multi-language translation
|   |   |-- alerts/                   # Alert engine & management
|   |   |   |-- router.py             # Alert CRUD, bulk actions
|   |   |   |-- engine.py             # Alert evaluation engine
|   |   |   |-- models.py             # Alert data models
|   |   |-- watchlists/               # Watchlist CRUD
|   |   |-- actors/                   # Actor profiling & graph
|   |   |   |-- router.py             # Actor endpoints
|   |   |   |-- profiler.py           # Pseudonym extraction, stylometry
|   |   |   |-- graph.py              # Neo4j relationship queries
|   |   |-- reports/                  # Report generation
|   |   |-- export/                   # SIEM & blockchain integration
|   |   |   |-- siem.py               # Syslog CEF/LEEF format
|   |   |   |-- blockchain.py         # Blockchain evidence sealing
|   |   |-- dashboard/                # Dashboard summary API
|   |   |-- search/                   # Full-text search + saved searches
|   |   |-- admin/                    # Admin & audit log viewer
|   |   |-- threat_scoring/           # Threat scoring engine
|   |   |   |-- engine.py             # Composite score calculator
|   |   |   |-- rules.py              # Scoring rules
|   |   |-- intel/                    # External threat intelligence
|   |       |-- virustotal.py         # VirusTotal API integration
|   |       |-- shodan.py             # Shodan API integration
|   |       |-- otx.py                # AlienVault OTX integration
|   |-- tests/                        # Test suite (13 test files)
|   |-- scripts/                      # Startup & utility scripts
|   |-- Dockerfile                    # Multi-stage build, non-root user
|   |-- requirements.txt              # 26+ Python packages
|   |-- pytest.ini                    # Test configuration
|
|-- frontend/                         # React dashboard (8,802 lines)
|   |-- src/
|   |   |-- App.tsx                   # Router setup (13 routes)
|   |   |-- main.tsx                  # Entry point
|   |   |-- index.css                 # Tailwind imports
|   |   |-- api/                      # API client layer (9 files)
|   |   |-- components/               # Reusable UI components (46 files)
|   |   |   |-- common/               # Shared components (10)
|   |   |   |-- layout/               # Layout components (4)
|   |   |   |-- dashboard/            # Dashboard widgets (6)
|   |   |   |-- alerts/               # Alert components (5)
|   |   |   |-- actors/               # Actor components (3)
|   |   |   |-- crawler/              # Crawler components (4)
|   |   |   |-- search/               # Search components (4)
|   |   |   |-- watchlists/           # Watchlist components (3)
|   |   |   |-- reports/              # Report components (3)
|   |   |   |-- admin/                # Admin components (4)
|   |   |-- pages/                    # Page components (13)
|   |   |-- hooks/                    # React Query hooks (9)
|   |   |-- store/                    # Zustand state (2)
|   |   |-- types/                    # TypeScript interfaces (9)
|   |   |-- utils/                    # Utility functions (3)
|   |-- Dockerfile                    # Multi-stage: Node 20 + nginx:alpine
|   |-- nginx.conf                    # Reverse proxy with security headers
|   |-- package.json                  # 17 deps + 10 devDeps
|
|-- docs/                             # Documentation
|   |-- api-reference.md              # REST API docs (913 lines)
|   |-- user-guide.md                 # Analyst user guide (472 lines)
|   |-- deployment-guide.md           # Production deployment (285 lines)
|   |-- ai-model-details.md           # NLP/AI documentation (296 lines)
|   |-- security/
|   |   |-- security-audit-report.md  # OWASP audit (1,406 lines)
|   |-- architecture/                 # Architecture docs (6 files)
|
|-- monitoring/                       # Observability
|   |-- prometheus.yml                # Scraping config (11 targets)
|   |-- alerts.yml                    # 14 alert rules across 5 groups
|   |-- grafana-datasources.yml       # 4 auto-provisioned datasources
|   |-- grafana-dashboards/
|       |-- darktrace-overview.json   # 9-panel production dashboard
|
|-- scripts/                          # Utility scripts (40+ files)
|-- .github/workflows/
|   |-- ci.yml                        # CI: lint, test, build, security
|   |-- deploy.yml                    # CD: build, staging, smoke, production
|
|-- docker-compose.yml                # 10 services, 3 networks, 7 volumes
|-- docker-compose.override.yml       # Development overrides
|-- .env.example                      # Environment template
|-- .gitignore                        # Git exclusions
|-- README.md                         # Project readme
```

---

## 6. Backend — Complete Details

### Application Entry (`main.py` — 263 lines)

- **Framework:** FastAPI with lifespan-based resource management
- **16 Routers Registered:** auth, crawler, alerts, alerts_rules, watchlists, actors, reports, dashboard, search, saved_search, admin, export, nlp, threat_scoring, intel, ws
- **Middleware:**
  - `CORSMiddleware` — configurable allowed origins
  - Custom `request_logging_middleware` — logs method, path, status, duration
- **Exception Handlers:** Global `Exception` (500), `ValueError` (422)
- **Health Endpoint:** `GET /health` returns `{"status": "healthy"}`
- **Root Endpoint:** `GET /` returns API info with links to docs
- **Startup:** Seeds default admin user, initializes DB connections, starts crawler scheduler

### Configuration (`config.py` — 142 lines)

**60 environment variables across 16 categories:**

| Category | Keys | Count |
|----------|------|-------|
| FastAPI | APP_NAME, APP_VERSION, DEBUG, TESTING, API_PREFIX, CORS_ORIGINS, CORS_ALLOW_CREDENTIALS | 7 |
| Security | SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, BCRYPT_ROUNDS | 5 |
| MongoDB | MONGODB_URI, MONGODB_DATABASE, MONGODB_MAX_POOL_SIZE, MONGODB_MIN_POOL_SIZE | 4 |
| Elasticsearch | ELASTICSEARCH_HOSTS, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD, ELASTICSEARCH_VERIFY_CERTS | 4 |
| Neo4j | NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_MAX_CONNECTION_POOL_SIZE | 4 |
| Redis | REDIS_URI, REDIS_PASSWORD, REDIS_SOCKET_TIMEOUT, REDIS_SOCKET_CONNECT_TIMEOUT | 4 |
| Rate Limiting | RATE_LIMIT_PER_USER, RATE_LIMIT_PER_IP, RATE_LIMIT_WINDOW_SECONDS, LOGIN_RATE_LIMIT_PER_IP, LOGIN_RATE_WINDOW_SECONDS | 5 |
| Crawler | CRAWL_DELAY, CONCURRENT_REQUESTS, PROXY_REFRESH_INTERVAL, MAX_RETRIES, CRAWL_TIMEOUT, TOR_PROXY_HOST, TOR_PROXY_PORT, I2P_PROXY_HOST, I2P_PROXY_PORT | 9 |
| RabbitMQ | RABBITMQ_URL | 1 |
| NLP | SPACY_MODEL_EN, TRANSLATION_CACHE_TTL | 2 |
| Threat Scoring | THREAT_SCORE_WEIGHTS | 1 |
| Logging | LOG_LEVEL, LOG_FORMAT | 2 |
| Report | REPORT_EXPIRY_HOURS, REPORT_STORAGE_PATH | 2 |
| SIEM | SIEM_SYSLOG_HOST, SIEM_SYSLOG_PORT | 2 |
| Default Admin | DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD | 2 |
| ML Models | HUGGINGFACE_MODEL, SENTIMENT_MODEL, MODEL_CACHE_DIR, MODEL_AUTO_DOWNLOAD | 4 |
| External APIs | VIRUSTOTAL_API_KEY, SHODAN_API_KEY, OTX_API_KEY | 3 |

### Dependency Injection (`dependencies.py` — 343 lines)

12 dependency functions providing:
- Database connections (MongoDB, Elasticsearch, Neo4j, Redis)
- JWT/API key authentication
- Role-based access control (RBAC) with 4 roles: admin, investigator, auditor, siem_integration
- Tamper-evident audit logging with hash chaining
- Sliding-window rate limiting via Redis sorted sets

### Authentication System

- **JWT tokens** with configurable TTL (default: 15 min access, 7 day refresh)
- **Refresh token rotation** — one-time use, stored as SHA-256 hash in MongoDB
- **Token blacklisting** — logout invalidates tokens via Redis
- **Account lockout** — 5 failed attempts triggers 5-minute lock
- **Login rate limiting** — 10 attempts per 5 minutes per IP
- **API key support** — for programmatic/SIEM integration
- **Password hashing** — bcrypt with 12 rounds

### Crawler Engine

- **Async crawling** via aiohttp with SOCKS5 proxy support
- **Tor proxy** integration for .onion domains
- **I2P proxy** support for I2P network
- **Proxy rotation** with configurable refresh interval
- **Configurable delays** between requests (default: 5s)
- **Concurrent request limit** (default: 8)
- **Retry logic** with configurable max retries
- **Content parsers** for HTML, forum posts, marketplace listings

### NLP Pipeline (10 files)

1. **Language Detection** — langdetect library
2. **Entity Extraction** — spaCy transformer model (en_core_web_trf)
3. **Sentiment Analysis** — TextBlob + DistilBERT ML model
4. **Threat Classification** — Rule-based + HuggingFace zero-shot (facebook/bart-large-mnli)
5. **Keyword Matching** — Watchlist regex and keyword matching
6. **Translation** — Google Translate + Argos Translate for offline
7. **ML Classifier** — scikit-learn fallback for classification

### Threat Scoring Engine

Composite score (0-100) based on weighted factors:
```json
{
  "classification": 0.30,
  "high_value_targets": 0.20,
  "actor_reputation": 0.15,
  "freshness": 0.10,
  "sentiment": 0.10,
  "keyword_matches": 0.10,
  "site_reputation": 0.05
}
```

### External Threat Intelligence

| Service | API | Purpose |
|---------|-----|---------|
| VirusTotal | VT API v3 | File/URL reputation lookup |
| Shodan | Shodan API | IoT/device intelligence |
| AlienVault OTX | OTX DirectConnect | Threat pulse indicators |

### Backend Dependencies (26 packages)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.111.0,<1.0.0 | API framework |
| uvicorn[standard] | >=0.29.0,<1.0.0 | ASGI server |
| pydantic | >=2.7.0,<3.0.0 | Data validation |
| pydantic[email] | >=2.7.0,<3.0.0 | Email validation |
| python-multipart | >=0.0.9 | File uploads |
| motor | >=3.4.0,<4.0.0 | Async MongoDB |
| elasticsearch[async] | >=8.14.0,<9.0.0 | Async Elasticsearch |
| neo4j | >=5.21.0,<6.0.0 | Neo4j driver |
| redis[hiredis] | >=5.0.0,<6.0.0 | Async Redis |
| PyJWT | >=2.8.0,<3.0.0 | JWT tokens |
| bcrypt | >=4.1.0,<5.0.0 | Password hashing |
| python-jose[cryptography] | >=3.3.0,<4.0.0 | JWT alternative |
| passlib[bcrypt] | >=1.7.4,<2.0.0 | Password utilities |
| aiohttp | >=3.9.0 | Async HTTP |
| aiohttp-socks | >=0.8.0,<4.0.0 | SOCKS5 proxy |
| beautifulsoup4 | >=4.12.0,<5.0.0 | HTML parsing |
| lxml | >=5.2.0,<6.0.0 | XML/HTML parsing |
| spacy | >=3.7.0,<4.0.0 | NLP |
| spacy-transformers | >=1.3.0 | Transformer NER |
| textblob | >=0.18.0,<1.0.0 | Sentiment |
| nltk | >=3.8.0,<4.0.0 | NLP toolkit |
| langdetect | >=1.0.9,<2.0.0 | Language detection |
| googletrans | >=4.0.0,<5.0.0 | Translation |
| argostranslate | >=1.8.0,<2.0.0 | Offline translation |
| transformers | >=4.35.0 | HuggingFace models |
| sentencepiece | >=0.1.99 | Tokenization |
| scikit-learn | >=1.3.0 | ML fallback |
| reportlab | >=4.1.0,<5.0.0 | PDF generation |
| web3 | >=7.0.0,<8.0.0 | Blockchain |
| python-dateutil | >=2.9.0,<3.0.0 | Date handling |
| python-dotenv | >=1.0.0,<2.0.0 | Env loading |
| orjson | >=3.10.0,<4.0.0 | Fast JSON |
| httpx | >=0.27.0,<1.0.0 | HTTP client |
| tenacity | >=8.3.0,<9.0.0 | Retry logic |
| python-json-logger | >=2.0.0,<3.0.0 | JSON logging |
| pytest | >=8.2.0,<9.0.0 | Testing |
| pytest-asyncio | >=0.23.0,<1.0.0 | Async testing |

---

## 7. Frontend — Complete Details

### Routing (13 routes)

| Route | Component | Auth Required | Description |
|-------|-----------|:-------------:|-------------|
| `/login` | LoginPage | No | Secure authentication portal |
| `/dashboard` | DashboardPage | Yes | Summary cards, charts, trends |
| `/alerts` | AlertsPage | Yes | Filterable alert table |
| `/alerts/:id` | AlertDetailPage | Yes | Single alert detail view |
| `/crawler` | CrawlerPage | Yes | Target management, job monitoring |
| `/watchlists` | WatchlistsPage | Yes | Keyword/pattern watchlists |
| `/actors` | ActorsPage | Yes | Threat actor profiles |
| `/actors/:id` | ActorDetailPage | Yes | Actor detail with network graph |
| `/search` | SearchPage | Yes | Full-text search |
| `/profile` | ProfilePage | Yes | User profile |
| `/reports` | ReportsPage | Yes | Generate & download reports |
| `/admin` | AdminPage | Yes | User management, audit logs |
| `/` | Redirect | — | Redirects to `/dashboard` |
| `*` | NotFoundPage | No | 404 page |

### Component Architecture (46 components)

| Group | Components | Count |
|-------|-----------|:-----:|
| Common | Clock, ConfirmDialog, ConnectionStatus, DataTable, EmptyState, ErrorState, LoadingSpinner, PageHeader, SearchBar, StatusBadge | 10 |
| Layout | Header, MainLayout, ProtectedRoute, Sidebar | 4 |
| Dashboard | ActivityTimeline, AlertTrendChart, SeverityChart, SourceRanking, SummaryCards, TrendingPanel | 6 |
| Alerts | AlertBulkActions, AlertCard, AlertDetail, AlertFilters, AlertList | 5 |
| Actors | ActorDetail, ActorList, ActorNetworkGraph | 3 |
| Crawler | JobList, JobStatus, TargetForm, TargetList | 4 |
| Search | SaveSearchModal, SearchFilters, SearchHistory, SearchResults | 4 |
| Watchlists | KeywordTagInput, WatchlistForm, WatchlistList | 3 |
| Reports | ReportDownload, ReportGenerator, ReportList | 3 |
| Admin | AuditLogViewer, SystemHealth, UserForm, UserList | 4 |

### API Client Layer (9 files)

| File | Endpoints |
|------|-----------|
| `client.ts` | Axios instance with interceptors, base URL, auth headers |
| `auth.ts` | login, logout, refreshToken, getProfile |
| `alerts.ts` | getAlerts, getAlert, updateAlert, bulkAction, getAlertRules |
| `actors.ts` | getActors, getActor, getActorNetwork |
| `crawler.ts` | getTargets, addTarget, updateTarget, deleteTarget, getJobs |
| `dashboard.ts` | getDashboardSummary |
| `reports.ts` | generateReport, getReports, downloadReport |
| `search.ts` | search, getSavedSearches, saveSearch, deleteSearch |
| `watchlists.ts` | getWatchlists, createWatchlist, updateWatchlist, deleteWatchlist |

### React Hooks (9 hooks)

| Hook | Purpose |
|------|---------|
| `useAuth` | Login/logout, token management, user profile |
| `useAlerts` | Alert CRUD, filtering, bulk actions |
| `useActors` | Actor list, detail, network graph data |
| `useCrawler` | Target management, job monitoring |
| `useDashboard` | Dashboard summary data fetching |
| `useReports` | Report generation, download, history |
| `useSearch` | Full-text search, saved searches |
| `useWatchlists` | Watchlist CRUD operations |
| `useRealtimeUpdates` | WebSocket connection for live updates |

### State Management

- **Zustand stores:** `authStore` (tokens, user), `preferencesStore` (UI preferences)
- **React Query:** Server state caching, background refetching, optimistic updates

### Frontend Dependencies (17 runtime + 10 dev)

| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.3.1 | UI framework |
| react-dom | ^18.3.1 | DOM rendering |
| react-router-dom | ^6.26.2 | Client routing |
| @tanstack/react-query | ^5.56.0 | Server state |
| zustand | ^4.5.5 | Client state |
| axios | ^1.7.7 | HTTP client |
| recharts | ^2.12.7 | Charts |
| cytoscape | ^3.30.1 | Graph visualization |
| react-cytoscapejs | ^2.0.0 | React Cytoscape wrapper |
| react-hook-form | ^7.53.0 | Form handling |
| @hookform/resolvers | ^3.9.0 | Form validation |
| zod | ^3.23.8 | Schema validation |
| clsx | ^2.1.1 | Class name utility |
| tailwind-merge | ^2.5.2 | Tailwind class merging |
| lucide-react | ^0.441.0 | Icons |
| react-hot-toast | ^2.4.1 | Notifications |
| date-fns | ^3.6.0 | Date formatting |

**Dev Dependencies:** TypeScript 5.5, Vite 5.4, TailwindCSS 3.4, PostCSS, Autoprefixer, @vitejs/plugin-react, @types/react, @types/react-dom, @types/node, @types/cytoscape

---

## 8. Database Design

### MongoDB Collections

| Collection | Purpose | Key Fields |
|-----------|---------|------------|
| `users` | User accounts | email, password_hash, role, api_keys, refresh_tokens, is_locked |
| `alerts` | Generated threats | title, severity, source, content_hash, threat_score, status, created_at |
| `alert_rules` | Watchlist rules | name, type (keyword/regex/entity), pattern, severity, is_active |
| `watchlists` | Keyword lists | name, keywords[], tags[], created_by |
| `crawl_targets` | Sites to monitor | url, type (onion/i2p/forum), schedule, is_active, last_crawled |
| `crawl_jobs` | Crawl execution history | target_id, status, started_at, completed_at, pages_crawled |
| `raw_content` | Crawled page data | url, title, body, crawled_at, content_hash, language |
| `actors` | Threat profiles | pseudonyms[], aliases, platforms[], first_seen, last_active |
| `reports` | Generated reports | type (pdf/csv/json), filters, file_path, expires_at |
| `audit_logs` | Tamper-evident trail | user_id, action, resource_type, tamper_hash, previous_hash |

### Elasticsearch Indices

| Index | Purpose |
|-------|---------|
| `darktrace_content` | Full-text search across crawled content |
| `darktrace_alerts` | Searchable alert data |

### Neo4j Graph Schema

| Node Labels | Relationships |
|-------------|---------------|
| `Actor` | `ALIAS_OF` — pseudonym relationships |
| `Pseudonym` | `ACTIVE_ON` — platform presence |
| `Platform` | `MENTIONED_IN` — content references |
| `Content` | `TRIGGERS` — alert connections |
| `Alert` | |

### Redis Usage

| Key Pattern | Purpose | TTL |
|------------|---------|-----|
| `rate:user:{id}` | Per-user rate limiting | 60s |
| `rate:ip:{ip}` | Per-IP rate limiting | 60s |
| `rate:login:{ip}` | Login brute-force protection | 300s |
| `blacklist:token:{jwt}` | Logged-out token blacklist | Token remaining TTL |
| `session:{id}` | Session cache | Configurable |

---

## 9. Docker & Deployment

### Docker Compose Services (10)

| Service | Image | Port | Health Check | Memory Limit |
|---------|-------|------|-------------|-------------|
| tor-proxy | dperson/torproxy:latest | 9050 | Tor API check | 256MB |
| mongodb | mongo:7.0 | 27017 (127.0.0.1:27018) | mongosh ping | 2GB |
| elasticsearch | elasticsearch:8.14.3 | 9200 (127.0.0.1) | Cluster health | 4GB |
| neo4j | neo4j:5.21.0 | 7474, 7687 (127.0.0.1) | cypher-shell RETURN 1 | 2GB |
| redis | redis:7.2-alpine | 6379 (127.0.0.1) | redis-cli ping | 512MB |
| rabbitmq | rabbitmq:3.13-management-alpine | 5672, 15672 (127.0.0.1) | diagnostics check_running | 512MB |
| backend | darktrace/backend:latest | 8000 (127.0.0.1) | HTTP /health | 4GB |
| frontend | darktrace/frontend:latest | 80 (127.0.0.1) | wget spider | 256MB |
| crawler-worker | darktrace/crawler-worker:latest | — | HTTP /health | 1GB |
| nlp-worker | darktrace/nlp-worker:latest | — | HTTP /health | 2GB |

### Docker Volumes (7)

| Volume | Purpose |
|--------|---------|
| darktrace_mongodb_data | MongoDB persistence |
| darktrace_elasticsearch_data | Elasticsearch indices |
| darktrace_neo4j_data | Neo4j graph data |
| darktrace_neo4j_logs | Neo4j logs |
| darktrace_redis_data | Redis AOF/RDB |
| darktrace_rabbitmq_data | RabbitMQ messages |
| darktrace_model_cache | HuggingFace/spaCy model cache |

### Backend Dockerfile (Multi-stage)

```
Stage 1 (builder): python:3.12-slim
  - Install gcc, libffi-dev
  - pip install torch (CPU-only) + requirements.txt into /install
  - Download spaCy models (en_core_web_trf, en_core_web_lg)

Stage 2 (runtime): python:3.12-slim
  - Create non-root user: darktrace:darktrace
  - Copy /install from builder
  - Copy application code
  - USER darktrace
  - EXPOSE 8000
  - HEALTHCHECK on /health
```

### Frontend Dockerfile (Multi-stage)

```
Stage 1 (builder): node:20-alpine
  - npm ci (install dependencies)
  - npm run build (tsc + vite build)

Stage 2 (runtime): nginx:1.27-alpine
  - Copy built dist/ to nginx html
  - Copy nginx.conf
  - USER nginx
  - EXPOSE 80
  - HEALTHCHECK on /
```

### Nginx Configuration

- **Security headers:** X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS, Permissions-Policy, CSP
- **API proxy:** `/api/` -> `backend:8000/` with proper headers
- **WebSocket proxy:** `/ws/` -> `backend:8000` with Upgrade/Connection headers
- **Static caching:** Hashed assets cached 1 year, HTML never cached
- **Compression:** gzip on for CSS, JS, JSON, SVG, XML

### Development Override

- Backend: hot-reload via `uvicorn --reload`
- Volume mounts for live code updates
- Exposed database ports for local tooling
- Frontend: Vite dev server (separate terminal)

---

## 10. CI/CD Pipeline

### CI Pipeline (`.github/workflows/ci.yml`)

Triggers: Push to `main`/`develop`, PRs to both

| Job | Depends On | Steps | Timeout |
|-----|-----------|-------|---------|
| **lint** | — | Python 3.11 + flake8 + black check + Node.js 20 + ESLint + TypeScript typecheck | 15 min |
| **test** | lint | MongoDB + Redis services + pytest with coverage + frontend tests (ChromeHeadless) | 20 min |
| **build** | test | Docker Buildx + matrix build (backend, frontend, crawler-worker, nlp-worker) + smoke check | 30 min |
| **security** | lint | pip-audit + npm audit + Trivy vulnerability scanner + SARIF upload to GitHub Security | 15 min |

### Deploy Pipeline (`.github/workflows/deploy.yml`)

Triggers: Push to `main` only

| Stage | Description |
|-------|-------------|
| **build-and-push** | Build 4 images, push to GHCR with SBOM + attestation |
| **deploy-staging** | SSH deploy via Docker Compose, health check |
| **smoke-tests** | API health, frontend, auth, MongoDB, Elasticsearch |
| **deploy-production** | Manual approval, rolling update, MongoDB backup, Slack notification |

---

## 11. Security

### Security Audit Results

**Overall Risk:** CRITICAL (addressed)
**Findings:** 27 total (3 Critical, 7 High, 10 Medium, 7 Low)
**Methodology:** OWASP Top 10 (2021), STRIDE Threat Modeling, Manual Code Review

### Security Measures Implemented

| Measure | Status | Details |
|---------|:------:|---------|
| SSRF Protection | Fixed | URL validation in crawler engine |
| JWT with short TTL | Implemented | 15 min access, 7 day refresh with rotation |
| Password Hashing | Implemented | bcrypt with 12 rounds |
| Rate Limiting | Implemented | Per-user, per-IP, and login-specific |
| CORS Restriction | Implemented | Configurable allowed origins |
| Audit Logging | Implemented | Tamper-evident hash chaining |
| Input Validation | Implemented | Pydantic models on all endpoints |
| Non-root Containers | Implemented | Backend + frontend Dockerfiles |
| Network Segmentation | Implemented | 3 isolated Docker networks |
| Login Brute-force Protection | Implemented | Account lockout after 5 failures |
| HSTS Headers | Implemented | nginx Strict-Transport-Security |
| CSP Headers | Implemented | Content-Security-Policy in nginx |
| .gitignore | Implemented | Protects .env, secrets from Git |
| Secret Rotation | Implemented | All secrets rotated, no real keys in repo |

### RBAC Roles

| Role | Permissions |
|------|------------|
| `admin` | Full access: alerts, search, crawler, watchlists, reports, actors, admin, dashboard, export |
| `investigator` | alerts, search, crawler, watchlists, reports, actors, dashboard, export |
| `auditor` | search, reports, actors, admin (read-only), dashboard |
| `siem_integration` | alerts (read-only) |

---

## 12. Monitoring & Alerting

### Prometheus Configuration

**Scrape interval:** 15s (10s for backend/workers)
**Targets:** 11 services

| Target | Endpoint |
|--------|----------|
| prometheus | localhost:9090 |
| backend | backend:8000/metrics |
| mongodb | mongodb-exporter:9216 |
| elasticsearch | elasticsearch-exporter:9114 |
| neo4j | neo4j:2004 |
| redis | redis-exporter:9121 |
| rabbitmq | rabbitmq:15692 |
| crawler-worker | crawler-worker:8000/metrics |
| nlp-worker | nlp-worker:8000/metrics |
| node-exporter | node-exporter:9100 |
| docker | docker-exporter:9323 |
| nginx | frontend:8080 |

### Alert Rules (14 rules across 5 groups)

| Group | Alert | Severity | Condition |
|-------|-------|----------|-----------|
| **service_health** | ServiceDown | critical | up == 0 for 1m |
| | HighErrorRate | warning | 5xx rate > 5% for 5m |
| **backend_performance** | HighLatency | warning | p95 > 2s for 5m |
| | HighCPUUsage | warning | CPU > 80% for 10m |
| | HighMemoryUsage | warning | RAM > 3.5GB for 5m |
| **datastores** | MongoDBDown | critical | down for 1m |
| | ElasticsearchDown | critical | down for 1m |
| | RedisDown | critical | down for 1m |
| | Neo4jDown | critical | down for 1m |
| | ElasticsearchHighMemory | warning | heap > 85% for 10m |
| **workers** | CrawlerWorkerDown | warning | down for 2m |
| | NLPWorkerDown | warning | down for 2m |
| **security** | HighLoginFailureRate | warning | > 0.5 failures/s for 5m |

### Grafana Dashboard (9 panels)

| Panel | Type | Metric |
|-------|------|--------|
| Backend Status | Stat | `up{job="backend"}` |
| Crawler Workers | Stat | `up{job="crawler-worker"}` |
| NLP Workers | Stat | `up{job="nlp-worker"}` |
| Datastores Available | Stat | `up{job=~"mongodb\|elasticsearch\|neo4j\|redis"}` |
| CPU Usage by Service | Time series | `rate(process_cpu_seconds_total[5m])` |
| Memory Usage by Service | Time series | `process_resident_memory_bytes` |
| API Request Rate | Time series | `rate(http_requests_total[5m])` |
| API Response Latency | Time series | `histogram_quantile(0.95/0.99, ...)` |
| API Error Rate | Time series | `rate(http_requests_total{status=~"5..\|4.."}[5m])` |

### Grafana Datasources (4)

| Datasource | Type |
|-----------|------|
| Prometheus | Prometheus |
| Elasticsearch | Elasticsearch 8.14.0 |
| MongoDB | grafana-mongodb-datasource |
| Redis | redis-datasource |

---

## 13. API Reference

**Base URL:** `http://localhost:8000/v1`
**Docs:** `http://localhost:8000/docs` (Swagger UI)
**ReDoc:** `http://localhost:8000/redoc`
**OpenAPI:** `http://localhost:8000/openapi.json`

### Endpoint Groups (16 routers)

| Prefix | Tag | Endpoints |
|--------|-----|-----------|
| `/auth` | Authentication | login, refresh, logout, register, profile |
| `/crawler` | Crawler | targets CRUD, jobs, start/stop |
| `/alerts` | Alerts | list, detail, update, bulk actions |
| `/alert-rules` | Alert Rules | watchlist rule CRUD |
| `/watchlists` | Watchlists | keyword/pattern list CRUD |
| `/actors` | Actors | profiles, detail, network graph |
| `/reports` | Reports | generate, list, download |
| `/dashboard` | Dashboard | summary statistics |
| `/search` | Search | full-text search, saved searches |
| `/admin` | Admin | user management, audit logs |
| `/export` | SIEM Export | syslog CEF/LEEF, webhook |
| `/nlp` | NLP | analyze text, detect language |
| `/threat-scoring` | Threat Scoring | score calculation |
| `/intel` | Threat Intel | VirusTotal, Shodan, OTX lookups |
| `/ws` | WebSocket | real-time updates |
| `/health` | Health | service health check |

### Authentication

```bash
# Login
POST /v1/auth/login
{
  "email": "admin@darktrace.com",
  "password": "your_password"
}

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 900,
  "user": { "id": "...", "email": "...", "role": "admin" }
}

# Use token
Authorization: Bearer <access_token>

# Or API key
X-API-Key: <your-api-key>
```

### Error Responses

| Code | Meaning |
|------|---------|
| 400 | Bad Request — invalid input |
| 401 | Unauthorized — missing/invalid credentials |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found — resource doesn't exist |
| 409 | Conflict — duplicate resource |
| 422 | Unprocessable Entity — validation error |
| 423 | Locked — account locked |
| 429 | Too Many Requests — rate limited |
| 500 | Internal Server Error |

---

## 14. Dashboard Pages

| Page | Description | Key Components |
|------|-------------|---------------|
| **Login** | Secure authentication portal | Email/password form, remember me |
| **Dashboard** | Overview with KPIs | SummaryCards, SeverityChart, AlertTrendChart, TrendingPanel, ActivityTimeline, SourceRanking |
| **Alerts** | Threat alert management | AlertList, AlertFilters, AlertBulkActions, severity badges, status filters |
| **Alert Detail** | Single alert view | Full content, threat score, related actors, timeline |
| **Crawler** | Dark web monitoring | TargetForm, TargetList, JobList, JobStatus, add/edit/delete targets |
| **Watchlists** | Keyword monitoring | WatchlistForm, WatchlistList, KeywordTagInput, regex patterns |
| **Actors** | Threat actor profiles | ActorList, ActorDetail, ActorNetworkGraph (Cytoscape.js) |
| **Actor Detail** | Actor deep dive | Pseudonyms, platforms, activity timeline, network relationships |
| **Search** | Full-text search | SearchBar, SearchFilters, SearchResults, SearchHistory, SaveSearchModal |
| **Reports** | Intelligence reports | ReportGenerator, ReportList, ReportDownload, PDF/CSV/JSON |
| **Admin** | System administration | UserList, UserForm, AuditLogViewer, SystemHealth |
| **Profile** | User profile | Edit profile, change password |
| **404** | Not found | Helpful redirect links |

---

## 15. Testing

### Backend Tests

| Test File | Module Covered |
|-----------|---------------|
| `test_auth.py` | Authentication, JWT, login/logout |
| `test_alerts.py` | Alert CRUD, filtering, bulk actions |
| `test_actors.py` | Actor profiles, graph queries |
| `test_admin.py` | User management, audit logs |
| `test_api.py` | General API endpoints |
| `test_crawler.py` | Crawler engine, target management |
| `test_dashboard.py` | Dashboard summary |
| `test_export.py` | SIEM export, blockchain |
| `test_nlp.py` | NLP pipeline, classification |
| `test_reports.py` | Report generation |
| `test_search.py` | Full-text search |
| `test_threat_scoring.py` | Threat score calculation |
| `test_watchlists.py` | Watchlist CRUD |

**Test Infrastructure:**
- `conftest.py` (972 lines) — Comprehensive mocks for MongoDB, Elasticsearch, Neo4j, Redis
- pytest-asyncio for async test support
- httpx for async HTTP test client
- pytest-cov for coverage reporting

### Frontend Tests

- TypeScript type checking via `tsc --noEmit`
- ESLint for code quality
- Build verification via `npm run build`

---

## 16. Configuration

### Environment Variables

All 60+ configuration keys are managed via environment variables following the 12-factor app methodology.

**Key configuration groups:**
- Application settings (name, version, debug mode)
- Security (JWT secret, algorithm, token TTL, bcrypt rounds)
- Database connections (MongoDB, Elasticsearch, Neo4j, Redis)
- Rate limiting (per-user, per-IP, login-specific)
- Crawler settings (delays, concurrency, proxy config)
- NLP settings (spaCy model, translation cache)
- Threat scoring weights
- External API keys (VirusTotal, Shodan, OTX)
- Logging (level, format)
- Report generation (expiry, storage path)
- SIEM integration (syslog host/port)

---

## 17. Quick Start Guide

### Docker Deployment (Recommended)

```bash
# 1. Clone
git clone https://github.com/rajsavaliya2301/DarkTrace.git
cd DarkTrace

# 2. Configure
cp .env.example .env
# Edit .env with your settings

# 3. Start all services
docker compose up -d

# 4. Verify
docker compose ps
# All 10 services should show "healthy"

# 5. Access
# Frontend:    http://localhost:80
# Backend API: http://localhost:8000
# API Docs:    http://localhost:8000/docs
# Neo4j:       http://localhost:7474
# RabbitMQ:    http://localhost:15672
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

### Default Credentials

```
Email:    admin@darktrace.com
Password: (set in .env — see DEFAULT_ADMIN_PASSWORD)
```

---

## 18. File Statistics

| Metric | Count |
|--------|-------|
| **Total files** | 380 |
| **Backend Python files** | 62 |
| **Backend lines of code** | 10,357 |
| **Frontend TypeScript/TSX files** | 94 |
| **Frontend lines of code** | 8,802 |
| **Test files** | 13 |
| **Documentation files** | 11 |
| **Docker/infra files** | 8 |
| **CI/CD workflow files** | 2 |
| **Script files** | 40+ |
| **Config files** | 15+ |
| **Total lines of code** | ~19,159+ |

---

## 19. Environment Variables

### Required (must set in `.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (64-char hex) | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DEFAULT_ADMIN_PASSWORD` | Initial admin password | Use strong password (20+ chars) |
| `MONGODB_URI` | MongoDB connection string | `mongodb://user:pass@mongodb:27017/db?authSource=admin` |
| `ELASTICSEARCH_PASSWORD` | Elasticsearch password | `your_elastic_password` |
| `NEO4J_PASSWORD` | Neo4j password | `your_neo4j_password` |
| `REDIS_PASSWORD` | Redis password | `your_redis_password` |

### Optional (have defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `info` | Logging level |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | JWT refresh token TTL |
| `RATE_LIMIT_PER_USER` | `100` | Requests per minute per user |
| `RATE_LIMIT_PER_IP` | `1000` | Requests per minute per IP |
| `LOGIN_RATE_LIMIT_PER_IP` | `10` | Login attempts per 5 min per IP |
| `CRAWL_DELAY` | `5.0` | Seconds between crawl requests |
| `CONCURRENT_REQUESTS` | `8` | Max concurrent crawl requests |
| `SPACY_MODEL_EN` | `en_core_web_trf` | spaCy NLP model |

### External API Keys (optional)

| Variable | Service | Free Tier |
|----------|---------|-----------|
| `VIRUSTOTAL_API_KEY` | VirusTotal | 4 req/min, 500 req/day |
| `SHODAN_API_KEY` | Shodan | 1 req/sec, 100 credits/month |
| `OTX_API_KEY` | AlienVault OTX | Generous limits |

---

## 20. Credits

**Built with by the DarkTrace team for KANADSHIELD26.**

Organized by Cyber Crime Branch, Ahmedabad City Police.

### Technologies Used

- Python, FastAPI, React, TypeScript, Docker, MongoDB, Elasticsearch, Neo4j, Redis, RabbitMQ, spaCy, HuggingFace Transformers, Prometheus, Grafana, GitHub Actions

---

*Document generated for KANADSHIELD26 hackathon submission.*
*Last updated: July 10, 2026*
