# DarkTrace — Architecture Overview

> **Version:** 1.0  
> **Date:** 2026-06-03  
> **Status:** Draft  
> **Audience:** Engineering Team, Architecture Review Board, Stakeholders

---

## 1. Executive Summary

DarkTrace is a full-scale production intelligence platform for law enforcement and cybercrime investigators. It automates the discovery, monitoring, analysis, and reporting of threat intelligence from dark web sources (Tor, I2P, anonymous forums, marketplaces, paste sites). The system follows an **event-driven microservices architecture** to achieve loose coupling, independent scalability, and fault isolation across its crawling, analysis, alerting, and reporting pipelines.

---

## 2. Architectural Style & Rationale

| Attribute | Decision | Rationale |
|---|---|---|
| **Style** | Event-Driven Microservices | Each major capability (crawling, NLP, scoring, alerting) has distinct scaling, resource, and deployment needs. Event-driven messaging decouples producers from consumers. |
| **Communication** | Asynchronous (RabbitMQ) + Synchronous (REST/gRPC) | Crawl jobs, analysis tasks, and alerts flow asynchronously via message queues. Query operations (dashboard, search, export) use synchronous REST APIs. |
| **Data Storage** | Polyglot Persistence | Different data shapes demand different stores: documents (MongoDB), full-text search (Elasticsearch), graph (Neo4j). |
| **Deployment** | Docker Compose (dev) → Kubernetes (prod) | Containerized services allow consistent environments; Kubernetes enables auto-scaling, rolling updates, and self-healing. |

---

