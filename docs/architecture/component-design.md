# DarkTrace — Detailed Component Design

> **Version:** 1.0  
> **Date:** 2026-06-03

---

## Table of Contents

1. [Crawler Service](#1-crawler-service)
2. [Proxy Pool Manager](#2-proxy-pool-manager)
3. [Content Parser & Extractor](#3-content-parser--extractor)
4. [NLP / Analysis Engine](#4-nlp--analysis-engine)
5. [Threat Scoring Engine](#5-threat-scoring-engine)
6. [Alert Engine](#6-alert-engine)
7. [Actor Profiling Engine](#7-actor-profiling-engine)
8. [Export & Report Service](#8-export--report-service)
9. [API Gateway / Backend API](#9-api-gateway--backend-api)
10. [Dashboard Frontend](#10-dashboard-frontend)
11. [User Management Service](#11-user-management-service)
12. [Blockchain Evidence Service (Optional)](#12-blockchain-evidence-service)

---

## 1. Crawler Service

### Purpose
Orchestrates the crawling of .onion and .i2p sites. Manages crawl scheduling, proxy assignment, politeness policies, and emits raw fetched content for downstream processing.

### Internal Architecture

```
┌─────────────────────────────────────────────┐
│             Crawler Service                  │
│                                              │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │   Job Scheduler  │  │  Scrapy Spider   │  │
│  │  (APScheduler)   │  │  Manager         │  │
│  │                  │  │                  │  │
│  │  - Cron triggers │  │  - Spawn spiders │  │
│  │  - One-off jobs  │  │  - Assign proxy  │  │
│  │  - Recurring     │  │  - Monitor       │  │
│  │    scans         │  │    completion    │  │
│  └────────┬─────────┘  └────────┬─────────┘  │
│           │                     │             │
│  ┌────────▼─────────────────────▼──────────┐  │
│  │         Crawl Queue (Redis)             │  │
│  │  URL + metadata + proxy assignment      │  │
│  └─────────────────────────────────────────┘  │
│                                              │
│  ┌─────────────────────────────────────────┐  │
│  │      Middleware Pipeline                │  │
│  │  - User-Agent rotation                  │  │
│  │  - Request delay (politeness)           │  │
│  │  - Cookie management                    │  │
│  │  - Retry with backoff                   │  │
│  │  - Response validation                  │  │
│  └─────────────────────────────────────────┘  │
│                                              │
│  ┌─────────────────────────────────────────┐  │
│  │     Output Pipeline                    │  │
│  │  - Emit raw HTML to RabbitMQ           │  │
│  │    (exchange: crawl.raw, routing:      │  │
│  │     raw.page)                          │  │
│  │  - Store raw to MinIO/S3               │  │
│  │  - Update crawl status in MongoDB       │  │
│  └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Key Configurations

| Parameter | Default | Description |
|---|---|---|
| `CRAWL_DELAY` | 5.0s | Minimum delay between requests (politeness) |
| `CONCURRENT_REQUESTS` | 8 | Per-spider concurrency |
| `PROXY_REFRESH_INTERVAL` | 600s | How often to rotate Tor circuits |
| `MAX_RETRIES` | 3 | Retry count for failed requests |
| `CRAWL_TIMEOUT` | 60s | Per-request timeout |
| `USER_AGENT_POOL_SIZE` | 50 | Number of UA strings to rotate |

### Message Contracts

**Outbound → RabbitMQ (exchange: `crawl.raw`)**

```json
{
  "message_id": "uuid",
  "source": "crawler-service",
  "type": "raw.page",
  "timestamp": "2026-06-03T12:00:00Z",
  "payload": {
    "crawl_id": "uuid",
    "url": "http://xyz.onion/listing/123",
    "source_type": "onion",
    "site_name": "example-market",
    "fetch_timestamp": "2026-06-03T12:00:00Z",
    "http_status": 200,
    "content_type": "text/html",
    "raw_content": "<base64-encoded-HTML>",
    "response_headers": {},
    "proxy_used": "tor_exit_12",
    "content_hash": "sha256-hex"
  }
}
```

---

## 2. Proxy Pool Manager

### Purpose
Maintains a dynamic pool of healthy Tor and I2P proxies. Provides a gRPC API for crawler services to request proxies. Performs health checks and circuit rotation.

### Architecture

```
┌─────────────────────────────────────────────┐
│          Proxy Pool Manager                  │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │          Proxy Registry              │   │
│  │  ┌──────────┐ ┌──────────┐          │   │
│  │  │ Tor Pool │ │ I2P Pool │          │   │
│  │  │ - exit1  │ │ - i2p1   │          │   │
│  │  │ - exit2  │ │ - i2p2   │          │   │
│  │  │ - ...    │ │ - ...    │          │   │
│  │  └──────────┘ └──────────┘          │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Health       │  │ Circuit Rotation    │  │
│  │ Checker      │  │ Engine              │  │
│  │              │  │                     │  │
│  │ - TCP probe  │  │ - Random rotation   │  │
│  │ - Latency    │  │ - Sticky sessions   │  │
│  │   tracking   │  │   per crawl job     │  │
│  │ - Anonymity  │  │ - Graceful drain    │  │
│  │   check      │  │                     │  │
│  └──────────────┘  └─────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │         gRPC API                     │   │
│  │  GetProxy(crawl_id, site) → Proxy   │   │
│  │  ReportFailure(proxy_id) → void     │   │
│  │  ListProxies() → Proxy[]            │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Health Check Logic

```
1. TCP connect to SOCKS5 proxy (10s timeout)
2. Fetch known check endpoint (e.g., http://check.torproject.org)
3. Verify response contains "Congratulations" (Tor check)
4. Measure RTT — mark slow proxies (>5s) as degraded
5. Track consecutive failures → remove from pool after 3 failures
6. Refresh Tor circuits every N seconds per proxy
```

---

## 3. Content Parser & Extractor

### Purpose
Consumes raw HTML/documents from RabbitMQ, extracts structured content based on site-specific or generic parsers, and publishes parsed results.

### Supported Formats

- HTML pages (marketplace listings, forum posts, paste content)
- Plain text pastes
- Images (OCR for embedded text)
- PDF documents
- Cryptocurrency addresses (BTC, ETH, XMR)

### Parser Pipeline

```
Raw HTML from RabbitMQ
        │
        ▼
┌───────────────────┐
│ Document Type     │
│ Classifier        │
│ - HTML vs text    │
│ - Marketplace     │
│ - Forum           │
│ - Paste           │
│ - Unknown         │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Site-Specific     │
│ Parser            │
│ (XPath/CSS rules) │
│ - Extract title   │
│ - Extract body    │
│ - Extract author  │
│ - Extract price   │
│ - Extract date    │
│ - Extract images  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Generic Fallback  │
│ Parser            │
│ (readability.js)  │
│ - Clean HTML      │
│ - Extract text    │
│ - Detect language │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Entity Pre-       │
│ Extraction        │
│ - URLs            │
│ - Emails          │
│ - BTC addresses   │
│ - Phone numbers   │
│ - Crypto addrs    │
└────────┬──────────┘
         │
         ▼
Publish to RabbitMQ (exchange: content.parsed)
Routing key: parsed.{site_type}.{document_type}
```

### Output Contract

```json
{
  "message_id": "uuid",
  "source": "content-parser",
  "type": "parsed.page",
  "timestamp": "2026-06-03T12:00:05Z",
  "payload": {
    "crawl_id": "uuid",
    "url": "http://xyz.onion/listing/123",
    "source_type": "onion",
    "site_name": "example-market",
    "document_type": "marketplace_listing",
    "title": "Exploit Kit v2026",
    "author": "hacker123",
    "author_profile_url": "http://xyz.onion/user/hacker123",
    "published_date": "2026-06-02",
    "content_text": "Full text of the listing...",
    "language": "en",
    "entities": {
      "emails": ["seller@example.com"],
      "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
      "eth_addresses": [],
      "xmr_addresses": [],
      "urls": ["http://xyz.onion/listing/123"],
      "phone_numbers": [],
      "ip_addresses": []
    },
    "metadata": {
      "price": "5000",
      "currency": "USD",
      "category": "exploits",
      "tags": ["zero-day", "remote-code-execution"]
    }
  }
}
```

---

## 4. NLP / Analysis Engine

### Purpose
Performs deep content analysis: language detection, translation, sentiment analysis, threat classification, custom keyword/PII matching, and named entity recognition.

### Sub-Components

#### 4.1 Language Detector
- **Model**: FastText language classification
- **Languages**: English, Hindi, Russian, Arabic, Chinese, Spanish, French, German
- **Confidence threshold**: 0.85

#### 4.2 Translator
- **Engine**: OPUS-MT (HuggingFace) for offline translation
- **Fallback**: Google Translate API (when internet available)
- **Cache**: Redis with 30-day TTL for repeated phrases

#### 4.3 NER Pipeline
- **Models**: 
  - spaCy `en_core_web_trf` for English
  - Custom fine-tuned NER for Hindi/Code-Mixed Hinglish
  - Regex patterns for cryptocurrency addresses, PII
- **Entities**: PERSON, ORG, GPE, PRODUCT, MONEY, DATE, PHONE, EMAIL, BTC, ETH, XMR

#### 4.4 Sentiment & Intent Analysis
- **Model**: Fine-tuned RoBERTa on cybercrime forums
- **Dimensions**: Threat intent, urgency, hostility, cooperation
- **Output**: Score per dimension (0.0–1.0)

#### 4.5 Threat Classification
- **Categories**: 
  - `malware` (ransomware, trojan, stealer)
  - `exploit` (zero-day, PoC, weaponization)
  - `data_breach` (leaked DBs, credential dumps)
  - `fraud` (carding, phishing kits, fake docs)
  - `illegal_goods` (drugs, weapons, counterfeit)
  - `services` (DDoS-for-hire, bulletproof hosting)
  - `intelligence` (threat actor chatter, planning)
- **Model**: Hierarchical multi-label classifier (PyTorch)

#### 4.6 Custom Keyword/PII Matcher
- User-defined watchlists (keywords, regex patterns)
- Built-in PII patterns (Aadhaar, PAN, passport, credit card)
- Matching with proximity windows and context validation

### Pipeline Flow

```
Parsed content from RabbitMQ
        │
        ▼
┌───────────────────┐
│ Language Detector │
└────────┬──────────┘
         │
         ▼ (if not English)
┌───────────────────┐
│ Translator        │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ NER Pipeline      │
│ (spaCy + custom)  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Keyword/PII       │
│ Matcher           │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Sentiment &       │
│ Intent Analysis   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Threat            │
│ Classification    │
└────────┬──────────┘
         │
         ▼
Publish to RabbitMQ (exchange: analysis.complete)
Routing key: analysis.{category}
```

---

## 5. Threat Scoring Engine

### Purpose
Assigns a severity score (0–1000) to each analyzed piece of content. Combines multiple signals: content classification, actor reputation, entity prevalence, and contextual factors.

### Scoring Factors

| Factor | Weight | Source |
|---|---|---|
| Threat classification | 30% | NLP Engine |
| Mention of high-value targets | 20% | Entity matching |
| Actor reputation score | 15% | Actor Profiling Engine |
| Freshness (recency) | 10% | Timestamp |
| Sentiment (hostility) | 10% | NLP Engine |
| Keyword match count | 10% | Watchlist matching |
| Source site reputation | 5% | Site ranking |

### Scoring Algorithm

```
BaseScore = Σ(factor_i × weight_i)
Severity =
    0–200: Informational
    201–400: Low
    401–600: Medium
    601–800: High
    801–1000: Critical
```

### Output

```json
{
  "message_id": "uuid",
  "type": "scored.alert",
  "payload": {
    "content_id": "uuid",
    "score": 780,
    "severity": "high",
    "factors": {
      "threat_classification": { "score": 240, "weight": 0.3 },
      "high_value_targets": { "score": 150, "weight": 0.2 },
      "actor_reputation": { "score": 120, "weight": 0.15 },
      "freshness": { "score": 80, "weight": 0.1 },
      "sentiment": { "score": 70, "weight": 0.1 },
      "keyword_matches": { "score": 80, "weight": 0.1 },
      "site_reputation": { "score": 40, "weight": 0.05 }
    },
    "breakdown": "High-value target mention + ransomware classification"
  }
}
```

---

## 6. Alert Engine

### Purpose
Matches scored content against user-configured watchlists and alert rules. Dispatches notifications through multiple channels.

### Alert Rules

```yaml
# Example rule
name: "Ransomware Alert"
description: "Alert when ransomware listing mentions critical infrastructure"
enabled: true
severity_threshold: 600  # Only trigger for High+ severity
conditions:
  - field: "threat_classification"
    operator: "in"
    value: ["ransomware", "data_breach"]
  - field: "entities.keywords_matched"
    operator: "contains_any"
    value: ["hospital", "power grid", "government", "critical infrastructure"]
  - field: "source_type"
    operator: "in"
    value: ["onion", "i2p"]
notifications:
  - type: "email"
    target: "team@police.gov.in"
  - type: "webhook"
    target: "https://siem.citypolice.gov.in/webhook"
  - type: "dashboard_alert"
  - type: "sms"  # optional
    target: "+919876543210"
```

### Deduplication
- Hash-based dedup: `sha256(content_id + rule_id)`
- Window: 24 hours (same alert not triggered within window)
- Stored in Redis with TTL

---

## 7. Actor Profiling Engine

### Purpose
Tracks threat actors across multiple platforms. Builds profiles from pseudonyms, writing style, cryptocurrency addresses, and PGP keys.

### Profile Building Process

```
Parse content →
    Extract author pseudonym → Check Neo4j for existing profile
        │
        ├── New → Create profile node
        │           ├── Add pseudonym
        │           ├── Add writing sample (stylometry)
        │           └── Add first seen timestamp
        │
        └── Existing → Update profile
                        ├── Link new pseudonym (if different)
                        ├── Update writing sample corpus
                        ├── Add new transaction/activity
                        ├── Update last seen timestamp
                        └── Create relationships to:
                             - Other actors (co-posts, transactions)
                             - Marketplaces used
                             - Products sold/bought
```

### Stylometry Analysis

- **Features**: Word frequency, sentence length, POS tag distribution, function word usage, misspelling patterns
- **Model**: Random Forest classifier trained on known actor writing samples
- **Confidence score**: 0.0–1.0 for pseudonym linkage

### Graph Schema (Neo4j)

```
(Actor)-[:USES]->(Pseudonym)
(Actor)-[:POSTED_ON]->(Site)
(Actor)-[:TRANSACTED_WITH]->(Actor)
(Actor)-[:MENTIONED_IN]->(Content)
(Pseudonym)-[:MAPS_TO]->(BTCAddress)
(Pseudonym)-[:MAPS_TO]->(PGPKey)
(Content)-[:CONTAINS]->(Entity)
```

---

## 8. Export & Report Service

### Purpose
Generates downloadable reports and handles SIEM integration.

### Report Types

| Report Type | Format | Description |
|---|---|---|
| Alert Report | PDF | Detailed alert with timeline, evidence, scores |
| Actor Dossier | PDF/JSON | Complete profile of a threat actor |
| Trend Report | PDF/CSV | Aggregated statistics over time period |
| Raw Data Export | JSON/CSV | Bulk export for external analysis |
| SIEM Forward | CEF/LEEF | Real-time alert forwarding |

### Generation Pipeline

```
Request (via API)
        │
        ▼
┌───────────────────┐
│ Template Engine   │
│ (Jinja2 / WeasyPrint)
│ - PDF via HTML→PDF │
│ - CSV via streams  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Evidence Packager │
│ - Collect related │
│   content         │
│ - Add digital     │
│   signature       │
│ - Optional block- │
│   chain hash      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Storage & Return  │
│ - Store in S3     │
│ - Return signed   │
│   URL (1hr TTL)   │
└───────────────────┘
```

---

## 9. API Gateway / Backend API

### Technology: FastAPI (Python)

### Responsibilities

1. **Authentication & Authorization**
   - JWT-based auth (access + refresh tokens)
   - OAuth2 + OpenID Connect support
   - Role-based access (admin, investigator, auditor)
   - API key authentication for SIEM integrations

2. **Rate Limiting**
   - Per-user: 100 req/min
   - Per-IP: 1000 req/min
   - Per-API-key: 1000 req/min

3. **Request Validation**
   - Pydantic schemas for request/response validation
   - Input sanitization (XSS prevention)

4. **API Documentation**
   - OpenAPI 3.1 (auto-generated)
   - ReDoc and Swagger UI

5. **CORS & Security Headers**
   - Strict CSP headers
   - HSTS, X-Frame-Options, X-Content-Type-Options

### Middleware Stack

```
Request → Rate Limiter → Auth → Request Logger → CORS → Router → Response
                                │
                           Audit Log
```

---

## 10. Dashboard Frontend

### Technology: React 18 + TypeScript + Vite

### Key Views

| View | Description |
|---|---|
| **Dashboard** | Summary cards: active alerts, crawled sites, actors tracked, trends |
| **Alerts** | Filterable, sortable alert list with severity indicators |
| **Alert Detail** | Full alert with content, analysis, actor info, timeline |
| **Search** | Full-text search across all indexed content with faceted filters |
| **Actor Profiles** | Graph visualization of actor network, timeline of activity |
| **Crawler Manager** | Configure crawl targets, view crawl status, schedule scans |
| **Watchlists** | Manage keyword/PII watchlists and alert rules |
| **Reports** | Generate and download reports |
| **Admin Panel** | User management, system configuration, audit logs |

### State Management
- **Primary**: React Query (TanStack Query) for server state
- **UI State**: Zustand (lightweight)
- **Graph Visualization**: Cytoscape.js or D3.js for Neo4j graphs

### Real-Time Updates
- WebSocket connection to API Gateway for live alert streaming
- Server-Sent Events (SSE) for crawl progress updates

---

## 11. User Management Service

### Authentication Flow

```
User → Login → POST /auth/login
    → Validate credentials (bcrypt)
    → Generate JWT (access: 15min, refresh: 7d)
    → Store refresh token hash in MongoDB
    → Return {access_token, refresh_token, user_info}

Token Refresh → POST /auth/refresh
    → Validate refresh token
    → Issue new access token

Logout → POST /auth/logout
    → Blacklist refresh token in Redis
```

### Role Model

| Role | Permissions |
|---|---|
| `investigator` | View alerts, search content, create watchlists, generate reports |
| `admin` | All investigator + manage users, configure system, view audit logs |
| `auditor` | View audit logs, view reports (read-only, no alerts) |
| `siem_integration` | API key access to alert stream only |

---

## 12. Blockchain Evidence Service (Optional)

### Purpose
Provides tamper-proof evidence hashing using a public blockchain (e.g., Ethereum or Polygon).

### Flow

```
1. Investigator generates report
2. Report hash computed: SHA-256(report_content + timestamp + investigator_id)
3. Hash submitted to smart contract on blockchain
4. Transaction receipt stored in MongoDB (tx_hash, block_number, timestamp)
5. Verification: recompute hash and compare against blockchain record
```

### Smart Contract

```solidity
contract EvidenceRegistry {
    bytes32[] public evidenceHashes;
    mapping(bytes32 => uint256) public timestamps;
    
    function seal(bytes32 hash) external returns (uint256) {
        evidenceHashes.push(hash);
        timestamps[hash] = block.timestamp;
        return block.timestamp;
    }
    
    function verify(bytes32 hash) external view returns (bool, uint256) {
        return (timestamps[hash] > 0, timestamps[hash]);
    }
}
```

---

*Document maintained by the Architecture Team.*
