# DarkTrace — API Contract

> **Version:** 1.0  
> **Date:** 2026-06-03  
> **Base URL:** `https://api.darktrace.local/v1`  
> **Protocol:** HTTPS only  
> **Auth:** JWT Bearer Token or API Key  
> **Content-Type:** `application/json`

---

## 1. Authentication

### 1.1 Login

```
POST /auth/login
```

**Request:**
```json
{
  "email": "investigator@police.gov.in",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "investigator@police.gov.in",
    "name": "Inspector Sharma",
    "role": "investigator",
    "permissions": ["alerts:read", "search:read", "reports:create"]
  }
}
```

### 1.2 Refresh Token

```
POST /auth/refresh
```

**Request:**
```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 900
}
```

### 1.3 Logout

```
POST /auth/logout
```

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

### 1.4 API Key Authentication

For SIEM integrations and automated clients:

```
GET /api/v1/alerts
Headers: X-API-Key: <api_key>
```

API keys are managed via the admin panel.

---

## 2. Alerts

### 2.1 List Alerts

```
GET /alerts
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 25 | Items per page (max 100) |
| `severity` | string | No | — | Filter: `info`, `low`, `medium`, `high`, `critical` |
| `status` | string | No | — | Filter: `new`, `acknowledged`, `investigating`, `resolved`, `false_positive` |
| `category` | string | No | — | Filter: `ransomware`, `data_breach`, `exploit`, `fraud`, `illegal_goods`, `intelligence` |
| `source_type` | string | No | — | Filter: `onion`, `i2p`, `surface` |
| `date_from` | ISO datetime | No | — | Start date for alert creation |
| `date_to` | ISO datetime | No | — | End date for alert creation |
| `q` | string | No | — | Full-text search query |
| `sort_by` | string | No | `created_at` | `created_at`, `severity`, `score` |
| `sort_order` | string | No | `desc` | `asc`, `desc` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "alert-uuid",
      "title": "Ransomware listing mentions critical infrastructure",
      "severity": "high",
      "score": 780,
      "status": "new",
      "category": "ransomware",
      "source_type": "onion",
      "source_url": "http://xyz.onion/listing/456",
      "created_at": "2026-06-03T12:00:00Z",
      "acknowledged_by": null,
      "summary": "Listing on ExampleMarket selling 'LockBit v4' targeting healthcare sector",
      "matched_keywords": ["hospital", "ransomware", "critical infrastructure"],
      "actor_pseudonym": "dark_hand",
      "actor_profile_id": "actor-uuid"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 142,
    "total_pages": 6
  }
}
```

### 2.2 Get Alert Detail

```
GET /alerts/{alert_id}
```