## 3. High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │  React.js    │  │  SIEM via   │  │  REST API    │  │  CLI / Admin  │   │
│  │  Dashboard   │  │  Syslog/Web │  │  Consumers   │  │  Scripts      │   │
│  └──────┬───────┘  └──────┬──────-┘  └──────┬───────┘  └───────┬───────┘   │
├─────────┼─────────────────┼─────────────────┼──────────────────┼────────────┤
│         │                 │                 │                  │            │
│  ┌──────▼─────────────────▼─────────────────▼──────────────────▼──────┐    │
│  │                      API GATEWAY (FastAPI)                         │    │
│  │  Auth (JWT/OAuth2) • Rate Limiting • Request Validation • Logging  │    │
│  └──────┬─────────────────┬─────────────────┬──────────────────┬──────┘    │
├─────────┼─────────────────┼─────────────────┼──────────────────┼────────────┤
│         │                 │                 │                  │            │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌───────▼──────┐     │
│  │  Crawler    │  │  Content    │  │  Auth &     │  │  Export &    │     │
│  │  Service    │  │  Parser     │  │  User Mgmt  │  │  Report Svc  │     │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘  └──────┬───────┘     │
│         │                │                                  │             │
│  ┌──────▼──────┐  ┌──────▼──────────────┐                  │             │
│  │  Proxy Pool │  │  NLP / Analysis     │                  │             │
│  │  Manager    │  │  Engine             │                  │             │
│  └─────────────┘  └──────┬──────────────┘                  │             │
│         │                │                                 │             │
│         │         ┌──────▼──────────────┐                  │             │
│         │         │  Threat Scoring     │                  │             │
│         │         │  Engine             │                  │             │
│         │         └──────┬──────────────┘                  │             │
│         │                │                                 │             │
│         │         ┌──────▼──────────────┐                  │             │
│         │         │  Alert Engine       │                  │             │
│         │         └──────┬──────────────┘                  │             │
│         │                │                                 │             │
│         │         ┌──────▼──────────────┐                  │             │
│         │         │  Actor Profiling    │                  │             │
│         │         │  Engine             │                  │             │
│         │         └─────────────────────┘                  │             │
│         │                │                                 │             │
├─────────┼────────────────┼─────────────────────────────────┼─────────────┤
│         │                │           MESSAGE BROKER (RabbitMQ)           │
│         └────────────────┼─────────────────────────────────┘             │
│                          │                                               │
│  ┌───────────────────────┼───────────────────────────────────────────┐   │
│  │         DATA LAYER    │                                           │   │
│  │  ┌────────────┐ ┌────▼────────┐ ┌────────────────┐               │   │
│  │  │  MongoDB   │ │Elasticsearch│ │    Neo4j       │               │   │
│  │  │  - Raw docs │ │ - Full-text │ │ - Actor graph  │               │   │
│  │  │  - Users    │ │ - Analytics │ │ - Relationships │               │   │
│  │  │  - Config   │ │ - Aggreg.  │ │ - Transaction   │               │   │
│  │  │  - Audit    │ │             │ │   trails       │               │   │
│  │  └────────────┘ └─────────────┘ └────────────────┘               │   │
│  │                                                                   │   │
│  │  ┌────────────┐ ┌─────────────┐ ┌────────────────┐               │   │
│  │  │   Redis    │ │    S3 /     │ │  Blockchain    │               │   │
│  │  │  - Cache   │ │   MinIO     │ │  (optional)    │               │   │
│  │  │  - Queue   │ │  - Crawled  │ │  - Evidence    │               │   │
│  │  │  - Session │ │    Assets   │ │    Sealing     │               │   │
│  │  └────────────┘ └─────────────┘ └────────────────┘               │   │
│  └───────────────────────────────────────────────────────────────────────┘
```

---

## 4. System Context & Actors

| Actor | Description |
|---|---|
| **Investigator** | Primary user: browses dashboard, configures watchlists, reviews alerts, generates reports. |
| **Administrator** | Manages users, system configuration, crawler targets, audit logs. |
| **SIEM System** | External security tool that consumes DarkTrace alerts via Syslog/Webhook. |
| **Dark Web** | Tor/I2P hidden services, anonymous forums, marketplaces, paste sites. |
| **Surface Web** | Optional: social media, clear-net forums for cross-correlation. |

---

## 5. Service Responsibilities

| Service | Responsibility |
|---|---|
| **API Gateway** | Auth, rate limiting, routing, request validation, API documentation (OpenAPI). |
| **Crawler Service** | Manages crawl jobs, rotates Tor/I2P proxies, schedules re-scans, emits raw HTML/documents to message queue. |
| **Proxy Pool Manager** | Maintains a pool of Tor and I2P exit nodes with health checking, RTT tracking, and automatic rotation. |
| **Content Parser** | Consumes raw content, extracts structured data (HTML→text, marketplace listings, forum posts), classifies document type. |
| **NLP / Analysis Engine** | Entity extraction, language detection/translation, sentiment analysis, keyword matching, classification of threat content. |
| **Threat Scoring Engine** | Computes threat severity scores based on configurable rules and ML models. |
| **Alert Engine** | Matches scored content against user watchlists and alert rules; dispatches notifications (email, webhook, SIEM). |
| **Actor Profiling Engine** | Correlates pseudonyms across sites, analyzes writing style (stylometry), maps transaction trails and social graphs. |
| **Export & Report Service** | Generates PDF/CSV/JSON reports, handles SIEM integration (CEF/LEEF formats). |
| **User Management Service** | CRUD for users, roles, permissions, authentication tokens. |
| **Blockchain Service** (opt.) | Hashes evidence to blockchain for tamper-proof chain of custody. |

---

## 6. Cross-Cutting Concerns

### 6.1 Security
- **Defense in Depth**: Network segmentation, WAF, API keys, JWT with short TTL.
- **Encryption at Rest**: All databases use AES-256 encryption.
- **Encryption in Transit**: mTLS between services, HTTPS for external communication.
- **Secrets Management**: HashiCorp Vault for API keys, database passwords, Tor credentials.
- **Audit Logging**: Every user action and system event is logged to MongoDB audit collection with tamper-evident hashing.

### 6.2 Observability
- **Metrics**: Prometheus + Grafana dashboards per service.
- **Logging**: Structured JSON logging via Fluentd → Elasticsearch → Kibana (ELK stack).
- **Tracing**: OpenTelemetry for distributed tracing across services.
- **Health Checks**: Each service exposes `/health` and `/ready` endpoints.

### 6.3 Resilience
- **Circuit Breakers**: For external dependencies (Tor network, SIEM endpoints).
- **Retry with Backoff**: All inter-service calls use exponential backoff.
- **Dead Letter Queues**: Failed messages sent to DLQ for manual inspection.
- **Service Redundancy**: Critical services (crawler, scoring, alert) run with N+1 redundancy.

### 6.4 Compliance
- **Data Retention**: Configurable retention policies per data type (raw pages: 90d, alerts: 1y, audit: 7y).
- **Access Control**: Role-based (RBAC) with investigator, admin, auditor roles.
- **Chain of Custody**: All exported evidence is digitally signed and optionally blockchain-sealed.

---

## 7. Network Architecture (Deployment)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                       │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Public Ingress │  │  DMZ        │  │  Private    │             │
│  │  (nginx +      │  │  Proxy Pool  │  │  Services   │             │
│  │   Cloudflare)  │  │  Manager     │  │  - API GW   │             │
│  └─────────────┘  └─────────────┘  │  - Crawler   │             │
│                                    │  - Parser    │             │
│  ┌─────────────────────────────────┤  - NLP       │             │
│  │         Service Mesh (Istio)    │  - Scoring   │             │
│  │  Mutual TLS • Traffic Mgmt      │  - Alert     │             │
│  │  Observability • Access Control  │  - Profiling │             │
│  └─────────────────────────────────┘  - Export    │             │
│                                    └─────────────┘             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Data Layer                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ MongoDB  │ │ Elastic  │ │  Neo4j   │ │  Redis   │   │   │
│  │  │ (SSD)   │ │ (SSD)   │ │ (SSD)   │ │ (RAM)   │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Message Broker                         │   │
│  │              RabbitMQ (Mirrored Queues)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Architecture Decision Records (Summary)

| ADR | Decision | Rationale |
|---|---|---|
| **ADR-001** | Event-driven microservices over monolith | Independent scaling of crawling vs analysis; fault isolation; team autonomy. |
| **ADR-002** | RabbitMQ over Kafka | Lower operational complexity; built-in DLQ; sufficient throughput for crawl volumes. Kafka if >1M msgs/sec needed. |
| **ADR-003** | Polyglot persistence | MongoDB for flexible schema; Elasticsearch for search; Neo4j for graph — each optimized for its access pattern. |
| **ADR-004** | FastAPI over Django REST | Native async support better for IO-bound crawling/scraping; automatic OpenAPI generation. |
| **ADR-005** | Scrapy over raw asyncio | Mature ecosystem for crawling; built-in retry, middleware, scheduler. |
| **ADR-006** | Tor + I2P via SOCKS5 proxies | Standard protocol support; ability to rotate exit nodes; transparency for debugging. |

---

## 9. Glossary

| Term | Definition |
|---|---|
| **.onion** | Tor hidden service domain name |
| **I2P** | Invisible Internet Project — anonymous network layer |
| **PII** | Personally Identifiable Information |
| **SIEM** | Security Information and Event Management |
| **SOCKS5** | Proxy protocol used for Tor/I2P routing |
| **Stylometry** | Linguistic style analysis for authorship attribution |
| **CEF/LEEF** | Common Event Format / Log Event Extended Format (SIEM standards) |

---

## 10. Next Steps

1. Validate architecture with stakeholders (cyber crime investigators).
2. Finalize API contracts between services.
3. Set up CI/CD pipeline (GitHub Actions → Docker registry → Kubernetes).
4. Implement core crawling pipeline (MVP).
5. Iterate on NLP models with labelled threat data.

---

*Document maintained by the Architecture Team. For questions, contact the system architect.*
