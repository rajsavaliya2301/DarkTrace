# DarkTrace — Database Schema Design

> **Version:** 1.0  
> **Date:** 2026-06-03  
> **Databases:** MongoDB 7.0+, Elasticsearch 8.14+, Neo4j 5.21+

---

## 1. MongoDB Schemas

MongoDB is used as the primary operational data store - it holds raw crawled content, user data, configuration, crawl metadata, and audit logs.

### 1.1 `raw_content` Collection

Stores the raw fetched content from crawls. Used for evidence preservation and reprocessing.

```javascript
{
  _id: ObjectId,
  crawl_id: UUID,
  url: String,
  normalized_url: String,
  source_type: String,
  site_name: String,
  fetch_timestamp: ISODate,
  http_status: Int32,
  response_headers: Object,
  content_type: String,
  raw_html: String,
  content_hash: String,
  content_size_bytes: Int64,
  text_content: String,
  proxy_used: String,
  error: { code: String, message: String, retry_count: Int32 },
  processing_status: String,
  parsed_at: ISODate,
  analyzed_at: ISODate,
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes:
// { url: 1, fetch_timestamp: -1 }
// { content_hash: 1 }
// { crawl_id: 1 }
// { fetch_timestamp: -1 }
// { processing_status: 1 }
// { created_at: 1 }, TTL: 90 days
```
### 1.2 `crawl_jobs` Collection

```javascript
{
  _id: UUID,
  target_id: UUID,
  target_url: String,
  source_type: String,
  status: String,
  priority: Int32,
  scheduled_at: ISODate,
  started_at: ISODate,
  completed_at: ISODate,
  pages_fetched: Int32,
  pages_total: Int32,
  pages_failed: Int32,
  errors: [{ url: String, error_code: String, error_message: String, timestamp: ISODate }],
  proxy_pool_used: [String],
  crawl_depth: Int32,
  triggered_by: String,
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes: { target_id: 1, started_at: -1 }, { status: 1 }, { scheduled_at: 1 }
```

### 1.3 `crawl_targets` Collection

```javascript
{
  _id: UUID,
  url: String,
  site_name: String,
  source_type: String,
  status: String,
  crawl_frequency: String,
  parser_type: String,
  parser_config: {
    title_xpath: String, body_xpath: String, author_xpath: String,
    date_xpath: String, price_xpath: String, link_selectors: [String]
  },
  auth_info: { username: String, password: String, login_url: String },
  politeness_config: { crawl_delay: Float64, max_concurrent: Int32, max_depth: Int32 },
  scope: { allowed_domains: [String], exclude_patterns: [String], include_patterns: [String] },
  last_crawled_at: ISODate,
  last_crawl_status: String,
  page_count: Int64,
  reputation_score: Float64,
  is_tor_only: Boolean,
  notes: String,
  tags: [String],
  added_by: UUID,
  added_at: ISODate,
  updated_at: ISODate
}

// Indexes: { url: 1 } unique, { status: 1, crawl_frequency: 1 }, { source_type: 1 }
```

### 1.4 `users` Collection

```javascript
{
  _id: UUID,
  email: String,
  password_hash: String,
  name: String,
  role: String,
  is_active: Boolean,
  is_locked: Boolean,
  failed_login_attempts: Int32,
  locked_until: ISODate,
  last_login_at: ISODate,
  last_login_ip: String,
  mfa_enabled: Boolean,
  mfa_secret: String,
  api_keys: [{
    key_id: UUID, key_hash: String, name: String,
    permissions: [String], is_active: Boolean,
    last_used_at: ISODate, created_at: ISODate, expires_at: ISODate
  }],
  preferences: {
    theme: String,
    notifications: { email_alerts: Boolean, dashboard_alerts: Boolean, sms_alerts: Boolean },
    default_report_format: String,
    items_per_page: Int32
  },
  refresh_tokens: [{ token_hash: String, device_info: String, ip_address: String, created_at: ISODate, expires_at: ISODate }],
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes: { email: 1 } unique, { role: 1 }, { "api_keys.key_hash": 1 }
```

### 1.5 `watchlists` Collection

