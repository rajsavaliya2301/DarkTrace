# DarkTrace — Technology Stack

> **Version:** 1.0  
> **Date:** 2026-06-03  
> **Status:** Proposed (pending review)

---

## 1. Technology Stack Overview

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Backend Framework** | FastAPI | 0.111+ | High-performance async Python API framework |
| **Crawling** | Scrapy | 2.11+ | Mature web crawling/scraping framework |
| **NLP / ML** | spaCy | 3.7+ | Industrial-strength NLP pipeline |
| | PyTorch | 2.3+ | Deep learning model training/inference |
| | TensorFlow | 2.16+ | Alternative ML framework |
| | Hugging Face Transformers | 4.40+ | Pre-trained transformer models |
| | NLTK | 3.8+ | Classic NLP utilities (tokenization, stemming) |
| **Database** | MongoDB | 7.0+ | Document store for raw content, users, config |
| | Elasticsearch | 8.14+ | Full-text search and analytics |
| | Neo4j | 5.21+ | Graph database for actor networks |
| **Message Queue** | RabbitMQ | 3.13+ | Async event bus between microservices |
| **Cache** | Redis | 7.2+ | Caching, session store, rate limiting |
| **Frontend** | React | 18.3+ | UI framework |
| | TypeScript | 5.5+ | Type-safe JavaScript |
| | Vite | 5.3+ | Build tool and dev server |
| | TanStack Query | 5.40+ | Server state management |
| | Zustand | 4.5+ | Client state management |
| | D3.js / Cytoscape.js | Latest | Graph visualization |
| | Tailwind CSS | 3.4+ | Utility-first CSS framework |
| **Object Storage** | MinIO | LATEST | S3-compatible object storage |
| **Containerization** | Docker | 26+ | Application containerization |
| | Docker Compose | 2.27+ | Local multi-service orchestration |
| | Kubernetes | 1.30+ | Production container orchestration |
| **Service Mesh** | Istio | 1.22+ | mTLS, traffic management, observability |
| **API Gateway** | FastAPI (self) | — | Built-in gateway with middleware |
| **Auth** | PyJWT / python-jose | Latest | JWT token handling |
| | OAuth2 (FastAPI) | — | OAuth2 password flow |
| **Monitoring** | Prometheus | 2.53+ | Metrics collection |
| | Grafana | 11.1+ | Metrics visualization |
| | OpenTelemetry | Latest | Distributed tracing |
| | ELK Stack | 8.14+ | Log aggregation (Elasticsearch, Logstash, Kibana) |
| | Fluentd | 1.17+ | Log collection and forwarding |
| **Secrets** | HashiCorp Vault | 1.17+ | Secrets management |
| **CI/CD** | GitHub Actions | — | CI/CD pipelines |
| **Blockchain (opt.)** | Web3.py | 7.0+ | Ethereum/Polygon interaction |
| **Proxy** | Tor | 0.4.8+ | Anonymous crawling via SOCKS5 |
| | I2P | 2.5+ | I2P anonymous network |
| | HAProxy | 2.9+ | Proxy load balancing |

---

## 2. Backend Technologies

### 2.1 FastAPI (Python)

**Version:** 0.111+

**Rationale:**
- **Async-native:** Excellent for IO-bound workloads (crawling, API calls, database queries). Uses `asyncio` under the hood.
- **Auto-generated OpenAPI docs:** Eliminates manual API documentation. Swagger UI and ReDoc come built-in.
- **Pydantic integration:** Request/response validation with zero boilerplate. Type hints enforced at runtime.
- **High performance:** On par with Node.js and Go for API throughput (Starlette-based).
- **Dependency injection:** Cleaner than Flask or Django REST for complex service dependencies.
- **Growing ecosystem:** Rich middleware, security utilities (OAuth2, JWT, CORS).
- **Single language stack:** Python across crawling, analysis, and API reduces context switching.

### 2.2 Scrapy (Crawling)

**Version:** 2.11+

**Rationale:**
- **Mature and battle-tested:** Used by many large-scale crawling operations.
- **Middleware architecture:** Easy to plug in proxy rotation, user-agent rotation, retry logic.
- **Built-in scheduling:** Spider middleware, scheduler, and duplicate filter.
- **Concurrent requests:** Async engine with configurable concurrency.
- **Extensible pipelines:** Item pipelines for data cleaning, validation, and storage.
- **Community:** Large ecosystem of extensions and middleware for proxy rotation, selenium integration, etc.

