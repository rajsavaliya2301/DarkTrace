# DarkTrace — Data Flow Design

> **Version:** 1.0  
> **Date:** 2026-06-03

---

## 1. End-to-End Data Pipeline

```
Dark Web    Crawler    Content     NLP /      Threat     Alert      Dashboard
(Sources)──►Service──►Parser──►Analysis──►Scoring──►Engine──►Frontend
   │          │          │          │          │          │          │
   │          │          │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼          ▼          ▼
 RabbitMQ  MongoDB   MinIO/S3  RabbitMQ   RabbitMQ   RabbitMQ   WebSocket
           (raw)     (assets)   (parsed)   (scored)   (alerts)   (live)
```

---

## 2. Primary Data Pipeline (Crawl to Alert)

```
Stage 1: Crawling
───────────────────────────────────────────────────────────────────
 [Scheduler] ──trigger──▶ [Crawler Job] ──▶ [Scrapy Spider]
                                                 │
                                    ┌────────────┴─────────────┐
                                    │                          │
                                    ▼                          ▼
                              [RabbitMQ]                 [MinIO/S3]
                              exchange:                    store raw
                              crawl.raw                    HTML/assets
                                    │
                                    │ routing: raw.page
                                    ▼
Stage 2: Parsing
───────────────────────────────────────────────────────────────────
 [Content Parser] ──consume──▶ [Document Classifier]
                                    │
                          ┌─────────┴──────────┐
                          │                    │
                    [Site-Specific]      [Generic Fallback]
                    Parser                Parser (readability)
                          │                    │
                          └─────────┬──────────┘
                                    ▼
                              [Entity Pre-Extractor]
                              (URLs, emails, crypto addrs)
                                    │
                                    ▼
                              [RabbitMQ]
                              exchange: content.parsed
                              routing: parsed.{type}
                                    │
                                    ▼
Stage 3: Analysis
───────────────────────────────────────────────────────────────────
 [NLP Engine] ──consume──▶ [Language Detection]
                                    │
                          ┌─────────┴──────────┐
                          │ (non-English)      │ (English)
                          ▼                    │
                    [Translator]               │
                          │                    │
                          └─────────┬──────────┘
                                    ▼
                              [NER Pipeline]
                              (people, orgs, crypto addrs, PII)
                                    │
                                    ▼
                              [Keyword/PII Matcher]
                              (watchlist matching)
                                    │
                                    ▼
                              [Sentiment & Intent Analysis]
                                    │
                                    ▼
                              [Threat Classification]
                                    │
                                    ▼
                              [RabbitMQ]
                              exchange: analysis.complete
                              routing: analysis.{category}
                                    │
                                    ▼
Stage 4: Scoring
───────────────────────────────────────────────────────────────────
 [Threat Scoring Engine] ──consume──▶ [Scoring Algorithm]
                                    │
                                    ▼
                              [RabbitMQ]
                              exchange: scoring.complete
                              routing: scored.{severity}
                                    │
                                    ▼
Stage 5: Alerting
───────────────────────────────────────────────────────────────────
 [Alert Engine] ──consume──▶ [Watchlist Rule Matcher]
                                    │
                          ┌─────────┴──────────┐
                          │                    │
                    [Dedup Check]       [No Match] → Archive
                          │
                          ▼
                    [Severity Evaluation]
                          │
                    ┌─────┴──────┐
                    │            │
                    ▼            ▼
              [Notification]  [RabbitMQ]
              (email/webhook) exchange: alerts.final
               ┌─────┘         routing: alert.{severity}
               │                     │
               ▼                     ▼
          [SIEM System]       [Dashboard]
                              (WebSocket push)
```

---

## 3. Actor Profiling Data Flow

```
Parsed content (from RabbitMQ exchange: content.parsed)
        │
        ▼
[Actor Profiling Engine]
        │
        ├── Extract author pseudonym → Query Neo4j
        │       │
        │       ├── Found → Update profile
        │       │            ├── Increment activity count
        │       │            ├── Update last seen
        │       │            ├── Add new relationships
        │       │            └── Update stylometry corpus
        │       │
        │       └── Not found → Create new profile
        │                      ├── Generate UUID
        │                      ├── Store pseudonym
        │                      ├── Store first seen timestamp
        │                      └── Store initial writing sample
        │
        ├── Extract entities (BTC addresses, PGP keys)
        │       └── Link to actor or pseudonym in Neo4j
        │
        ├── Stylometry comparison
        │       ├── Compare writing sample against existing profiles
        │       └── If similarity > threshold → link pseudonyms
        │
        └── Write profile_update event to RabbitMQ
            exchange: profiling.update
```

---