```javascript
{
  _id: UUID,
  name: String,
  description: String,
  keywords: [String],
  regex_patterns: [{ pattern: String, label: String, case_sensitive: Boolean }],
  entities: [String],
  severity_boost: Int32,
  is_active: Boolean,
  match_count: Int64,
  last_match_at: ISODate,
  created_by: UUID,
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes: { created_by: 1 }, { is_active: 1 }
```

### 1.6 `alert_rules` Collection

```javascript
{
  _id: UUID,
  name: String,
  description: String,
  enabled: Boolean,
  severity_threshold: Int32,
  conditions: [{ field: String, operator: String, value: Mixed }],
  notifications: [{ type: String, target: String, config: { format: String, auth_header: String } }],
  cooldown_minutes: Int32,
  dedup_field: String,
  match_count: Int64,
  last_triggered_at: ISODate,
  created_by: UUID,
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes: { enabled: 1 }, { "conditions.field": 1 }
```

### 1.7 `reports` Collection

```javascript
{
  _id: UUID,
  type: String,
  format: String,
  status: String,
  parameters: Object,
  file_path: String,
  file_size_bytes: Int64,
  content_hash: String,
  digital_signature: String,
  blockchain_tx: { chain: String, tx_hash: String, block_number: Int64, block_timestamp: ISODate },
  download_token: String,
  download_count: Int32,
  expires_at: ISODate,
  created_by: UUID,
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes: { created_by: 1, created_at: -1 }, { status: 1 }
```

### 1.8 `audit_logs` Collection

```javascript
{
  _id: ObjectId,
  timestamp: ISODate,
  user_id: UUID,
  user_name: String,
  user_role: String,
  action: String,
  resource_type: String,
  resource_id: String,
  details: { before: Mixed, after: Mixed, change_summary: String },
  ip_address: String,
  user_agent: String,
  request_id: String,
  tamper_hash: String,
  previous_hash: String
}

// Indexes: { timestamp: -1 }, { user_id: 1, timestamp: -1 }, { action: 1 }
// TTL: 7 years (2555 days)
```

### 1.9 `dedup_cache` Collection

```javascript
{
  _id: String,  // dedup_key = sha256(content_id + rule_id)
  alert_id: UUID,
  rule_id: UUID,
  content_id: String,
  triggered_at: ISODate,
  expires_at: ISODate  // TTL index
}

// Index: { expires_at: 1 }, TTL auto-expire
```

---

## 2. Elasticsearch Index Mappings

Elasticsearch is used for **full-text search and analytics**. Data is denormalized for query performance.

### 2.1 Index: `crawled_content`

Primary search index for all crawled and analyzed content.

```json
{
  "index": "crawled_content",
  "settings": {
    "number_of_shards": 5,
    "number_of_replicas": 2,
    "analysis": {
      "analyzer": {
        "russian_analyzer": { "type": "russian" },
        "arabic_analyzer": { "type": "arabic" }
      }
    }
  },
  "mappings": {
    "properties": {
      "id":                   { "type": "keyword" },
      "crawl_id":             { "type": "keyword" },
      "url":                  { "type": "keyword", "index": false },
      "source_type":          { "type": "keyword" },
      "site_name":            { "type": "keyword" },
      "document_type":        { "type": "keyword" },
      "title": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" },
          "english": { "type": "text", "analyzer": "english" }
        }
      },
      "content_text": {
        "type": "text",
        "fields": {
          "english": { "type": "text", "analyzer": "english" },
          "russian": { "type": "text", "analyzer": "russian" },
          "arabic": { "type": "text", "analyzer": "arabic" }
        }
      },
      "author": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "published_date":       { "type": "date" },
      "crawl_timestamp":      { "type": "date" },
      "language":             { "type": "keyword" },
      "translated_text":      { "type": "text", "analyzer": "english" },
      "entities": {
        "properties": {
          "emails":           { "type": "keyword" },
          "btc_addresses":    { "type": "keyword" },
          "eth_addresses":    { "type": "keyword" },
          "xmr_addresses":    { "type": "keyword" },
          "phone_numbers":    { "type": "keyword" },
          "ip_addresses":     { "type": "ip" },
          "persons":          { "type": "keyword" },
          "organizations":    { "type": "keyword" },
          "keywords_matched": { "type": "keyword" }
        }
      },
      "analysis": {
        "properties": {
          "sentiment": {
            "properties": {
              "threat_intent":  { "type": "float" },
              "hostility":      { "type": "float" },
              "urgency":        { "type": "float" }
            }
          },
          "classification": {
            "properties": {
              "primary":        { "type": "keyword" },
              "secondary":      { "type": "keyword" },
              "confidence":     { "type": "float" }
            }
          }
        }
      },
      "scoring": {
        "properties": {
          "score":            { "type": "integer" },
          "severity":         { "type": "keyword" }
        }
      },
      "metadata": {
        "properties": {
          "price":    { "type": "text" },
          "currency": { "type": "keyword" },
          "category": { "type": "keyword" },
          "tags":     { "type": "keyword" }
        }
      },
      "content_hash":         { "type": "keyword" },
      "processing_status":    { "type": "keyword" },
      "created_at":           { "type": "date" },
      "updated_at":           { "type": "date" }
    }
  }
}
```