**Response (200):**
```json
{
  "id": "alert-uuid",
  "title": "Ransomware listing mentions critical infrastructure",
  "severity": "high",
  "score": 780,
  "score_breakdown": {
    "threat_classification": { "score": 240, "weight": 0.3 },
    "high_value_targets": { "score": 150, "weight": 0.2 },
    "actor_reputation": { "score": 120, "weight": 0.15 },
    "freshness": { "score": 80, "weight": 0.1 },
    "sentiment": { "score": 70, "weight": 0.1 },
    "keyword_matches": { "score": 80, "weight": 0.1 },
    "site_reputation": { "score": 40, "weight": 0.05 }
  },
  "status": "new",
  "assignee": null,
  "category": "ransomware",
  "source": {
    "url": "http://xyz.onion/listing/456",
    "site_name": "ExampleMarket",
    "source_type": "onion",
    "crawl_timestamp": "2026-06-03T12:00:00Z"
  },
  "content": {
    "title": "LockBit v4 - Full Package",
    "author": "dark_hand",
    "author_profile_url": "http://xyz.onion/user/dark_hand",
    "published_date": "2026-06-02",
    "content_text": "Selling LockBit v4 source code... targeting hospital infrastructure...",
    "language": "en",
    "translated_from": null
  },
  "entities": {
    "persons": ["dark_hand"],
    "organizations": [],
    "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
    "emails": ["darkhand@protonmail.com"],
    "keywords_matched": ["hospital", "ransomware", "critical infrastructure", "healthcare"]
  },
  "analysis": {
    "sentiment": {
      "threat_intent": 0.92,
      "hostility": 0.78,
      "urgency": 0.65
    },
    "classification": {
      "primary": "ransomware",
      "secondary": ["malware", "data_breach"],
      "confidence": 0.94
    }
  },
  "actor": {
    "profile_id": "actor-uuid",
    "pseudonyms": ["dark_hand", "dark_hand_99", "dh_seller"],
    "risk_score": 820,
    "first_seen": "2025-11-15T00:00:00Z",
    "last_seen": "2026-06-03T12:00:00Z",
    "total_posts": 47,
    "active_marketplaces": ["ExampleMarket", "DarkHub"]
  },
  "timeline": [
    { "event": "crawled", "timestamp": "2026-06-03T12:00:00Z", "detail": "Page fetched via Tor" },
    { "event": "parsed", "timestamp": "2026-06-03T12:00:01Z", "detail": "Marketplace listing extracted" },
    { "event": "analyzed", "timestamp": "2026-06-03T12:00:03Z", "detail": "NLP classification: ransomware" },
    { "event": "scored", "timestamp": "2026-06-03T12:00:04Z", "detail": "Score: 780 (High)" },
    { "event": "alerted", "timestamp": "2026-06-03T12:00:05Z", "detail": "Rule 'Ransomware Alert' matched" }
  ],
  "related_alerts": [
    { "id": "alert-uuid-2", "title": "Same actor listing exploit kit", "severity": "medium", "created_at": "2026-06-02T08:00:00Z" }
  ],
  "created_at": "2026-06-03T12:00:05Z",
  "updated_at": "2026-06-03T12:00:05Z"
}
```

### 2.3 Update Alert Status

```
PATCH /alerts/{alert_id}
```

**Request:**
```json
{
  "status": "investigating",
  "assignee": "user-uuid",
  "comment": "Investigating the actor's other listings"
}
```

**Response (200):**
```json
{
  "id": "alert-uuid",
  "status": "investigating",
  "assignee": "user-uuid",
  "updated_at": "2026-06-03T14:00:00Z"
}
```

### 2.4 Bulk Alert Update

```
POST /alerts/bulk
```

**Request:**
```json
{
  "alert_ids": ["alert-uuid-1", "alert-uuid-2"],
  "action": "acknowledge",
  "assignee": "user-uuid"
}
```

**Response (200):**
```json
{
  "updated_count": 2,
  "message": "2 alerts acknowledged"
}
```

### 2.5 Get Alert Statistics

