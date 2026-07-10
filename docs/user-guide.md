# DarkTrace — User Guide

> **Version:** 1.0 | **Last Updated:** 2026-06-03  
> **Target Audience:** Cyber crime investigators, threat analysts, SOC operators

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Dashboard Overview](#2-dashboard-overview)
3. [Managing Crawl Targets](#3-managing-crawl-targets)
4. [Working with Alerts](#4-working-with-alerts)
5. [Creating Watchlists](#5-creating-watchlists)
6. [Investigating Threat Actors](#6-investigating-threat-actors)
7. [Searching Intelligence](#7-searching-intelligence)
8. [Generating Reports](#8-generating-reports)
9. [Administration](#9-administration)
10. [Best Practices](#10-best-practices)
11. [Glossary](#11-glossary)

---

## 1. Getting Started

### 1.1 Logging In

1. Open your browser and navigate to your DarkTrace instance (e.g., `http://localhost:3000`)
2. Enter your credentials provided by your system administrator
3. Upon successful login, you will be redirected to the **Dashboard**

> **Default admin credentials** (change immediately in production):  
> Email: `admin@darktrace.local`  
> Password: `admin123`

### 1.2 User Roles

DarkTrace has four user roles with escalating privileges:

| Role | Permissions | Typical User |
|------|-------------|--------------|
| **Viewer** | View dashboards, alerts, actors, and reports | Senior officers, supervisors |
| **Analyst** | Viewer + manage watchlists, triage alerts, generate reports | Threat analysts, investigators |
| **Crawler Operator** | Analyst + manage crawl targets, trigger crawls | Technical operators |
| **Admin** | Full access including user management, audit logs, system config | System administrators |

### 1.3 Understanding the Interface

The DarkTrace interface consists of:

- **Header** — Search bar, notifications, user menu
- **Sidebar** — Navigation menu with links to all sections
- **Main Content Area** — Displays the selected page

---

## 2. Dashboard Overview

The Dashboard is your command centre. It provides a real-time snapshot of all threat intelligence activities.

### 2.1 Summary Cards

At the top of the dashboard, you will find summary cards showing:

- **Total Alerts** — Number of active alerts across all severities
- **Critical Alerts** — Alerts requiring immediate attention (shown in red)
- **New Today** — Alerts generated in the last 24 hours
- **Active Targets** — Crawl targets currently being monitored
- **Tracked Actors** — Number of identified threat actors

### 2.2 Charts and Visualizations

- **Severity Distribution** (Donut chart) — Breakdown of alerts by severity level
- **Alert Trends** (Line chart) — Daily alert volume over the past 7-30 days
- **Trending Threats** — Top threat categories with trend indicators (up/down/stable)
- **Source Rankings** — Top dark web sources generating alerts
- **Activity Timeline** — Chronological feed of recent events (alerts, crawls, etc.)

### 2.3 Interpretation Guide

| Indicator | Meaning | Action Required |
|-----------|---------|-----------------|
| 🔴 Critical alert count rising | Active threat campaign | Investigate immediately |
| 🟠 High alert spike | New threat category detected | Review and triage |
| 📉 Crawl success rate dropping | Target sites may be down | Check proxy pool |
| 🆕 New actor detected | Unknown entity surfacing | Profile and monitor |

---

## 3. Managing Crawl Targets

Crawl targets are the dark web sites DarkTrace monitors for threats.

### 3.1 Adding a Target

1. Navigate to **Crawler** in the sidebar
2. Click **"Add Target"**
3. Fill in the form:
   - **URL** — Full URL of the target site (`.onion`, `.i2p`, or surface web)
   - **Site Name** — A descriptive name for the target
   - **Source Type** — `onion` (Tor), `i2p`, or `surface`
   - **Crawl Frequency** — How often to crawl (every 1h to every 30 days)
   - **Parser Type** — Optional: `marketplace`, `forum`, `paste`, or generic
   - **Tags** — Labels for organization (e.g., "ransomware", "marketplace")
4. Click **"Save"** — the target will appear in the targets list

### 3.2 Crawl Frequencies

| Frequency | Best For | Expected Pages/Day |
|-----------|----------|-------------------|
| Every 1h | High-priority targets | 50-200 |
| Every 6h | Active marketplaces, forums | 10-50 |
| Every 24h | Standard monitoring | 1-10 |
| Every 7-30d | Low-priority or stable targets | 0-5 |

### 3.3 Triggering a Manual Crawl

1. In the targets list, find the target you want to crawl
2. Click the **"Crawl Now"** button (play icon)
3. A job will be queued and executed immediately
4. Monitor progress in the **Jobs** section below the target list

### 3.4 Viewing Crawl Jobs

The Jobs section shows all crawl jobs with their status:

| Status | Meaning |
|--------|---------|
| `queued` | Job is waiting for a worker |
| `running` | Crawl is in progress |
| `completed` | All pages fetched successfully |
| `failed` | Crawl encountered errors |
| `partial` | Some pages fetched, some failed |

### 3.5 Target Statuses

| Status | Meaning |
|--------|---------|
| `active` | Target is being crawled on schedule |
| `paused` | Crawl schedule is suspended |
| `disabled` | Target is not crawled |

---

## 4. Working with Alerts

Alerts are generated when crawled content matches watchlist keywords, patterns, or exceeds threat score thresholds.

### 4.1 Alert Severity Levels

| Severity | Score Range | Color | Response Time |
|----------|------------|-------|---------------|
| **Critical** | 801-1000 | 🔴 Red | Immediate |
| **High** | 501-800 | 🟠 Amber | Within 24 hours |
| **Medium** | 201-500 | 🟡 Yellow | Within 72 hours |
| **Low** | 0-200 | 🟢 Green | Log for reference |

### 4.2 Alert Statuses

| Status | Meaning |
|--------|---------|
| `new` | Alert requires review |
| `investigating` | An analyst is working on it |
| `resolved` | Threat has been addressed |
| `false_positive` | Confirmed not a real threat |

### 4.3 Viewing and Filtering Alerts

1. Navigate to **Alerts** in the sidebar
2. Use the filter panel to narrow down:
   - **Severity** — Check specific severity levels
   - **Status** — Filter by investigation status
   - **Category** — Filter by threat category
   - **Date Range** — Time period filter
   - **Search** — Keyword search within alerts
3. Click on any alert to view full details

### 4.4 Alert Detail View

The alert detail page provides:

- **Summary** — AI-generated overview of the threat
- **Source Information** — URL, source type, crawl timestamp
- **Content Snippet** — Excerpt of the crawled content that triggered the alert
- **Matched Keywords** — Specific keywords that matched (with positions)
- **Matched Patterns** — Regex patterns detected (e.g., credit card numbers)
- **Extracted Entities** — PII, crypto addresses, emails, etc.
- **Threat Score Breakdown** — Factor-by-factor score composition
- **Notes** — Add investigation notes
- **Assignment** — Assign to a team member

### 4.5 Triage Actions

From the alert detail page, you can:

- **Change Status** — Update investigation progress
- **Assign** — Assign to yourself or another analyst
- **Add Notes** — Document findings
- **Bulk Actions** — Select multiple alerts and change status or add notes in bulk

### 4.6 Best Practices for Alert Triage

1. **Triage critical alerts first** — Sort by severity descending
2. **Add investigation notes** — Document findings for team awareness
3. **Resolve or mark false positive** — Keep the alert queue clean
4. **Correlate with actors** — Link alerts to known threat actors
5. **Export evidence** — Generate reports for legal proceedings

---

## 5. Creating Watchlists

Watchlists are the core mechanism for detecting specific threats. They define keywords, regex patterns, and entity types to monitor.

### 5.1 Creating a Watchlist

1. Navigate to **Watchlists** in the sidebar
2. Click **"New Watchlist"**
3. Configure the watchlist:
   - **Name** — Descriptive name (e.g., "Ransomware Operators")
   - **Description** — Purpose of this watchlist
   - **Keywords** — Words or phrases to detect (one per line, press Enter to add)
   - **Regex Patterns** — Regular expressions for pattern matching
   - **Entities** — Entity types to flag (BTC addresses, emails, etc.)
   - **Severity Boost** — Additional score weight when content matches
4. Click **"Save"**

### 5.2 Keyword Tips

- Use specific terms relevant to your investigation
- Include variations (e.g., "ransomware", "ransom ware", "ransom")
- For usernames, include common handles
- Keywords are case-insensitive

### 5.3 Regex Pattern Examples

| Pattern | Detects | Example Match |
|---------|---------|---------------|
| `\b[A-Z]{5}\d{4}[A-Z]\b` | Payment Card Numbers | `ABCD1234E` |
| `\b1[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b` | Bitcoin Addresses | `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` |
| `\b0x[a-fA-F0-9]{40}\b` | Ethereum Addresses | `0x742d35Cc6634C0532925a3b844Bc9e` |
| `\b\d{3}-\d{2}-\d{4}\b` | SSNs | `123-45-6789` |
| `\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b` | Credit Cards | `4111-1111-1111-1111` |

### 5.4 Watchlist Use Cases

| Use Case | Keywords | Patterns | Severity Boost |
|----------|----------|----------|----------------|
| Ransomware tracking | `lockbit`, `blackcat`, `ransomware` | — | 200 |
| Data leak monitoring | Company name, domain | Email patterns | 300 |
| Fraud detection | `CVV`, `fullz`, `dumps` | Credit card, PAN | 250 |
| Threat actor tracking | Actor handle | BTC address regex | 150 |
| Drug monitoring | Drug names, slang | — | 100 |

---

## 6. Investigating Threat Actors

DarkTrace profiles threat actors by linking pseudonyms, platforms, and entities across crawled content.

### 6.1 Actors List

Navigate to **Actors** to see all identified threat actors ranked by risk score. The list shows:

- **Pseudonyms** — Known usernames/aliases
- **Risk Score** — 0-1000 based on activity severity
- **Posts** — Total content attributed to the actor
- **First/Last Seen** — Activity timeline
- **Active Platforms** — Marketplaces/forums used
- **Top Categories** — Types of threats associated

### 6.2 Actor Detail

Click on an actor to view their full profile:

- **Pseudonyms** — All known aliases with associated platforms
- **Risk Score** — Score breakdown and risk factors
- **Timeline** — Activity over time
- **Linked Entities** — BTC addresses, emails, phone numbers
- **Recent Activity** — Latest posts and alerts
- **Connected Actors** — Other actors linked via Neo4j graph

### 6.3 Network Graph

The **Network Graph** tab visualizes actor relationships:

- **Nodes** — Actors (size indicates risk score)
- **Edges** — Relationships (collaboration, same platform, shared entities)
- **Colors** — Category or platform grouping
- **Interactions** — Click to focus, drag to explore, zoom in/out

**Investigative uses:**
- Identify organized groups working together
- Find actors sharing the same BTC address
- Discover new actors connected to known threats

---

## 7. Searching Intelligence

The Search page provides full-text search across all crawled content, alerts, and actors.

### 7.1 Basic Search

1. Use the search bar in the header (always accessible)
2. Enter keywords, phrases, or patterns
3. Results appear grouped by relevance score

### 7.2 Advanced Search

On the Search page, you can apply filters:

- **Index** — Search specific data: `Content`, `Alerts`, `Actors`, or `All`
- **Category** — Filter by threat category
- **Source Type** — `onion`, `i2p`, or `surface`
- **Date Range** — Time period for results
- **Facets** — Refine by category count and source type

### 7.3 Search Tips

- Use quotes for exact phrases: `"ransomware builder"`
- Combine terms for specific results: `lockbit hospital`
- Search entity values: BTC addresses, emails, phone numbers
- Use date filters to narrow results to specific incidents

---

## 8. Generating Reports

Reports provide formal documentation of threat intelligence for sharing with stakeholders or legal proceedings.

### 8.1 Available Report Types

| Report Type | Description | Best For |
|-------------|-------------|----------|
| **Alert Report** | Detailed alert with evidence summary | Individual incident |
| **Threat Summary** | Overview of threats over a period | Management briefings |
| **Actor Profile** | Comprehensive actor dossier | Legal proceedings |
| **Custom Report** | User-selected data and format | Ad-hoc needs |

### 8.2 Generating a Report

1. Navigate to **Reports** in the sidebar
2. Click **"Generate Report"**
3. Configure:
   - **Type** — Select report template
   - **Format** — PDF, CSV, or JSON
   - **Parameters** — Severity, date range, categories
   - **Include Evidence** — Include content snippets (PDF only)
4. Click **"Generate"**
5. Monitor status — reports typically generate within 30 seconds
6. Once complete, click **"Download"** and provide the one-time download token

### 8.3 Report Formats

| Format | Best For | Notes |
|--------|----------|-------|
| **PDF** | Formal reports, legal evidence | Includes branding, formatting |
| **CSV** | Data analysis, spreadsheets | Machine-readable, flat structure |
| **JSON** | Programmatic integration | Structured data for APIs |

### 8.4 Downloading Reports

1. In the Reports list, find your generated report
2. Click the download icon
3. Enter the download token (shown once at generation)
4. The file will be saved to your computer

> **Security:** Download tokens are one-time use and expire after 24 hours.

---

## 9. Administration

Available to users with the **admin** role.

### 9.1 User Management

Navigate to **Admin > Users** to:

- **View Users** — List all users with roles and status
- **Create User** — Add new investigators or operators
- **Edit User** — Change name, email, role, or reset password
- **Delete User** — Remove deactivated users
- **Generate API Key** — Create programmatic access keys

### 9.2 Audit Logs

The **Audit Logs** section records all user actions:

- Login/logout events
- Alert status changes
- Watchlist modifications
- Report generation
- Admin actions

Audit logs are tamper-evident and suitable for compliance requirements.

### 9.3 System Health

The **System Health** page shows:

- Database connection status (MongoDB, Elasticsearch, Neo4j, Redis)
- Queue depths (crawl tasks, NLP tasks)
- Uptime and version information
- Latency measurements

---

## 10. Best Practices

### 10.1 Daily Operations

1. **Start with the Dashboard** — Review summary cards and trending threats
2. **Triage new alerts** — Process alerts from highest severity down
3. **Check crawl status** — Ensure targets are being crawled successfully
4. **Review watchlist matches** — Fine-tune keywords to reduce noise

### 10.2 Watchlist Management

- Start with broad keywords, then narrow down to reduce false positives
- Use severity boost sparingly — high values can overwhelm with noise
- Regularly review and update watchlists based on emerging threats
- Archive inactive watchlists rather than deleting them

### 10.3 Alert Triage Workflow

```
New Alert → Review Details → Check Source URL
    → Verify Content → Correlate with Actors
    → Investigate or Mark False Positive
    → Add Notes → Change Status
```

### 10.4 Performance Optimization

- Limit concurrent crawl targets to match available bandwidth
- Use appropriate crawl frequencies (don't over-crawl stable sites)
- Archive old alerts (90+ days) to maintain dashboard performance
- Schedule report generation during off-peak hours

### 10.5 Security Recommendations

- Change all default passwords immediately
- Use strong, unique passwords for each user
- Regularly rotate JWT secrets and API keys
- Monitor audit logs for suspicious activity
- Use HTTPS in production environments

---

## 11. Glossary

| Term | Definition |
|------|------------|
| **Alert** | A notification generated when content matches threat criteria |
| **Actor** | A threat actor identified by pseudonyms across dark web platforms |
| **Crawl Target** | A dark web URL configured for monitoring |
| **Crawl Job** | A single execution of crawling a target site |
| **CEF** | Common Event Format — SIEM log format |
| **ES** | Elasticsearch — full-text search database |
| **I2P** | Invisible Internet Project — anonymous network layer |
| **LEEF** | Log Event Extended Format — SIEM log format |
| **NLP** | Natural Language Processing — text analysis |
| **NER** | Named Entity Recognition — extracting entities from text |
| **Onion** | .onion domain accessible via Tor network |
| **PII** | Personally Identifiable Information |
| **SIEM** | Security Information and Event Management |
| **SOC** | Security Operations Center |
| **Tor** | The Onion Router — anonymous communication network |
| **Watchlist** | A set of keywords/patterns for threat detection |
| **Webhook** | HTTP callback for real-time event notifications |