### 2.2 Index: `alerts`

Denormalized alert index for fast searching and aggregation.

```json
{
  "index": "alerts",
  "settings": { "number_of_shards": 3, "number_of_replicas": 2 },
  "mappings": {
    "properties": {
      "id":                   { "type": "keyword" },
      "title":                { "type": "text", "analyzer": "english" },
      "severity":             { "type": "keyword" },
      "score":                { "type": "integer" },
      "status":               { "type": "keyword" },
      "category":             { "type": "keyword" },
      "source_type":          { "type": "keyword" },
      "source_url":           { "type": "keyword", "index": false },
      "source_site":          { "type": "keyword" },
      "summary":              { "type": "text", "analyzer": "english" },
      "matched_keywords":     { "type": "keyword" },
      "actor_pseudonym":      { "type": "keyword" },
      "actor_id":             { "type": "keyword" },
      "assignee":             { "type": "keyword" },
      "created_at":           { "type": "date" },
      "updated_at":           { "type": "date" }
    }
  }
}
```

### 2.3 Index: `actors`

Searchable actor profiles.

```json
{
  "index": "actors",
  "settings": { "number_of_shards": 3, "number_of_replicas": 2 },
  "mappings": {
    "properties": {
      "id":                   { "type": "keyword" },
      "pseudonyms":           { "type": "keyword" },
      "risk_score":           { "type": "integer" },
      "first_seen":           { "type": "date" },
      "last_seen":            { "type": "date" },
      "total_posts":          { "type": "integer" },
      "active_platforms":     { "type": "keyword" },
      "top_categories":       { "type": "keyword" },
      "bio_summary":          { "type": "text", "analyzer": "english" },
      "linked_entities": {
        "properties": {
          "btc_addresses":    { "type": "keyword" },
          "emails":           { "type": "keyword" },
          "pgp_keys":         { "type": "keyword" }
        }
      }
    }
  }
}
```

### 2.4 Index: `audit_logs`

System audit events with daily rotation.

```json
{
  "index": "audit_logs",
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "timestamp":        { "type": "date" },
      "user_id":          { "type": "keyword" },
      "user_name":        { "type": "keyword" },
      "user_role":        { "type": "keyword" },
      "action":           { "type": "keyword" },
      "resource_type":    { "type": "keyword" },
      "resource_id":       { "type": "keyword" },
      "details":          { "type": "object", "enabled": false },
      "ip_address":       { "type": "ip" },
      "request_id":       { "type": "keyword" },
      "tamper_hash":      { "type": "keyword" }
    }
  }
}
```

---

## 3. Neo4j Graph Schema

Neo4j is used for **actor network analysis**, **relationship mapping**, and **entity linkage**.

### 3.1 Nodes