```
GET /alerts/stats
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `date_from` | ISO datetime | No | 7 days ago | Start date |
| `date_to` | ISO datetime | No | now | End date |
| `granularity` | string | No | `day` | `hour`, `day`, `week`, `month` |

**Response (200):**
```json
{
  "total": 142,
  "by_severity": {
    "critical": 12,
    "high": 38,
    "medium": 52,
    "low": 30,
    "info": 10
  },
  "by_category": {
    "ransomware": 35,
    "data_breach": 28,
    "exploit": 22,
    "fraud": 30,
    "illegal_goods": 18,
    "intelligence": 9
  },
  "by_status": {
    "new": 85,
    "acknowledged": 30,
    "investigating": 20,
    "resolved": 5,
    "false_positive": 2
  },
  "trend": [
    { "date": "2026-05-28", "count": 18, "critical": 2, "high": 5 },
    { "date": "2026-05-29", "count": 22, "critical": 3, "high": 6 },
    { "date": "2026-05-30", "count": 15, "critical": 1, "high": 4 },
    { "date": "2026-05-31", "count": 20, "critical": 2, "high": 5 },
    { "date": "2026-06-01", "count": 25, "critical": 2, "high": 8 },
    { "date": "2026-06-02", "count": 28, "critical": 1, "high": 7 },
    { "date": "2026-06-03", "count": 14, "critical": 1, "high": 3 }
  ]
}
```

---

## 3. Search

### 3.1 Full-Text Search

```
GET /search
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `q` | string | Yes | — | Search query (Elasticsearch query string syntax) |
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 25 | Items per page (max 100) |
| `source_type` | string | No | — | `onion`, `i2p`, `surface` |
| `category` | string | No | — | Threat category filter |
| `language` | string | No | — | Language filter |
| `author` | string | No | — | Author/pseudonym filter |
| `date_from` | ISO datetime | No | — | Start date |
| `date_to` | ISO datetime | No | — | End date |
| `has_entities` | string | No | — | `btc`, `email`, `phone` |
| `sort_by` | string | No | `relevance` | `relevance`, `date`, `score` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "content-uuid",
      "url": "http://xyz.onion/listing/456",
      "title": "LockBit v4 - Full Package",
      "snippet": "...selling <em>LockBit</em> v4 source code targeting <em>hospital</em> infrastructure...",
      "author": "dark_hand",
      "source_type": "onion",
      "site_name": "ExampleMarket",
      "category": "ransomware",
      "severity_score": 780,
      "language": "en",
      "crawled_at": "2026-06-03T12:00:00Z",
      "matched_entities": {
        "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
        "emails": ["darkhand@protonmail.com"]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 89,
    "total_pages": 4
  },
  "facets": {
    "categories": [
      { "value": "ransomware", "count": 35 },
      { "value": "data_breach", "count": 22 }
    ],
    "source_types": [
      { "value": "onion", "count": 78 },
      { "value": "i2p", "count": 11 }
    ],
    "languages": [
      { "value": "en", "count": 60 },
      { "value": "ru", "count": 18 },
      { "value": "hi", "count": 6 },
      { "value": "ar", "count": 5 }
    ]
  }
}
```

### 3.2 Saved Searches

```
POST /search/saved
```

**Request:**
```json
{
  "name": "Ransomware monitoring",
  "query": "ransomware OR lockbit OR blackcat",
  "filters": {
    "severity": ["high", "critical"],
    "source_type": ["onion"]
  },
  "notify_on_new": true
}
```

**Response (201):**
```json
{
  "id": "saved-search-uuid",
  "name": "Ransomware monitoring",
  "created_at": "2026-06-03T12:00:00Z"
}
```

---

## 4. Crawler Management

### 4.1 List Crawl Targets

```
GET /crawler/targets
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "target-uuid",
      "url": "http://xyz.onion",
      "site_name": "ExampleMarket",
      "source_type": "onion",
      "status": "active",
      "crawl_frequency": "every_6h",
      "last_crawled": "2026-06-03T11:00:00Z",
      "last_status": "success",
      "pages_crawled": 1520,
      "added_by": "admin-uuid",
      "added_at": "2026-05-01T00:00:00Z"
    }
  ]
}
```

### 4.2 Add Crawl Target

```
POST /crawler/targets
```

**Request:**
```json
{
  "url": "http://new-market.onion",
  "site_name": "NewMarket",
  "source_type": "onion",
  "crawl_frequency": "every_12h",
  "parser_type": "marketplace",
  "notes": "New marketplace discovered via forum chatter"
}
```

**Response (201):**
```json
{
  "id": "target-uuid",
  "url": "http://new-market.onion",
  "status": "pending_verification",
  "created_at": "2026-06-03T12:00:00Z"
}
```

### 4.3 Trigger Immediate Crawl

```
POST /crawler/targets/{target_id}/crawl
```

**Response (202):**
```json
{
  "job_id": "crawl-job-uuid",
  "status": "queued",
  "estimated_completion": "2026-06-03T12:05:00Z"
}
```

### 4.4 Get Crawl Job Status

```
GET /crawler/jobs/{job_id}
```

**Response (200):**
```json
{
  "id": "crawl-job-uuid",
  "target_id": "target-uuid",
  "target_url": "http://xyz.onion",
  "status": "in_progress",
  "pages_fetched": 45,
  "pages_total": 120,
  "errors": 2,
  "started_at": "2026-06-03T12:00:00Z",
  "completed_at": null,
  "proxy_used": "tor_exit_12"
}
```

### 4.5 List Crawl Jobs

```
GET /crawler/jobs
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `status` | string | No | — | `queued`, `in_progress`, `completed`, `failed` |
| `target_id` | string | No | — | Filter by target |
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 25 | Items per page |