### 2.3 spaCy (NLP)

**Version:** 3.7+

**Rationale:**
- **Production-oriented:** Designed for efficient, pipeline-based NLP in production.
- **Transformer support:** `en_core_web_trf` for state-of-the-art accuracy.
- **Custom pipeline components:** Easy to add custom NER, text classification.
- **Fast:** Significantly faster than NLTK for core NLP tasks.
- **Entity linking:** Can link entities to knowledge bases.
- **Multi-language support:** Models for Hindi, Russian, Arabic (limited but available).

### 2.4 PyTorch & TensorFlow (Deep Learning)

**Versions:** PyTorch 2.3+ / TensorFlow 2.16+

**Rationale:**
- **PyTorch primary:** Preferred for research and custom model development. Dynamic computation graphs ease debugging.
- **TensorFlow secondary:** Used if specific pre-trained models are only available in TF (e.g., some BERT variants).
- **Hugging Face Transformers:** Unified interface for both frameworks.
- **GPU acceleration:** Both support CUDA for training and inference.

---

## 3. Database Technologies

### 3.1 MongoDB

**Version:** 7.0+

**Rationale:**
- **Schema flexibility:** Raw crawled content has varied structure (HTML, JSON, plaintext). MongoDB's document model accommodates this naturally.
- **Rich queries:** Aggregation pipeline for analytics, text indexes for basic search.
- **TTL indexes:** Auto-expire old raw content (90-day retention).
- **Change streams:** Can watch for changes to push real-time updates.
- **Horizontal scaling:** Sharding for large volumes of crawled data.
- **Manageable operations:** Less complex than managing a relational DB for heterogeneous data.

**Use cases:**
- Raw crawled content (full HTML)
- User accounts and roles
- Watchlists and alert rules
- Crawl job metadata
- Audit logs
- Report storage
- Configuration

### 3.2 Elasticsearch

**Version:** 8.14+

**Rationale:**
- **Full-text search:** The industry standard. BM25 scoring, fuzzy matching, highlighting.
- **Analytics aggregations:** Powerful bucketing and metrics aggregations for dashboards and trend analysis.
- **Faceted search:** Essential for filtering large content sets by category, source, language, etc.
- **Speed:** Sub-second query response on billions of documents with proper architecture.
- **ILM (Index Lifecycle Management):** Hot → Warm → Cold → Delete for data retention policies.
- **Kibana integration:** Ad-hoc exploration for analysts during investigations.
- **Elastic Common Schema (ECS):** Normalized field naming for easier cross-referencing.

**Use cases:**
- Primary search index for all crawled and analyzed content
- Alert index with aggregations
- Actor search index
- Audit log storage and search

### 3.3 Neo4j

**Version:** 5.21+

**Rationale:**
- **Native graph storage:** Unlike relational DBs that emulate graphs, Neo4j stores relationships natively.
- **Cypher queries:** Expressive and readable graph query language.
- **Traversal performance:** Constant-time relationship traversal regardless of graph depth.
- **Graph algorithms:** Built-in algorithms for community detection, centrality, pathfinding — useful for actor network analysis.
- **Visualization:** Neo4j Bloom and browser for interactive graph exploration.
- **ACID compliance:** Ensures data integrity for actor profiles.

**Use cases:**
- Actor-pseudonym mappings
- Actor-actor transaction networks
- Actor-site relationships
- Entity (BTC address, PGP key) to actor linking
- Content relationship graphs

---

## 4. Message Queue

### 4.1 RabbitMQ

**Version:** 3.13+

**Rationale:**
- **Mature and reliable:** Battle-tested in production environments for decades.
- **Flexible routing:** Topic exchanges allow fine-grained routing (e.g., `parsed.marketplace.ransomware`).
- **Dead letter queues:** Built-in DLQ for failed message handling.
- **Mirrored queues:** High availability across cluster nodes.
- **Management UI:** Built-in monitoring dashboard.
- **AMQP protocol:** Language-agnostic, well-supported in Python (via `aio-pika` or `pika`).
- **Lower operational complexity than Kafka:** For our expected throughput (thousands of messages/sec), RabbitMQ is sufficient and simpler to operate.

**When to consider Kafka:**
- If crawl volume exceeds 1M pages/day
- If log aggregation needs long-term retention in the broker
- If replay/rewind capability becomes critical