```cypher
// Actor Node
CREATE CONSTRAINT FOR (a:Actor) REQUIRE a.uuid IS UNIQUE;
CREATE (a:Actor {
  uuid: String,
  risk_score: Float,
  total_posts: Int,
  first_seen: DateTime,
  last_seen: DateTime,
  notes: String
})
// Labels: Actor, ThreatActor, Vendor, Buyer

// Pseudonym Node
CREATE CONSTRAINT FOR (p:Pseudonym) REQUIRE p.name IS UNIQUE;
CREATE (p:Pseudonym {
  name: String,
  first_seen: DateTime,
  last_seen: DateTime,
  platforms: [String],
  post_count: Int,
  stylometry_profile: String
})

// Content Node
CREATE (c:Content {
  uuid: String,
  url: String,
  title: String,
  content_hash: String,
  crawl_timestamp: DateTime,
  category: String,
  severity_score: Int
})
// Labels: Content, ForumPost, Listing, Paste

// Site Node
CREATE (s:Site {
  domain: String,
  type: String,              // "onion" | "i2p" | "surface"
  site_name: String,
  status: String,
  reputation_score: Float,
  first_discovered: DateTime,
  last_crawled: DateTime
})
// Labels: Site, OnionSite, I2PSite

// Entity Node
CREATE CONSTRAINT FOR (e:Entity) REQUIRE e.value IS UNIQUE;
CREATE (e:Entity {
  value: String,
  type: String,              // "btc_address" | "email" | "pgp_key" | "phone" | "xmr_address"
  first_seen: DateTime,
  last_seen: DateTime,
  total_mentions: Int
})

// Watchlist Node
CREATE (w:Watchlist {
  uuid: String,
  name: String,
  is_active: Boolean,
  severity_boost: Int,
  created_at: DateTime
})
```

### 3.2 Relationships

```cypher
// Actor to Pseudonym
CREATE (a:Actor)-[:USES {
  first_seen: DateTime,
  confidence: Float,
  method: String            // "explicit" | "stylometry" | "transaction_link"
}]->(p:Pseudonym)

// Actor to Content
CREATE (a:Actor)-[:POSTED {
  posted_at: DateTime,
  site: String,
  platform: String
}]->(c:Content)

// Actor to Actor (transactions)
CREATE (a1:Actor)-[:TRANSACTED_WITH {
  count: Int,
  first_seen: DateTime,
  last_seen: DateTime,
  total_value_btc: Float,
  currencies: [String]
}]->(a2:Actor)

// Pseudonym to Entity
CREATE (p:Pseudonym)-[:CONTROLS {
  first_seen: DateTime,
  confidence: Float
}]->(e:Entity)

// Content contains Entity
CREATE (c:Content)-[:MENTIONS {
  context: String,
  position: Int
}]->(e:Entity)

// Content posted on Site
CREATE (c:Content)-[:POSTED_ON {
  fetched_at: DateTime
}]->(s:Site)

// Actor active on Site
CREATE (a:Actor)-[:ACTIVE_ON {
  first_seen: DateTime,
  last_seen: DateTime,
  total_posts: Int
}]->(s:Site)

// Content references Content
CREATE (c1:Content)-[:REFERENCES {
  type: String              // "reply" | "quote" | "cross_post"
}]->(c2:Content)

// Pseudonym similarity (stylometry match)
CREATE (p1:Pseudonym)-[:STYLISTICALLY_SIMILAR {
  similarity_score: Float,
  model_version: String,
  analyzed_at: DateTime
}]->(p2:Pseudonym)
```

### 3.3 Common Cypher Queries

```cypher
// Find all pseudonyms of an actor
MATCH (a:Actor {uuid: $actorId})-[:USES]->(p:Pseudonym)
RETURN p.name, p.platforms, p.first_seen, p.last_seen

// Find transaction network of an actor (2 hops)
MATCH (a:Actor {uuid: $actorId})
OPTIONAL MATCH path = (a)-[:TRANSACTED_WITH*1..2]-(connected:Actor)
RETURN path

// Find actors who control a specific BTC address
MATCH (a:Actor)-[:USES]->(p:Pseudonym)-[:CONTROLS]->(e:Entity {value: $btcAddress})
RETURN a.uuid, p.name, e.value

// Find actors posting about specific category
MATCH (a:Actor)-[:POSTED]->(c:Content {category: $category})
WHERE c.crawl_timestamp >= $dateFrom
RETURN a.uuid, count(c) as postCount
ORDER BY postCount DESC

// Community detection (Louvain algorithm via Neo4j GDS)
CALL gds.louvain.stream('actor-graph')
YIELD nodeId, communityId
MATCH (a:Actor) WHERE id(a) = nodeId
RETURN a.uuid, communityId

// Find similar actors by shared entities
MATCH (a1:Actor {uuid: $actorId})-[:USES]->(:Pseudonym)-[:CONTROLS]->(e:Entity)<-[:CONTROLS]-(:Pseudonym)<-[:USES]-(a2:Actor)
WHERE a1 <> a2
RETURN a2.uuid, a2.risk_score, count(e) as sharedEntities
ORDER BY sharedEntities DESC
```