**Response (200):**
```json
{
  "data": [
    {
      "id": "crawl-job-uuid",
      "target_url": "http://xyz.onion",
      "status": "completed",
      "started_at": "2026-06-03T06:00:00Z",
      "completed_at": "2026-06-03T06:15:00Z",
      "pages_fetched": 120,
      "pages_total": 120,
      "errors": 0
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 340,
    "total_pages": 14
  }
}
```

---

## 5. Watchlists

### 5.1 List Watchlists

```
GET /watchlists
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "watchlist-uuid",
      "name": "Critical Infrastructure Keywords",
      "description": "Keywords related to critical infrastructure targeting",
      "keywords": ["hospital", "power grid", "government", "dam", "nuclear"],
      "regex_patterns": [],
      "severity_boost": 200,
      "is_active": true,
      "created_by": "user-uuid",
      "created_at": "2026-05-15T00:00:00Z",
      "match_count": 34
    }
  ]
}
```

### 5.2 Create Watchlist

```
POST /watchlists
```

**Request:**
```json
{
  "name": "Indian PII Monitoring",
  "description": "Monitor for Indian PII data leaks",
  "keywords": ["Aadhaar", "PAN card", "Indian passport", "Voter ID"],
  "regex_patterns": [
    {"pattern": "\\d{4}\\s\\d{4}\\s\\d{4}", "label": "Aadhaar"},
    {"pattern": "[A-Z]{5}\\d{4}[A-Z]", "label": "PAN"}
  ],
  "severity_boost": 150,
  "is_active": true
}
```

**Response (201):**
```json
{
  "id": "watchlist-uuid",
  "name": "Indian PII Monitoring",
  "created_at": "2026-06-03T12:00:00Z"
}
```

### 5.3 Update Watchlist

```
PUT /watchlists/{watchlist_id}
```

**Request:**
```json
{
  "keywords": ["Aadhaar", "PAN card", "Indian passport", "Voter ID", "Driving License"],
  "is_active": true
}
```

**Response (200):**
```json
{
  "id": "watchlist-uuid",
  "updated_at": "2026-06-03T14:00:00Z"
}
```

### 5.4 Delete Watchlist

```
DELETE /watchlists/{watchlist_id}
```

**Response (204):** No Content

---

## 6. Alert Rules

### 6.1 List Alert Rules

```
GET /alert-rules
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "rule-uuid",
      "name": "Ransomware Alert",
      "description": "Alert on ransomware listings mentioning critical infrastructure",
      "enabled": true,
      "severity_threshold": 600,
      "conditions": [
        {"field": "threat_classification", "operator": "in", "value": ["ransomware", "data_breach"]},
        {"field": "entities.keywords_matched", "operator": "contains_any", "value": ["hospital", "power grid", "government"]}
      ],
      "notifications": [
        {"type": "email", "target": "team@police.gov.in"},
        {"type": "webhook", "target": "https://siem.citypolice.gov.in/webhook"}
      ],
      "created_by": "admin-uuid",
      "created_at": "2026-05-10T00:00:00Z",
      "triggered_count": 28
    }
  ]
}
```

### 6.2 Create Alert Rule

```
POST /alert-rules
```

**Request:**
```json
{
  "name": "Exploit Kit Monitoring",
  "description": "Alert on exploit kit listings",
  "enabled": true,
  "severity_threshold": 400,
  "conditions": [
    {"field": "threat_classification", "operator": "in", "value": ["exploit", "malware"]},
    {"field": "source_type", "operator": "in", "value": ["onion", "i2p"]}
  ],
  "notifications": [
    {"type": "dashboard_alert"},
    {"type": "email", "target": "analyst@police.gov.in"}
  ]
}
```

**Response (201):**
```json
{
  "id": "rule-uuid",
  "name": "Exploit Kit Monitoring",
  "created_at": "2026-06-03T12:00:00Z"
}
```

---

## 7. Actor Profiles

### 7.1 List Actors

```
GET /actors
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 25 | Items per page |
| `risk_score_min` | integer | No | — | Minimum risk score |
| `q` | string | No | — | Search by pseudonym |
| `sort_by` | string | No | `risk_score` | `risk_score`, `last_seen`, `total_posts` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "actor-uuid",
      "pseudonyms": ["dark_hand", "dark_hand_99", "dh_seller"],
      "risk_score": 820,
      "first_seen": "2025-11-15T00:00:00Z",
      "last_seen": "2026-06-03T12:00:00Z",
      "total_posts": 47,
      "active_platforms": ["ExampleMarket", "DarkHub"],
      "linked_entities": {
        "btc_addresses": 3,
        "emails": 2,
        "pgp_keys": 1
      },
      "top_categories": ["ransomware", "exploit"]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 312,
    "total_pages": 13
  }
}
```