---

## 5. Frontend Technologies

### 5.1 React 18 + TypeScript

**Version:** React 18.3+, TypeScript 5.5+

**Rationale:**
- **Ecosystem:** Largest frontend ecosystem. Rich library support for dashboards, charts, data grids.
- **TypeScript:** Essential for large codebases — catches type errors at compile time.
- **React 18 features:** Concurrent rendering, automatic batching, Suspense for data fetching.
- **Component reusability:** Modular UI for dashboard cards, tables, forms.

### 5.2 Vite

**Version:** 5.3+

**Rationale:**
- **Fast dev server:** Native ESM-based HMR (Hot Module Replacement).
- **Optimized builds:** Tree-shaking, code splitting out of the box.
- **TypeScript support:** First-class, no additional configuration needed.

### 5.3 TanStack Query (React Query)

**Version:** 5.40+

**Rationale:**
- **Server state management:** Handles caching, background refetching, pagination, optimistic updates.
- **Reduces boilerplate:** No need for Redux for API data.
- **DevTools:** Built-in devtools for debugging queries.

### 5.4 Zustand

**Version:** 4.5+

**Rationale:**
- **Lightweight:** ~1KB bundle size.
- **Simple API:** No boilerplate compared to Redux.
- **TypeScript-friendly:** Full type inference.

### 5.5 Visualization Libraries

**D3.js (Latest):**
- Flexible low-level charting library.
- Used for custom visualizations (timelines, activity heatmaps).

**Cytoscape.js (Latest):**
- Purpose-built for graph/network visualization.
- Used for actor network graphs from Neo4j data.
- Supports compound nodes, edge bundling, animations.

---

## 6. Infrastructure & DevOps

### 6.1 Docker & Kubernetes

**Versions:** Docker 26+, Kubernetes 1.30+

**Rationale:**
- **Consistency:** Docker ensures identical environments across dev, staging, and production.
- **Microservices isolation:** Each service runs in its own container with resource limits.
- **Kubernetes orchestration:** Auto-scaling, rolling updates, service discovery, self-healing.
- **Resource efficiency:** Better than VM-based deployment for microservices.

### 6.2 Istio Service Mesh

**Version:** 1.22+

**Rationale:**
- **mTLS:** Automatic encryption between services without application changes.
- **Traffic management:** Canary deployments, circuit breaking, retries.
- **Observability:** Built-in metrics (Prometheus), tracing (Jaeger), access logs.
- **Access control:** Service-level authorization policies.

### 6.3 Monitoring Stack

**Prometheus + Grafana:**
- Prometheus for metrics collection (CPU, memory, request latency, queue depth).
- Grafana for dashboards (alert volume, crawl rate, system health).

**OpenTelemetry:**
- Distributed tracing across services.
- Trace IDs propagated via RabbitMQ message headers and HTTP headers.

**ELK (Elasticsearch, Logstash, Kibana):**
- Fluentd collects structured JSON logs from containers.
- Elasticsearch indexes logs for search.
- Kibana for log exploration and dashboard.

---

## 7. Proxy & Anonymity

### 7.1 Tor

**Version:** 0.4.8+

**Rationale:**
- Industry standard for accessing `.onion` services.
- SOCKS5 proxy interface for easy integration with Scrapy.
- Circuit rotation via `NEWNYM` signal for identity change.
- Widely deployed and well-documented.

### 7.2 I2P

**Version:** 2.5+

**Rationale:**
- Access to `.i2p` domains (some marketplaces/forums are I2P-only).
- Different anonymity properties than Tor (garlic routing vs onion routing).
- SOCKS5 proxy support.

### 7.3 HAProxy

**Version:** 2.9+

**Rationale:**
- Load balance across multiple Tor/I2P proxy instances.
- Health checks to remove dead proxies from pool.
- TCP mode for SOCKS5 proxy load balancing.

---

## 8. Development Tooling

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Primary development language |
| Poetry | 1.8+ | Python dependency management |
| Pytest | 8.2+ | Python testing framework |
| Black | 24.4+ | Python code formatting |
| Ruff | 0.5+ | Python linting |
| MyPy | 1.10+ | Python static type checking |
| Prettier | 3.3+ | Frontend code formatting |
| ESLint | 9.5+ | JavaScript/TypeScript linting |
| Playwright | 1.44+ | E2E frontend testing |