### 3.4 Graph Indexes

```cypher
CREATE INDEX actor_uuid IF NOT EXISTS FOR (a:Actor) ON (a.uuid);
CREATE INDEX pseudonym_name IF NOT EXISTS FOR (p:Pseudonym) ON (p.name);
CREATE INDEX entity_value IF NOT EXISTS FOR (e:Entity) ON (e.value);
CREATE INDEX site_domain IF NOT EXISTS FOR (s:Site) ON (s.domain);
CREATE INDEX content_uuid IF NOT EXISTS FOR (c:Content) ON (c.uuid);
CREATE INDEX content_timestamp IF NOT EXISTS FOR (c:Content) ON (c.crawl_timestamp);
```

### 3.5 Graph Projections (for GDS algorithms)

```cypher
// Create named graph for graph algorithms
CALL gds.graph.project('actor-graph', 'Actor', {
  TRANSACTED_WITH: { orientation: 'UNDIRECTED' },
  POSTED_ON: { orientation: 'NATURAL' }
})
```

---

## 4. Redis Caching Schema

Redis is used for **caching**, **rate limiting**, **session management**, and **task queues**.

### 4.1 Key Patterns

| Key Pattern | Type | TTL | Purpose |
|---|---|---|---|
| `cache:alert:{alert_id}` | String | 5 min | Alert detail cache |
| `cache:dashboard:summary` | Hash | 1 min | Dashboard summary data |
| `cache:search:{query_hash}` | String | 2 min | Search result cache |
| `cache:translation:{hash}` | String | 30 days | Translated text cache |
| `rate:user:{user_id}` | Sorted Set | 1 min | Per-user rate limiting |
| `rate:ip:{ip}` | Sorted Set | 1 min | Per-IP rate limiting |
| `session:{session_id}` | Hash | 24 hours | User session data |
| `queue:crawl:{target_id}` | List | — | Crawl job queue |
| `dedup:alert:{rule_id}:{content_id}` | String | 24 hours | Alert deduplication |
| `lock:crawl:{target_id}` | String | 10 min | Crawl job lock (prevent duplicate) |
| `config:{key}` | String | 1 hour | System config cache |

### 4.2 Rate Limiting Lua Script

```lua
-- Sliding window rate limiter
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)

if count >= limit then
  return 0  -- Rate limited
end

redis.call('ZADD', key, now, now)
redis.call('EXPIRE', key, window)
return 1  -- Allowed
```

---

## 5. Data Lifecycle Summary

| Data | Primary Store | Search Index | Graph | Cache | Retention |
|---|---|---|---|---|---|
| Raw crawled content | MongoDB | — | — | — | 90 days |
| Parsed content | — | Elasticsearch | Neo4j | — | 180 days |
| Analysis results | — | Elasticsearch | — | — | 180 days |
| Alerts | MongoDB | Elasticsearch | — | Redis | 1 year |
| Actor profiles | — | Elasticsearch | Neo4j | — | Indefinite |
| Users | MongoDB | — | — | — | Until deletion |
| Watchlists | MongoDB | — | — | — | Indefinite |
| Audit logs | MongoDB | Elasticsearch | — | — | 7 years |
| Reports | MinIO/S3 | — | — | — | 5 years |
| Crawl queues | — | — | — | Redis | Ephemeral |
| Sessions | — | — | — | Redis | 24 hours |

---

*Document maintained by the Architecture Team.*