### 7.2 Get Actor Detail

```
GET /actors/{actor_id}
```

**Response (200):**
```json
{
  "id": "actor-uuid",
  "pseudonyms": [
    {"name": "dark_hand", "platforms": ["ExampleMarket"], "first_seen": "2025-11-15", "last_seen": "2026-06-03"},
    {"name": "dark_hand_99", "platforms": ["DarkHub"], "first_seen": "2026-01-20", "last_seen": "2026-05-28"},
    {"name": "dh_seller", "platforms": ["ExampleMarket"], "first_seen": "2026-03-01", "last_seen": "2026-06-01"}
  ],
  "risk_score": 820,
  "risk_factors": [
    "Sells ransomware",
    "Mentions critical infrastructure",
    "High posting frequency",
    "Uses multiple pseudonyms"
  ],
  "first_seen": "2025-11-15T00:00:00Z",
  "last_seen": "2026-06-03T12:00:00Z",
  "total_posts": 47,
  "active_platforms": ["ExampleMarket", "DarkHub"],
  "linked_entities": {
    "btc_addresses": [
      {"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "first_seen": "2025-11-15", "total_received_btc": 12.5}
    ],
    "emails": ["darkhand@protonmail.com", "seller@tutanota.com"],
    "pgp_keys": ["0xDEADBEEF"]
  },
  "activity_timeline": [
    {"date": "2025-11", "posts": 5, "categories": ["exploit"]},
    {"date": "2025-12", "posts": 8, "categories": ["ransomware", "exploit"]},
    {"date": "2026-01", "posts": 10, "categories": ["ransomware"]},
    {"date": "2026-02", "posts": 7, "categories": ["ransomware", "data_breach"]},
    {"date": "2026-03", "posts": 6, "categories": ["ransomware"]},
    {"date": "2026-04", "posts": 5, "categories": ["ransomware", "exploit"]},
    {"date": "2026-05", "posts": 4, "categories": ["ransomware"]},
    {"date": "2026-06", "posts": 2, "categories": ["ransomware"]}
  ],
  "recent_activity": [
    {
      "content_id": "content-uuid",
      "url": "http://xyz.onion/listing/456",
      "title": "LockBit v4 - Full Package",
      "category": "ransomware",
      "crawled_at": "2026-06-03T12:00:00Z"
    }
  ],
  "network_graph": {
    "nodes": [
      {"id": "actor-uuid", "label": "dark_hand", "type": "actor", "risk_score": 820},
      {"id": "actor-uuid-2", "label": "vendor_king", "type": "actor", "risk_score": 650},
      {"id": "site-uuid", "label": "ExampleMarket", "type": "site"}
    ],
    "edges": [
      {"source": "actor-uuid", "target": "site-uuid", "label": "POSTED_ON"},
      {"source": "actor-uuid", "target": "actor-uuid-2", "label": "TRANSACTED_WITH", "count": 5}
    ]
  }
}
```

### 7.3 Actor Search

```
GET /actors/search?q=dark_hand
```

**Response (200):** Same format as List Actors, filtered by pseudonym match.

---

## 8. Reports

### 8.1 Generate Report

```
POST /reports
```

**Request:**
```json
{
  "type": "alert_report",
  "format": "pdf",
  "parameters": {
    "alert_id": "alert-uuid",
    "include_evidence": true,
    "include_blockchain_seal": false
  }
}
```

Types:
- `alert_report` — Detailed alert report
- `actor_dossier` — Complete actor profile
- `trend_report` — Aggregated statistics
- `raw_export` — Bulk data export

**Response (202):**
```json
{
  "report_id": "report-uuid",
  "status": "generating",
  "estimated_completion": "2026-06-03T12:00:30Z"
}
```

### 8.2 Get Report Status

```
GET /reports/{report_id}
```