## 4. Search and Query Data Flow

```
User Query (Dashboard)
        │
        ▼
[API Gateway] ──▶ [Search Service]
        │
        ├── Full-text query → Elasticsearch
        │       ├── Search across crawled content
        │       ├── Faceted filters (date range, source, category, severity)
        │       └── Return paginated results with highlights
        │
        ├── Actor query → Neo4j
        │       ├── Traverse graph for actor profile
        │       ├── Find related actors, transactions
        │       └── Return graph data for visualization
        │
        └── Metadata query → MongoDB
                ├── Crawl status, user config, watchlists
                └── Return document data
```

---

## 5. Export and Report Data Flow

```
Export Request (Dashboard)
        │
        ▼
[API Gateway] ──▶ [Export Service]
        │
        ├── Collect data
        │   ├── Query Elasticsearch for relevant content
        │   ├── Query Neo4j for actor relationships
        │   ├── Query MongoDB for metadata
        │   └── Collect raw evidence from MinIO/S3
        │
        ├── Generate Report
        │   ├── PDF: Render HTML template → WeasyPrint → PDF
        │   ├── CSV: Stream data as CSV rows
        │   └── JSON: Package data as JSON document
        │
        ├── Sign Evidence
        │   ├── Compute SHA-256 of report content
        │   ├── Sign with service private key (ECDSA)
        │   └── Optionally hash to blockchain
        │
        └── Store & Return
            ├── Upload to MinIO/S3 with signed URL
            └── Return download URL (1-hour TTL)
```

---

## 6. Configuration Management Flow

```
Admin Action (Dashboard)
        │
        ▼
[API Gateway] ──▶ [User Management / Config Service]
        │
        ├── Update watchlist
        │   ├── Store in MongoDB (watchlists collection)
        │   └── Publish config update event to RabbitMQ
        │       exchange: config.updates
        │       routing: config.watchlist
        │
        ├── Add crawl target
        │   ├── Store in MongoDB (crawl_targets collection)
        │   └── Notify Crawler Scheduler
        │
        ├── Update alert rules
        │   ├── Store in MongoDB (alert_rules collection)
        │   └── Publish to RabbitMQ
        │       routing: config.alert_rules
        │
        └── Manage users
            └── CRUD in MongoDB (users collection)
```

---

## 7. Message Queue Topology (RabbitMQ)

### Exchanges

| Exchange Name | Type | Description |
|---|---|---|
| `crawl.raw` | `topic` | Raw crawled content from spiders |
| `content.parsed` | `topic` | Parsed/structured content |
| `analysis.complete` | `topic` | NLP analysis results |
| `scoring.complete` | `topic` | Threat scoring results |
| `alerts.final` | `topic` | Triggered alerts |
| `profiling.update` | `topic` | Actor profile updates |
| `config.updates` | `fanout` | Configuration changes broadcast |

### Key Queues & Bindings

| Queue | Exchange | Routing Key | Consumers |
|---|---|---|---|
| `parser.raw` | `crawl.raw` | `raw.page` | Content Parser |
| `analysis.parsed` | `content.parsed` | `parsed.*` | NLP Engine |
| `analysis.parsed.actor` | `content.parsed` | `parsed.*` | Actor Profiling |
| `scoring.analysis` | `analysis.complete` | `analysis.*` | Threat Scoring |
| `alert.scored` | `scoring.complete` | `scored.*` | Alert Engine |
| `dashboard.alerts` | `alerts.final` | `alert.#` | WebSocket Server |
| `siem.alerts` | `alerts.final` | `alert.high`, `alert.critical` | SIEM Forwarder |
| `config.all` | `config.updates` | `#` | All Services (config cache refresh) |

### Dead Letter Queue (DLQ)

```
Any Queue → DLX: dlx.exchange
               │
               ▼
          dlq.queue
               │
               ▼
     [Manual Inspection / Retry Script]
```

---

## 8. Storage Data Flows

### 8.1 MongoDB Flow

```
┌─────────────────────────────────────────────────────────┐
│                      MongoDB                             │
│                                                          │
│  Collections:                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │ raw_content │ │ crawl_jobs  │ │ users       │        │
│  │ - crawl_id  │ │ - target_url│ │ - email     │        │
│  │ - url       │ │ - status    │ │ - role      │        │
│  │ - html      │ │ - schedule  │ │ - hash      │        │
│  │ - fetched_at│ │ - result    │ └─────────────┘        │
│  └─────────────┘ └─────────────┘                        │
│  ┌──────────────┐┌──────────────┐┌──────────────┐       │
│  │ watchlists   ││ alert_rules  ││ audit_logs   │       │
│  │ - keywords   ││ - conditions ││ - user       │       │
│  │ - patterns   ││ - actions    ││ - action     │       │
│  │ - created_by ││ - severity   ││ - timestamp  │       │
│  └──────────────┘└──────────────┘└──────────────┘       │
│  ┌──────────────┐┌──────────────┐                        │
│  │ reports      ││ blockchain   │                        │
│  │ - generated  ││ tx_log       │                        │
│  │ - format     ││ - tx_hash    │                        │
│  │ - signed_url ││ - content    │                        │
│  └──────────────┘│   hash       │                        │
│                  └──────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Elasticsearch Flow

```
[Content Parser / NLP Engine]
        │
        ▼