---

## 9. Technology Decision Matrix

| Requirement | Candidate Options | Selected | Reason |
|---|---|---|---|
| **API Framework** | FastAPI, Django REST, Flask, Node.js/Express | FastAPI | Async native, auto-docs, Pydantic |
| **Crawling** | Scrapy, Selenium, Puppeteer, asyncio | Scrapy | Mature, middleware, scheduling |
| **NLP Pipeline** | spaCy, NLTK, Stanford NLP, HuggingFace | spaCy (primary) | Production-ready, fast, extensible |
| **Deep Learning** | PyTorch, TensorFlow, JAX | PyTorch | Dynamic graphs, research-friendly |
| **Full-Text Search** | Elasticsearch, Solr, MeiliSearch | Elasticsearch | Rich aggregations, ILM, ecosystem |
| **Document Store** | MongoDB, CouchDB, DynamoDB | MongoDB | Schema flexibility, TTL indexes |
| **Graph DB** | Neo4j, ArangoDB, JanusGraph | Neo4j | Native graph, Cypher, community |
| **Message Queue** | RabbitMQ, Apache Kafka, Redis Streams | RabbitMQ | Mature, routing, DLQ, simpler ops |
| **Cache** | Redis, Memcached, Dragonfly | Redis | Multi-purpose (cache, queue, session) |
| **Frontend** | React, Vue, Svelte, Next.js | React + Vite | Ecosystem, TypeScript, visualization libs |
| **Container Orchestration** | Kubernetes, Docker Swarm, Nomad | Kubernetes | Industry standard, auto-scaling |
| **Service Mesh** | Istio, Linkerd, Consul Connect | Istio | Feature-rich, mTLS, observability |
| **Object Storage** | MinIO, AWS S3, Ceph | MinIO | S3-compatible, self-hosted |
| **Monitoring** | Prometheus/Grafana, Datadog, New Relic | Prometheus/Grafana | Open source, K8s native |
| **Secrets** | HashiCorp Vault, AWS Secrets Manager, K8s Secrets | HashiCorp Vault | Multi-cloud, dynamic secrets, audit |

---

## 10. Versioning Strategy

- **Dependencies:** Pinned to exact versions in `pyproject.toml` / `package.json` with lockfiles.
- **Service images:** Tagged with Git commit SHA + semantic version (e.g., `crawler-service:1.2.0-a1b2c3d`).
- **API versioning:** URL-based (`/v1/`, `/v2/`). Breaking changes require version bump.
- **Database migrations:** Incremental scripts with rollback support (MongoDB: custom scripts; Elasticsearch: reindex; Neo4j: Cypher scripts).

---

## 11. Hardware Sizing (Minimum for Production)

| Service | CPU | RAM | Storage | GPU |
|---|---|---|---|---|
| API Gateway | 2 cores | 4 GB | 20 GB | — |
| Crawler Service (×3) | 4 cores each | 8 GB each | 50 GB each | — |
| Proxy Pool (×2) | 2 cores | 4 GB | 20 GB | — |
| Content Parser (×2) | 2 cores | 4 GB each | 20 GB each | — |
| NLP Engine | 8 cores | 32 GB | 50 GB | NVIDIA T4+ (16 GB) |
| Threat Scoring | 4 cores | 8 GB | 20 GB | — |
| Alert Engine | 2 cores | 4 GB | 20 GB | — |
| Actor Profiling | 4 cores | 8 GB | 50 GB | — |
| MongoDB | 8 cores | 32 GB | 500 GB SSD | — |
| Elasticsearch (×3) | 8 cores each | 32 GB each | 2 TB SSD each | — |
| Neo4j | 8 cores | 32 GB | 200 GB SSD | — |
| RabbitMQ (×3) | 2 cores each | 4 GB each | 50 GB each | — |
| Redis | 4 cores | 16 GB | 50 GB SSD | — |
| MinIO (×3) | 4 cores each | 8 GB each | 5 TB each | — |
| Frontend | 2 cores | 4 GB | 10 GB | — |

---

## 12. Software Bill of Materials (SBOM)

A complete SBOM will be generated before deployment using:
- Python: `pip-audit` + `safety`
- Node.js: `npm audit` + `synk`
- Container scanning: `Trivy` in CI pipeline
- Regular dependency updates via Dependabot / Renovate

---

*Document maintained by the Architecture Team.*