**Response (200):**
```json
{
  "id": "report-uuid",
  "type": "alert_report",
  "format": "pdf",
  "status": "completed",
  "file_size_bytes": 245000,
  "download_url": "https://api.darktrace.local/v1/reports/report-uuid/download?token=temp-token",
  "url_expires_at": "2026-06-03T13:00:00Z",
  "created_at": "2026-06-03T12:00:00Z",
  "blockchain_tx": null
}
```

### 8.3 List Reports

```
GET /reports
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 25 | Items per page |
| `type` | string | No | — | Filter: `alert_report`, `actor_dossier`, `trend_report`, `raw_export` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "report-uuid",
      "type": "alert_report",
      "format": "pdf",
      "status": "completed",
      "file_size_bytes": 245000,
      "created_at": "2026-06-03T12:00:00Z",
      "expires_at": "2026-12-31T00:00:00Z"
    }
  ],
  "pagination": { "page": 1, "per_page": 25, "total": 45, "total_pages": 2 }
}
```

---

## 9. Dashboard / Statistics

### 9.1 Dashboard Summary

```
GET /dashboard/summary
```

**Response (200):**
```json
{
  "active_alerts": {
    "total": 142,
    "critical": 12,
    "high": 38,
    "medium": 52,
    "low": 30,
    "info": 10,
    "trend": "+12%"  // compared to last 24h
  },
  "crawler_status": {
    "active_targets": 25,
    "queued_jobs": 3,
    "running_jobs": 2,
    "pages_today": 1520,
    "success_rate": "98.5%"
  },
  "actors": {
    "total_tracked": 312,
    "high_risk": 45,
    "new_today": 3
  },
  "recent_alerts": [
    {
      "id": "alert-uuid",
      "title": "Ransomware listing mentions critical infrastructure",
      "severity": "critical",
      "created_at": "2026-06-03T12:00:00Z",
      "source_type": "onion"
    }
  ],
  "top_categories": [
    {"category": "ransomware", "count": 35, "trend": "+15%"},
    {"category": "fraud", "count": 30, "trend": "+5%"},
    {"category": "data_breach", "count": 28, "trend": "-8%"}
  ]
}
```

### 9.2 Trending Data

```
GET /dashboard/trending
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `days` | integer | No | 7 | Lookback period |

**Response (200):**
```json
{
  "most_mentioned_products": [
    {"product": "LockBit", "mentions": 45, "trend": "+20%"},
    {"product": "BlackCat", "mentions": 32, "trend": "+5%"},
    {"product": "Cobalt Strike", "mentions": 28, "trend": "-10%"}
  ],
  "most_active_marketplaces": [
    {"site": "ExampleMarket", "posts": 520, "trend": "+8%"},
    {"site": "DarkHub", "posts": 380, "trend": "+12%"}
  ],
  "top_threat_actors": [
    {"pseudonym": "dark_hand", "risk_score": 820, "recent_posts": 5},
    {"pseudonym": "shadow_vendor", "risk_score": 790, "recent_posts": 3}
  ],
  "language_distribution": [
    {"language": "en", "percentage": 55.0},
    {"language": "ru", "percentage": 25.0},
    {"language": "ar", "percentage": 10.0},
    {"language": "hi", "percentage": 5.0},
    {"language": "other", "percentage": 5.0}
  ]
}
```

---

## 10. Admin / Configuration

### 10.1 List Users

```
GET /admin/users
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "user-uuid",
      "email": "investigator@police.gov.in",
      "name": "Inspector Sharma",
      "role": "investigator",
      "is_active": true,
      "last_login": "2026-06-03T08:00:00Z",
      "created_at": "2026-04-01T00:00:00Z"
    }
  ]
}
```

### 10.2 Create User

```
POST /admin/users
```

**Request:**
```json
{
  "email": "new.analyst@police.gov.in",
  "name": "Analyst Kumar",
  "password": "temporary-password",
  "role": "investigator"
}
```

**Response (201):**
```json
{
  "id": "user-uuid",
  "email": "new.analyst@police.gov.in",
  "created_at": "2026-06-03T12:00:00Z"
}
```

### 10.3 Get Audit Logs

```
GET /admin/audit-logs
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 50 | Items per page |
| `user_id` | string | No | — | Filter by user |
| `action` | string | No | — | Filter: `login`, `alert_update`, `report_generated`, `target_added`, `user_created` |
| `date_from` | ISO datetime | No | — | Start date |
| `date_to` | ISO datetime | No | — | End date |

