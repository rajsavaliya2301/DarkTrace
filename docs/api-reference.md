# DarkTrace — API Reference

> **Version:** 1.0 | **Base URL:** `http://localhost:8000/v1` | **OpenAPI:** `/docs`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Alerts](#2-alerts)
3. [Alert Rules](#3-alert-rules)
4. [Watchlists](#4-watchlists)
5. [Actors](#5-actors)
6. [Crawler](#6-crawler)
7. [Reports](#7-reports)
8. [Dashboard](#8-dashboard)
9. [Search](#9-search)
10. [Admin](#10-admin)
11. [SIEM Export](#11-siem-export)
12. [Error Responses](#12-error-responses)

---

## 1. Authentication

All API endpoints (except login) require a Bearer JWT token in the `Authorization` header.

### POST `/auth/login`

Authenticate with email and password.

**Request:**
```json
{
  "email": "admin@darktrace.local",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "usr_abc123",
    "email": "admin@darktrace.local",
    "name": "Admin",
    "role": "admin",
    "permissions": ["*"]
  }
}
```

### POST `/auth/refresh`

Refresh an expired access token using a valid refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### POST `/auth/logout`

Invalidate the current refresh token.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## 2. Alerts

### GET `/alerts`

List alerts with pagination and filtering.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 25 | Items per page (max 100) |
| `severity` | string | — | Filter: `critical`, `high`, `medium`, `low` |
| `status` | string | — | Filter: `new`, `investigating`, `resolved`, `false_positive` |
| `category` | string | — | Filter by category |
| `q` | string | — | Search query |
| `sort_by` | string | `created_at` | `created_at`, `score`, `severity` |
| `sort_order` | string | `desc` | `asc` or `desc` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "alt_abc123",
      "title": "Ransomware listing detected on DarkMarket",
      "severity": "high",
      "score": 750,
      "status": "new",
      "category": "ransomware",
      "source_url": "http://darkmarket.onion/listing/123",
      "source_type": "onion",
      "summary": "Ransomware listing targeting hospitals detected",
      "matched_keywords": ["ransomware", "lockbit"],
      "created_at": "2026-06-03T10:30:00Z"
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

### GET `/alerts/stats`

Get alert statistics for dashboard.

**Response (200):**
```json
{
  "total": 142,
  "by_severity": {
    "critical": 12,
    "high": 45,
    "medium": 58,
    "low": 27
  },
  "by_status": {
    "new": 67,
    "investigating": 38,
    "resolved": 25,
    "false_positive": 12
  },
  "by_category": {
    "ransomware": 42,
    "data_breach": 31,
    "financial_fraud": 28,
    "drugs": 18,
    "hacking_services": 15,
    "other": 8
  },
  "trending": [
    {"date": "2026-06-01", "count": 18},
    {"date": "2026-06-02", "count": 24},
    {"date": "2026-06-03", "count": 31}
  ]
}
```

### GET `/alerts/{alert_id}`

Get a single alert with full details.

**Response (200):**
```json
{
  "id": "alt_abc123",
  "title": "Ransomware listing detected on DarkMarket",
  "severity": "high",
  "score": 750,
  "status": "new",
  "category": "ransomware",
  "source_url": "http://darkmarket.onion/listing/123",
  "source_type": "onion",
  "content_snippet": "Fresh ransomware builder available...",
  "summary": "Ransomware listing targeting hospitals detected",
  "matched_keywords": ["ransomware", "lockbit"],
  "matched_patterns": [
    {"pattern": "\\b[A-Z]{5}\\d{4}[A-Z]\\b", "label": "PAN", "matches": ["ABCD1234E"]}
  ],
  "extracted_entities": {
    "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
    "emails": ["seller@protonmail.com"],
    "drugs": []
  },
  "threat_score_breakdown": {
    "classification": 250,
    "high_value_target": 200,
    "actor_reputation": 100,
    "freshness": 80,
    "sentiment": 70,
    "keyword_match": 50,
    "site_reputation": 0
  },
  "assigned_to": null,
  "notes": [],
  "created_at": "2026-06-03T10:30:00Z",
  "updated_at": "2026-06-03T10:30:00Z"
}
```

### PATCH `/alerts/{alert_id}`

Update alert status or assignment.

**Request:**
```json
{
  "status": "investigating",
  "assigned_to": "usr_xyz789",
  "notes": "Investigating the ransomware builder URL"
}
```

**Response (200):**
```json
{
  "id": "alt_abc123",
  "status": "investigating",
  "assigned_to": "usr_xyz789",
  "updated_at": "2026-06-03T11:00:00Z"
}
```

### POST `/alerts/bulk`

Bulk update alerts.

**Request:**
```json
{
  "alert_ids": ["alt_abc123", "alt_def456"],
  "action": "resolve",
  "status": "resolved",
  "notes": "False positives - no active threat"
}
```

**Response (200):**
```json
{
  "updated_count": 2,
  "message": "2 alerts updated successfully"
}
```

---

## 3. Alert Rules

### GET `/alert-rules`

List all alert rules.

**Response (200):**
```json
{
  "data": [
    {
      "id": "rule_abc123",
      "name": "Ransomware Keyword Alert",
      "description": "Alert on high-severity ransomware keywords",
      "conditions": {
        "min_score": 600,
        "categories": ["ransomware"],
        "keywords": ["lockbit", "blackcat", "ransomware"]
      },
      "actions": {
        "email": ["analyst@police.gov.in"],
        "webhook": "https://hooks.siem.gov/alert",
        "syslog": true
      },
      "is_active": true,
      "created_at": "2026-06-01T00:00:00Z"
    }
  ]
}
```

### POST `/alert-rules`

Create a new alert rule.

**Request:**
```json
{
  "name": "Critical Data Leak Alert",
  "description": "Alert on data breach mentions with high score",
  "conditions": {
    "min_score": 700,
    "categories": ["data_breach"],
    "severity": ["critical", "high"]
  },
  "actions": {
    "email": ["lead-investigator@police.gov.in"],
    "webhook": "https://hooks.siem.gov/alert"
  }
}
```

**Response (201):** Created rule object with `id`.

### PUT `/alert-rules/{rule_id}`

Update an alert rule.

### DELETE `/alert-rules/{rule_id}`

Delete an alert rule.

**Response (204):** No content.

---

## 4. Watchlists

### GET `/watchlists`

List all watchlists.

### POST `/watchlists`

Create a new watchlist.

**Request:**
```json
{
  "name": "Ransomware Watchlist",
  "description": "Track ransomware-related keywords and patterns",
  "keywords": ["ransomware", "lockbit", "blackcat", "alphv"],
  "regex_patterns": [
    {
      "pattern": "\\b[A-Z]{5}\\d{4}[A-Z]\\b",
      "label": "PAN (Payment Card Number)"
    }
  ],
  "entities": ["btc_addresses", "emails"],
  "severity_boost": 200,
  "is_active": true
}
```

**Response (201):**
```json
{
  "id": "wl_abc123",
  "name": "Ransomware Watchlist",
  "keywords": ["ransomware", "lockbit", "blackcat", "alphv"],
  "regex_patterns": [
    {"pattern": "\\b[A-Z]{5}\\d{4}[A-Z]\\b", "label": "PAN (Payment Card Number)"}
  ],
  "entities": ["btc_addresses", "emails"],
  "severity_boost": 200,
  "is_active": true,
  "created_by": "usr_abc123",
  "created_at": "2026-06-03T10:30:00Z",
  "updated_at": "2026-06-03T10:30:00Z"
}
```

### GET `/watchlists/{watchlist_id}`

Get watchlist details.

### PUT `/watchlists/{watchlist_id}`

Update a watchlist.

### DELETE `/watchlists/{watchlist_id}`

Delete a watchlist.

**Response (204):** No content.

---

## 5. Actors

### GET `/actors`

List threat actors with pagination.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 25 | Items per page |
| `q` | string | — | Search by pseudonym |
| `risk_score_min` | int | 0 | Minimum risk score filter |
| `sort_by` | string | `risk_score` | Sort field |

**Response (200):**
```json
{
  "data": [
    {
      "id": "act_abc123",
      "pseudonyms": ["dark_hacker", "ghost"],
      "risk_score": 850,
      "total_posts": 142,
      "first_seen": "2026-01-15T00:00:00Z",
      "last_seen": "2026-06-02T15:30:00Z",
      "active_platforms": ["DarkMarket", "AlphaBay"],
      "top_categories": ["ransomware", "exploit"],
      "linked_entities": {
        "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
        "emails": ["dark@protonmail.com"]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 45,
    "total_pages": 2
  }
}
```

### GET `/actors/search`

Search actors by pseudonym.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | — | Search query (required) |
| `risk_score_min` | int | 0 | Minimum risk score |
| `page` | int | 1 | Page number |
| `per_page` | int | 25 | Items per page |

### GET `/actors/{actor_id}`

Get detailed actor profile including pseudonyms, platform activity, and risk factors.

### GET `/actors/{actor_id}/graph`

Get actor network graph data for visualization (compatible with Cytoscape.js).

**Response (200):**
```json
{
  "nodes": [
    {"data": {"id": "act_abc123", "label": "dark_hacker", "risk_score": 850}},
    {"data": {"id": "act_def456", "label": "cipher_master", "risk_score": 720}}
  ],
  "edges": [
    {"data": {"source": "act_abc123", "target": "act_def456", "label": "COLLABORATES_WITH", "weight": 3}}
  ]
}
```

---

## 6. Crawler

### GET `/crawler/targets`

List all crawl targets.

### POST `/crawler/targets`

Create a new crawl target.

**Request:**
```json
{
  "url": "http://example.onion/market",
  "site_name": "DarkMarket",
  "source_type": "onion",
  "crawl_frequency": "every_6h",
  "parser_type": "marketplace",
  "notes": "Major ransomware marketplace",
  "tags": ["ransomware", "marketplace"]
}
```

**Response (201):**
```json
{
  "id": "tgt_abc123",
  "url": "http://example.onion/market",
  "site_name": "DarkMarket",
  "source_type": "onion",
  "status": "active",
  "crawl_frequency": "every_6h",
  "last_crawled": null,
  "last_status": null,
  "pages_crawled": 0,
  "added_by": "usr_abc123",
  "added_at": "2026-06-03T10:30:00Z",
  "notes": "Major ransomware marketplace",
  "tags": ["ransomware", "marketplace"]
}
```

### PUT `/crawler/targets/{target_id}`

Update a crawl target.

### DELETE `/crawler/targets/{target_id}`

Delete a crawl target.

### POST `/crawler/targets/{target_id}/crawl`

Trigger an immediate crawl.

**Response (202):**
```json
{
  "job_id": "job_abc123",
  "target_id": "tgt_abc123",
  "status": "queued",
  "queued_at": "2026-06-03T10:30:00Z"
}
```

### GET `/crawler/jobs`

List crawl jobs with status.

**Response (200):**
```json
{
  "data": [
    {
      "id": "job_abc123",
      "target_id": "tgt_abc123",
      "target_url": "http://example.onion/market",
      "status": "completed",
      "pages_fetched": 25,
      "pages_total": 25,
      "errors": 2,
      "started_at": "2026-06-03T10:30:00Z",
      "completed_at": "2026-06-03T10:32:15Z",
      "proxy_used": "tor"
    }
  ],
  "pagination": {"page": 1, "per_page": 25, "total": 89, "total_pages": 4}
}
```

### GET `/crawler/jobs/{job_id}`

Get detailed job status including individual page results.

---

## 7. Reports

### POST `/reports`

Generate a new report.

**Request:**
```json
{
  "type": "alert_report",
  "format": "pdf",
  "parameters": {
    "severity": ["critical", "high"],
    "date_from": "2026-05-01T00:00:00Z",
    "date_to": "2026-06-03T23:59:59Z",
    "categories": ["ransomware", "data_breach"],
    "include_evidence": true
  }
}
```

**Response (202):**
```json
{
  "report_id": "rpt_abc123",
  "status": "generating",
  "estimated_completion": "2026-06-03T10:31:00Z"
}
```

### GET `/reports`

List generated reports.

### GET `/reports/{report_id}`

Get report status and metadata.

### GET `/reports/{report_id}/download`

Download the generated report file.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token` | string | — | Download token (required, one-time use) |

**Response (200):** Binary file download with `Content-Disposition: attachment` header.

---

## 8. Dashboard

### GET `/dashboard/summary`

Get dashboard summary statistics.

**Response (200):**
```json
{
  "total_alerts": 142,
  "critical_alerts": 12,
  "high_alerts": 45,
  "new_alerts_today": 8,
  "active_targets": 23,
  "total_targets": 35,
  "total_actors": 45,
  "total_pages_crawled": 12580,
  "avg_response_time_ms": 2450,
  "severity_distribution": {
    "critical": 12,
    "high": 45,
    "medium": 58,
    "low": 27
  }
}
```

### GET `/dashboard/trending`

Get trending threats over time.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 7 | Number of days for trend data |

**Response (200):**
```json
{
  "daily_counts": [
    {"date": "2026-05-28", "count": 15},
    {"date": "2026-05-29", "count": 22},
    {"date": "2026-05-30", "count": 18},
    {"date": "2026-05-31", "count": 25},
    {"date": "2026-06-01", "count": 30},
    {"date": "2026-06-02", "count": 28},
    {"date": "2026-06-03", "count": 8}
  ],
  "top_categories": [
    {"category": "ransomware", "count": 42, "trend": "up"},
    {"category": "data_breach", "count": 31, "trend": "stable"},
    {"category": "financial_fraud", "count": 28, "trend": "up"}
  ],
  "top_sources": [
    {"source": "DarkMarket", "count": 55, "source_type": "onion"},
    {"source": "BreachForums", "count": 32, "source_type": "onion"}
  ]
}
```

### GET `/dashboard/timeline`

Get recent activity timeline.

**Response (200):**
```json
{
  "events": [
    {
      "type": "alert_created",
      "severity": "high",
      "title": "Ransomware listing detected",
      "timestamp": "2026-06-03T10:30:00Z"
    },
    {
      "type": "crawl_completed",
      "target": "DarkMarket",
      "pages": 25,
      "timestamp": "2026-06-03T10:25:00Z"
    }
  ]
}
```

---

## 9. Search

### GET `/search`

Full-text search across crawled content, alerts, and actors.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | — | Search query (required) |
| `index` | string | `all` | `content`, `alerts`, `actors`, `all` |
| `category` | string | — | Filter by category |
| `source_type` | string | — | Filter by source type |
| `date_from` | string | — | ISO 8601 date filter |
| `date_to` | string | — | ISO 8601 date filter |
| `page` | int | 1 | Page number |
| `per_page` | int | 25 | Items per page |

**Response (200):**
```json
{
  "data": [
    {
      "id": "cnt_abc123",
      "index": "content",
      "title": "DarkMarket - Ransomware Listings",
      "url": "http://darkmarket.onion/listings/ransomware",
      "snippet": "...ransomware builder <em>LockBit 3.0</em> available now...",
      "score": 850,
      "source_type": "onion",
      "crawled_at": "2026-06-03T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 47,
    "total_pages": 2
  },
  "facets": {
    "categories": [
      {"value": "ransomware", "count": 18},
      {"value": "data_breach", "count": 12}
    ],
    "source_types": [
      {"value": "onion", "count": 35},
      {"value": "surface", "count": 12}
    ]
  }
}
```

---

## 10. Admin

### GET `/admin/users`

List all users (admin only).

### POST `/admin/users`

Create a new user (admin only).

**Request:**
```json
{
  "email": "investigator@police.gov.in",
  "name": "Investigator Singh",
  "password": "securePassword123",
  "role": "analyst"
}
```

**Response (201):** Created user object (password excluded).

**Roles:** `admin`, `analyst`, `viewer`, `crawler_operator`

### PUT `/admin/users/{user_id}`

Update user details or role.

### DELETE `/admin/users/{user_id}`

Delete a user.

### POST `/admin/users/{user_id}/api-keys`

Generate an API key for programmatic access.

### GET `/admin/audit-logs`

View audit logs with pagination.

### GET `/admin/health`

System health check.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "services": {
    "mongodb": {"status": "connected", "latency_ms": 5},
    "elasticsearch": {"status": "connected", "latency_ms": 12},
    "neo4j": {"status": "connected", "latency_ms": 8},
    "redis": {"status": "connected", "latency_ms": 2}
  },
  "active_users": 3,
  "queues": {
    "crawl_tasks": {"depth": 5, "consumers": 2},
    "nlp_tasks": {"depth": 12, "consumers": 3}
  }
}
```

---

## 11. SIEM Export

DarkTrace can export alerts to SIEM systems via two methods:

### Syslog (RFC 5424)

Alerts are forwarded in **CEF** (Common Event Format) or **LEEF** (Log Event Extended Format):

```
CEF:0|DarkTrace|ThreatIntelligence|1.0|1001|Ransomware Detection|5|
  src=172.20.0.5 dst=185.220.101.x dvc=10.0.0.1
  cs1Label=alert_id cs1=alt_abc123
  cs2Label=category cs2=ransomware
  cs3Label=score cs3=750
  cs4Label=source_url cs4=http://darkmarket.onion/listing/123
```

### Webhook

POST JSON payloads to a configurable HTTPS endpoint with HMAC-SHA256 signature header.

---

## 12. Error Responses

All API errors follow a consistent format:

```json
{
  "detail": "Human-readable error message",
  "status_code": 422,
  "errors": [
    {
      "loc": ["body", "url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `202` | Accepted (async operation) |
| `204` | No content (delete success) |
| `400` | Bad request |
| `401` | Unauthorized (missing/invalid token) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Resource not found |
| `409` | Conflict (duplicate resource) |
| `422` | Validation error |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

### Rate Limiting

Rate limit headers are included in all responses:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Remaining requests in current window |
| `X-RateLimit-Reset` | Unix timestamp when the limit resets |

Default limits: 100 requests per minute per user.

---

## Authentication Header Format

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
X-Request-ID: req-abc-123-def  (optional, for tracing)
```

> For complete and detailed API documentation with interactive testing, visit `/docs` (Swagger UI) or `/redoc` (ReDoc) on your DarkTrace instance.