[Elasticsearch Bulk Index]
        │
        ├── Index: `crawled_content` (primary)
        │   ├── Full document text with analysis results
        │   ├── Field: title, content, author, entities, scores
        │   ├── Field: threat_classification, severity
        │   ├── Field: source_type, site_name, crawl_timestamp
        │   └── Mapping: keyword, text, date, float, geo_point
        │
        ├── Index: `alerts` (denormalized for fast search)
        │   ├── Alert summary + linked content snippets
        │   └── TTL-based rollover (hot/warm/cold)
        │
        ├── Index: `actors` (searchable actor profiles)
        │   └── Pseudonyms, total posts, first/last seen, risk score
        │
        └── Index: `audit_logs` (system events)
            └── Rotated daily → 90-day retention
```

### 8.3 Neo4j Flow

```
[Content Parser / Actor Profiling]
        │
        ▼
[Neo4j Graph Updates]
        │
        ├── Node: Actor
        │   ├── Properties: uuid, risk_score, total_posts, first_seen, last_seen
        │   └── Labels: Actor, ThreatActor, Vendor, Buyer
        │
        ├── Node: Pseudonym
        │   ├── Properties: name, first_seen, platforms[]
        │   └── Labels: Pseudonym
        │
        ├── Node: Content
        │   ├── Properties: url, title, crawl_timestamp, content_hash
        │   └── Labels: Content, ForumPost, Listing, Paste
        │
        ├── Node: Site
        │   ├── Properties: domain, type, status, reputation_score
        │   └── Labels: Site, OnionSite, I2PSite
        │
        ├── Node: Entity
        │   ├── Properties: value, type, first_seen
        │   └── Labels: Entity, BTCAddress, Email, PGPKey
        │
        ├── Relationship: (:Actor)-[:USES]->(:Pseudonym)
        ├── Relationship: (:Actor)-[:POSTED_ON]->(:Site)
        ├── Relationship: (:Actor)-[:MENTIONED_IN]->(:Content)
        ├── Relationship: (:Pseudonym)-[:CONTROLS]->(:BTCAddress)
        ├── Relationship: (:Content)-[:CONTAINS]->(:Entity)
        └── Relationship: (:Actor)-[:TRANSACTED_WITH]->(:Actor)
```

---

## 9. Data Retention & Lifecycle

| Data Type | Storage | Retention | Deletion Policy |
|---|---|---|---|
| Raw crawled content | MongoDB + MinIO | 90 days | Scheduled TTL index + S3 lifecycle |
| Parsed content | Elasticsearch | 180 days | ILM hot→warm→delete |
| Analysis results | Elasticsearch | 180 days | ILM policy |
| Alerts | Elasticsearch + MongoDB | 1 year | Archive to cold storage then delete |
| Actor profiles | Neo4j | Indefinite | Manual review |
| User data | MongoDB | Until account deletion | Cascade delete |
| Watchlists | MongoDB | Indefinite | Manual |
| Audit logs | Elasticsearch | 7 years | ILM policy |
| Reports | MinIO/S3 | 5 years | S3 lifecycle |
| Blockchain tx logs | MongoDB | Indefinite | Never deleted |

---

## 10. Critical Data Flow: Alert to Notification

```
Time: T0     T0+1s      T0+2s       T0+3s       T0+4s       T0+5s
Crawler    Parser     NLP         Scoring     Alert       Dashboard
Fetch      Extract    Classify    Compute     Match       Notify
─────▶     ─────▶     ─────▶      ─────▶      ─────▶      ─────▶
 │          │          │           │           │           │
 │pub:      │pub:      │pub:       │pub:       │pub:       │WS push
 │raw.page  │parsed    │analysis   │scored     │alert      │live alert
 │          │.market   │.ransomware│.high      │.critical  │+ email
 ▼          ▼          ▼           ▼           ▼           ▼
MQ         MQ         MQ          MQ          MQ          WS

Total latency: ~5 seconds (typical dark web crawl → dashboard alert)
```

---

*Document maintained by the Architecture Team.*