**Response (200):**
```json
{
  "data": [
    {
      "id": "log-uuid",
      "timestamp": "2026-06-03T12:00:00Z",
      "user_id": "user-uuid",
      "user_name": "Inspector Sharma",
      "action": "alert_update",
      "resource_type": "alert",
      "resource_id": "alert-uuid",
      "details": "Status changed to investigating",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "pagination": { "page": 1, "per_page": 50, "total": 1520, "total_pages": 31 }
}
```

### 10.4 System Health

```
GET /admin/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "services": {
    "api_gateway": { "status": "up", "uptime": "12d 4h 32m" },
    "crawler": { "status": "up", "workers": 4, "queue_depth": 12 },
    "parser": { "status": "up", "throughput": "120 docs/min" },
    "nlp_engine": { "status": "degraded", "message": "GPU memory at 85%" },
    "scoring": { "status": "up" },
    "alert_engine": { "status": "up" },
    "elasticsearch": { "status": "up", "health": "green" },
    "mongodb": { "status": "up", "health": "healthy" },
    "neo4j": { "status": "up" },
    "rabbitmq": { "status": "up", "queues": 24 }
  }
}
```

---

## 11. WebSocket Events

### 11.1 Live Alert Stream

```
WebSocket: wss://api.darktrace.local/v1/ws/alerts
Auth: Token in query string (wss://...?token=<jwt>)
```

**Server → Client Events:**

```json
{
  "type": "alert.new",
  "data": {
    "id": "alert-uuid",
    "title": "New ransomware listing detected",
    "severity": "critical",
    "category": "ransomware",
    "source_type": "onion",
    "created_at": "2026-06-03T12:00:05Z"
  }
}
```

```json
{
  "type": "alert.updated",
  "data": {
    "id": "alert-uuid",
    "status": "investigating",
    "assignee": "user-uuid",
    "updated_at": "2026-06-03T14:00:00Z"
  }
}
```

### 11.2 Crawl Progress Stream

```
WebSocket: wss://api.darktrace.local/v1/ws/crawler
```

```json
{
  "type": "crawl.progress",
  "data": {
    "job_id": "crawl-job-uuid",
    "target_url": "http://xyz.onion",
    "pages_fetched": 45,
    "pages_total": 120,
    "status": "in_progress"
  }
}
```

---

## 12. SIEM Integration Endpoints

### 12.1 SIEM Webhook Registration

```
POST /integrations/siem
```

**Request:**
```json
{
  "name": "City Police SIEM",
  "type": "webhook",
  "endpoint": "https://siem.citypolice.gov.in/webhook/darktrace",
  "format": "cef",
  "auth_type": "api_key",
  "api_key": "siem-api-key",
  "severity_filter": ["high", "critical"],
  "categories_filter": ["ransomware", "data_breach", "exploit"],
  "is_active": true
}
```

**Response (201):**
```json
{
  "id": "integration-uuid",
  "created_at": "2026-06-03T12:00:00Z"
}
```

### 12.2 Syslog Alternative

For SIEMs that support Syslog:

```
Syslog Server: udp://api.darktrace.local:514
Format: CEF (Common Event Format)

Example CEF Message:
CEF:0|DarkTrace|ThreatIntelligence|1.0|100|Ransomware Alert|10|dvc=10.0.0.1 start=Jun 03 2026 12:00:00 msg=LockBit v4 listing targeting hospitals src=xyz.onion suser=dark_hnd cs1Label=category cs1=ransomware cs2Label=score cs2=780 cs3Label=sourceType cs3=onion
```

---

## 13. Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "severity",
        "message": "Must be one of: info, low, medium, high, critical"
      }
    ],
    "request_id": "req-uuid",
    "timestamp": "2026-06-03T12:00:00Z"
  }
}
```

### Common HTTP Status Codes

| Code | Description |
|---|---|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation) |
| 204 | No Content (deletion success) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate resource) |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

*Document maintained by the Architecture Team.*
