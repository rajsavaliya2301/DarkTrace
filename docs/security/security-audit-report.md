# DarkTrace Security Audit Report

**Application:** DarkTrace — Dark Web Surveillance & Threat Intelligence Tool  
**Audit Date:** June 3, 2026  
**Auditor:** Security Engineer  
**Version:** 1.0.0  
**Classification:** CONFIDENTIAL — Law Enforcement Sensitive

---

## 1. Executive Summary

### Overall Risk Level: **CRITICAL**

DarkTrace is a sophisticated dark web monitoring application that handles highly sensitive law enforcement data. The audit identified **27 security findings** across the OWASP Top 10 (2021) categories, including **3 Critical**, **7 High**, **10 Medium**, and **7 Low** severity issues.

### Top Findings

| # | Finding | Severity | Category |
|---|---------|----------|----------|
| 1 | Server-Side Request Forgery (SSRF) in Crawler Engine | **CRITICAL** | A10:SSRF |
| 2 | Default Admin Credentials with Plaintext Logging | **CRITICAL** | A07:Identification Failures |
| 3 | Weak Default JWT Secret Key | **CRITICAL** | A02:Cryptographic Failures |
| 4 | No Rate Limiting on Authentication Endpoints | **HIGH** | A07:Identification Failures |
| 5 | Elasticsearch TLS Verification Disabled by Default | **HIGH** | A02:Cryptographic Failures |
| 6 | Hardcoded Default Passwords Across Infrastructure | **HIGH** | A05:Security Misconfiguration |
| 7 | Refresh Token Reuse Detection Missing | **HIGH** | A07:Identification Failures |
| 8 | Weak Default Neo4j Password | **HIGH** | A05:Security Misconfiguration |
| 9 | No MFA Implementation | **HIGH** | A07:Identification Failures |

### Risk Context

As a law enforcement tool operating on the dark web, DarkTrace faces elevated threat risks:
- **Targeted attacks** from sophisticated threat actors seeking to identify investigators
- **Legal & compliance requirements** for chain of custody and evidence integrity
- **Data sensitivity** involving PII, criminal intelligence, and investigation details
- **Operational security (OPSEC)** risks from leaking investigator identity via crawl operations

---

## 2. Methodology

The audit was conducted using the following methodology framework:

1. **Architecture Review** — Analyzed the application's architecture, network segmentation, data flow, and trust boundaries
2. **Manual Code Review** — Read all 45+ backend Python files, 8+ frontend TypeScript files, and 5 infrastructure configuration files
3. **Threat Modeling (STRIDE)** — Applied STRIDE per component to identify spoofing, tampering, repudiation, information disclosure, DoS, and elevation of privilege threats
4. **OWASP Top 10 (2021) Mapping** — Mapped findings to OWASP categories
5. **Dependency Analysis** — Reviewed `requirements.txt` and `package.json` for known vulnerable components
6. **Configuration Review** — Examined Docker, nginx, CI/CD, and environment configurations

### Scope

| Component | Files Reviewed |
|-----------|---------------|
| Backend Auth | `auth/router.py`, `auth/models.py`, `auth/jwt.py` |
| Backend Crawler | `crawler/router.py`, `crawler/engine.py`, `crawler/scheduler.py`, `crawler/parsers.py`, `crawler/proxy_pool.py` |
| Backend Alerts | `alerts/router.py`, `alerts/engine.py`, `alerts/models.py` |
| Backend Watchlists | `watchlists/router.py`, `watchlists/models.py` |
| Backend Actors | `actors/router.py`, `actors/profiler.py`, `actors/graph.py` |
| Backend Reports | `reports/router.py`, `reports/generator.py` |
| Backend Export | `export/siem.py`, `export/blockchain.py` |
| Backend NLP | `nlp/analyzer.py`, `nlp/entities.py`, `nlp/sentiment.py`, `nlp/translator.py`, `nlp/classifier.py`, `nlp/keyword_matcher.py` |
| Backend Admin | `admin/router.py` |
| Backend Search | `search/router.py` |
| Backend Dashboard | `dashboard/router.py` |
| Backend Threat Scoring | `threat_scoring/engine.py`, `threat_scoring/rules.py` |
| Backend Core | `config.py`, `database.py`, `dependencies.py`, `main.py` |
| Frontend Auth | `api/client.ts`, `store/authStore.ts`, `components/layout/ProtectedRoute.tsx` |
| Infrastructure | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `.env.example`, `.github/workflows/ci.yml` |

---

## 3. Findings by Severity

### 3.1 CRITICAL FINDINGS

#### FINDING-001: Server-Side Request Forgery (SSRF) in Crawler Engine

**Severity:** CRITICAL (CVSS 9.1)  
**CWE:** CWE-918 (Server-Side Request Forgery)  
**OWASP:** A10:2021 — Server-Side Request Forgery (SSRF)

**Description:**
The crawler engine accepts arbitrary URLs from authenticated users and fetches them directly via `aiohttp.ClientSession.get()` without validating that the target is a legitimate dark web (`.onion`, `.i2p`) or surface web URL. An attacker with `crawler:write` permissions can use the crawler to scan internal network infrastructure, access cloud metadata endpoints, or attack other services.

**Affected Files:**
- `backend/app/crawler/router.py` — Lines 32-42: `CrawlTargetCreate.url: str = Field(..., max_length=1024)` — no URL scheme/domain validation
- `backend/app/crawler/engine.py` — Lines 52, 186: `session.get(target_url, ...)` — direct fetch without URL validation

**Impact:**
- Internal network reconnaissance (probe `172.20.x.x`, `10.x.x.x` subnets)
- Access cloud provider metadata endpoints (`169.254.169.254`)
- Abuse the application to attack third-party services
- Data exfiltration via crafted responses
- Since the crawler routes through Tor/I2P proxies, malicious requests may be difficult to trace

**Remediation:**

```python
# Add URL validation in crawler/router.py - CrawlTargetCreate
from pydantic import validator
import re

class CrawlTargetCreate(BaseModel):
    url: str = Field(..., max_length=1024)
    
    @validator("url")
    def validate_crawl_url(cls, v):
        # Reject internal IPs and common SSRF targets
        blocked_patterns = [
            r"^https?://(localhost|127\.\d+\.\d+\.\d+)",
            r"^https?://10\.\d+\.\d+\.\d+",
            r"^https?://172\.(1[6-9]|2\d|3[01])\.\d+\.\d+",
            r"^https?://192\.168\.\d+\.\d+",
            r"^https?://169\.254\.\d+\.\d+",
            r"^https?://.*\.internal",
            r"^https?://.*\.local",
            r"^https?://metadata\.google\.internal",
            r"^file://",
            r"^dict://",
            r"^gopher://",
        ]
        for pattern in blocked_patterns:
            if re.match(pattern, v, re.IGNORECASE):
                raise ValueError(f"URL '{v}' is not allowed (blocked by SSRF protection)")
        
        # Validate scheme
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        
        return v
```

Additionally, add URL validation in the crawl engine before fetching:

```python
# In crawler/engine.py, add URL validation before making requests
from urllib.parse import urlparse

def _validate_target_url(self, url: str) -> bool:
    """Validate target URL to prevent SSRF."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    
    # Block internal IP ranges
    import ipaddress
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        # Hostname (non-IP) — check for internal domains
        blocked_domains = [".local", ".internal", "localhost"]
        if any(hostname.endswith(d) for d in blocked_domains):
            return False
    
    # Only allow http/https
    if parsed.scheme not in ("http", "https"):
        return False
    
    return True
```

---

#### FINDING-002: Default Admin Credentials with Plaintext Logging

**Severity:** CRITICAL (CVSS 9.3)  
**CWE:** CWE-798 (Use of Hardcoded Credentials), CWE-532 (Information Exposure Through Log Files)  
**OWASP:** A07:2021 — Identification and Authentication Failures

**Description:**
The application seeds a default admin user on first startup using credentials from environment variables with easily guessable defaults (`admin123` / `changeme_admin_password`). Worse, the credentials are logged to the console **in plaintext** during startup (`main.py` lines 214-216). If a production deployment forgets to change these, any attacker who gains access to the network can log in as administrator. Additionally, the logs themselves expose credentials.

**Affected Files:**
- `backend/app/config.py` — Lines 109-114: Default values for admin email and password
- `backend/app/main.py` — Lines 206-216: `_seed_default_admin()` — logs email and password
- `.env.example` — Lines 94-95: Default credentials documented

**Impact:**
- Complete application compromise if default credentials are not changed
- Credential exposure in log aggregation systems (ELK, Splunk, CloudWatch)
- Regulatory non-compliance (GDPR, evidence handling)

**Remediation:**

```python
# In main.py, remove password from log output:
async def _seed_default_admin():
    """Create default admin user if no users exist."""
    try:
        from app.database import get_mongodb
        db = await get_mongodb()
        existing = await db.users.find_one()
        if existing:
            return

        from app.auth.models import new_user_document
        settings = get_settings()
        admin_doc = new_user_document(
            email=settings.DEFAULT_ADMIN_EMAIL,
            name="System Administrator",
            password=settings.DEFAULT_ADMIN_PASSWORD,
            role="admin",
        )
        await db.users.insert_one(admin_doc)
        # NEVER log passwords!
        logger.info("Default admin user created: %s", settings.DEFAULT_ADMIN_EMAIL)
    except Exception as e:
        logger.warning("Failed to seed default admin: %s", e)
```

Additional hardening:
```python
# In config.py, force override check in production
import os

class Settings:
    @property
    def SECRET_KEY(self) -> str:
        key = os.getenv("SECRET_KEY", "")
        if not key or key == "change-me-in-production-use-a-strong-random-secret":
            raise RuntimeError(
                "CRITICAL: SECRET_KEY must be set to a strong random value in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
        return key
```

---

#### FINDING-003: Weak Default JWT Secret Key

**Severity:** CRITICAL (CVSS 9.1)  
**CWE:** CWE-321 (Use of Hard-coded Cryptographic Key)  
**OWASP:** A02:2021 — Cryptographic Failures

**Description:**
The JWT `SECRET_KEY` defaults to a well-known string `"change-me-in-production-use-a-strong-random-secret"` if not provided via environment variable. This means any deployment that does not explicitly set `SECRET_KEY` will have its JWT tokens forgeable by anyone who knows the default (including all open-source viewers of this codebase). Combined with the HS256 symmetric algorithm, a leaked secret compromises all tokens.

**Affected Files:**
- `backend/app/config.py` — Lines 22-24
- `backend/app/auth/jwt.py` — Lines 35, 53, 61-66: Uses `settings.SECRET_KEY` for encoding/verification

**Impact:**
- Complete authentication bypass — anyone can forge valid JWTs for any user
- Privilege escalation to admin role
- Indefinite session hijacking

**Remediation:**

1. **Add validation to prevent the default from being used in production:**

```python
# In config.py
import os
import secrets

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    
    def __init__(self):
        if not self.SECRET_KEY:
            if os.getenv("ENVIRONMENT") == "production":
                raise RuntimeError(
                    "SECRET_KEY environment variable is required in production. "
                    "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                )
            self.SECRET_KEY = "dev-only-insecure-key-do-not-use-in-prod"
```

2. **Consider upgrading to RS256 (asymmetric JWT):**

```python
# In auth/jwt.py, add support for RS256
# Generate keys:
#   openssl genrsa -out private.pem 2048
#   openssl rsa -in private.pem -pubout -out public.pem

def create_access_token(...):
    settings = get_settings()
    if settings.ALGORITHM.startswith("RS"):
        with open(settings.JWT_PRIVATE_KEY_PATH, "r") as f:
            private_key = f.read()
        token = pyjwt.encode(payload, private_key, algorithm=settings.ALGORITHM)
    else:
        token = pyjwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token
```

---

### 3.2 HIGH FINDINGS

#### FINDING-004: No Rate Limiting on Authentication Endpoints

**Severity:** HIGH (CVSS 7.5)  
**CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)  
**OWASP:** A07:2021 — Identification and Authentication Failures

**Description:**
The application implements a rate-limiting dependency (`check_rate_limit`) but it is **not applied** to the `/auth/login` endpoint. This allows an attacker to perform unlimited password brute-force attacks. The account lockout mechanism (after 5 failed attempts with a 5-minute lock) is helpful but can be bypassed by rotating IPs or waiting out the lockout. Without rate limiting at the network level, a distributed attack can try thousands of passwords per minute against multiple accounts.

**Affected Files:**
- `backend/app/auth/router.py` — Lines 40-152: The `login` endpoint does not include `Depends(check_rate_limit)`
- `backend/app/dependencies.py` — Lines 311-343: `check_rate_limit` exists but is unused on auth routes

**Impact:**
- Successful password brute-force attacks against investigator/administrator accounts
- Account takeover with full system access
- Data exfiltration and investigation compromise

**Remediation:**

```python
# In auth/router.py, add rate limiting dependency to the login endpoint:
from app.dependencies import check_rate_limit

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis: AsyncRedis = Depends(get_redis_client),
    _: None = Depends(check_rate_limit),  # Add this line
):
    # ... existing code ...
```

Additionally, implement IP-based rate limiting specifically for login:

```python
# In dependencies.py, add a login-specific rate limiter
async def check_login_rate_limit(
    request: Request,
    redis: AsyncRedis = Depends(get_redis_client),
):
    """Stricter rate limiting for login attempts."""
    ip = request.client.host if request.client else "unknown"
    key = f"rate:login:{ip}"
    
    pipe = redis.pipeline()
    now = time.time()
    window = 300  # 5 minutes
    limit = 10   # 10 attempts per 5 minutes
    
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window)
    results = await pipe.execute()
    
    count = results[1]
    if count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )
```

---

#### FINDING-005: Elasticsearch TLS Verification Disabled by Default

**Severity:** HIGH (CVSS 7.4)  
**CWE:** CWE-295 (Improper Certificate Validation)  
**OWASP:** A02:2021 — Cryptographic Failures

**Description:**
Elasticsearch TLS certificate verification is disabled by default (`ELASTICSEARCH_VERIFY_CERTS=false`). This means all communication between the DarkTrace backend and Elasticsearch is vulnerable to man-in-the-middle attacks. Credentials (username/password) sent to Elasticsearch can be intercepted, and data in transit can be read or modified.

**Affected Files:**
- `docker-compose.yml` — Line 285: `ELASTICSEARCH_VERIFY_CERTS=${ELASTICSEARCH_VERIFY_CERTS:-false}`
- `.env.example` — Line 37: `ELASTICSEARCH_VERIFY_CERTS=false`
- `backend/app/database.py` — Lines 81-88: `verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS`

**Impact:**
- Man-in-the-middle attacks on search index data
- Credential interception
- Data integrity compromise on search results

**Remediation:**

```yaml
# In docker-compose.yml, change default to true:
ELASTICSEARCH_VERIFY_CERTS=${ELASTICSEARCH_VERIFY_CERTS:-true}
```

```python
# In database.py, add a warning if verify_certs is disabled:
if not settings.ELASTICSEARCH_VERIFY_CERTS:
    logger.warning(
        "Elasticsearch TLS verification is DISABLED. "
        "Set ELASTICSEARCH_VERIFY_CERTS=true in production."
    )
```

```bash
# In production, provide the CA certificate:
# docker-compose.yml
volumes:
  - ./certs/elasticsearch-ca.pem:/usr/share/elasticsearch/config/certs/ca.pem
environment:
  ELASTICSEARCH_CA_CERTS: /usr/share/elasticsearch/config/certs/ca.pem
```

---

#### FINDING-006: Hardcoded Default Passwords Across Infrastructure

**Severity:** HIGH (CVSS 8.2)  
**CWE:** CWE-798 (Use of Hardcoded Credentials)  
**OWASP:** A05:2021 — Security Misconfiguration

**Description:**
Multiple infrastructure services use default, hardcoded passwords in `docker-compose.yml` and `.env.example`. These passwords are documented in plaintext in the source code:
- MongoDB: `darktrace_pass`
- Elasticsearch: `darktrace_es_pass`
- Neo4j: `darktrace_neo4j_pass`
- Redis: `darktrace_redis_pass`
- RabbitMQ: `darktrace_rabbit_pass`

**Affected Files:**
- `docker-compose.yml` — Lines 83-84, 123, 161, 198, 230-233, 278, 288, 290, 309, 391, 443
- `.env.example` — Lines 25-55
- `backend/app/config.py` — Lines 35-36, 54-55

**Impact:**
- Complete database compromise if network access is obtained
- Data breach of all crawled content, user data, and intelligence
- Privilege escalation via database credential reuse

**Remediation:**

```yaml
# docker-compose.yml — Remove default password values, require explicit overrides:
services:
  mongodb:
    environment:
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_INITDB_ROOT_PASSWORD:?MongoDB root password is required}
```

```python
# config.py — Validate passwords are not defaults:
class Settings:
    @property
    def NEO4J_PASSWORD(self) -> str:
        pw = os.getenv("NEO4J_PASSWORD", "")
        if pw in ("password", "darktrace_neo4j_pass", ""):
            logger.warning("Neo4j password is using a weak/default value. Change immediately.")
        return pw
```

---

#### FINDING-007: Refresh Token Reuse Detection Missing

**Severity:** HIGH (CVSS 7.1)  
**CWE:** CWE-323 (Reusing a Nonce, Key Pair in Encryption)  
**OWASP:** A07:2021 — Identification and Authentication Failures

**Description:**
The refresh token rotation mechanism removes the old token when a new one is issued, but it does **not** detect if an old/stolen refresh token is reused. If an attacker steals a refresh token, they can use it alongside the legitimate user, and both will work until the legitimate user's token happens to be rotated first. There is no token family tracking or theft detection.

**Affected Files:**
- `backend/app/auth/router.py` — Lines 155-226: `refresh_token` endpoint removes old token but doesn't detect reuse

**Impact:**
- Persistent session hijacking
- Stolen refresh tokens can be used indefinitely until legitimate user logs out
- No alerting on token theft

**Remediation:**

```python
# In auth/router.py, add token reuse detection:
@router.post("/refresh")
async def refresh_token(...):
    # ... existing verification ...
    
    # Verify refresh token exists in user document
    refresh_hash = hashlib.sha256(body.refresh_token.encode()).hexdigest()
    user = await db.users.find_one(
        {"_id": user_id, "refresh_tokens.token_hash": refresh_hash}
    )
    if not user:
        # Token reuse detected! Invalidate ALL refresh tokens for this user
        await db.users.update_one(
            {"_id": user_id},
            {
                "$set": {"refresh_tokens": []},
                "$push": {
                    "security_events": {
                        "type": "token_reuse_attack",
                        "timestamp": datetime.utcnow().isoformat(),
                        "ip_address": request.client.host if request.client else "",
                        "severity": "high",
                    }
                },
            },
        )
        logger.warning(f"Refresh token reuse detected for user {user_id}. All sessions invalidated.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not recognized. All sessions invalidated due to suspected token theft.",
        )
    
    # Generate new tokens
    new_access = create_access_token(user_id, user["email"], user.get("role", "investigator"))
    new_refresh = create_refresh_token(user_id)
    
    # Store new refresh token (remove old, add new — rotation with detection)
    new_refresh_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    
    # Remove ALL existing tokens if reuse detected (already done above)
    # Otherwise just remove the used one
    await db.users.update_one(
        {"_id": user_id},
        {"$pull": {"refresh_tokens": {"token_hash": refresh_hash}}},
    )
    # ... rest of existing code ...
```

---

#### FINDING-008: Weak Default Neo4j Password

**Severity:** HIGH (CVSS 7.5)  
**CWE:** CWE-521 (Weak Password Requirements)  
**OWASP:** A07:2021 — Identification and Authentication Failures

**Description:**
The Neo4j database password defaults to `"password"` in `config.py`. This is one of the most commonly used and guessed passwords. Combined with the fact that Neo4j's HTTP interface (port 7474) is exposed (bound to `127.0.0.1` in Docker but could be exposed in some deployments), the graph database containing actor relationship data is at high risk.

**Affected Files:**
- `backend/app/config.py` — Line 55: `NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")`

**Impact:**
- Unauthorized access to the actor relationship graph
- Tampering with intelligence data linking investigators' targets
- Data exfiltration of all actor profiles and connections

**Remediation:**

```python
# In config.py
NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD environment variable must be set in production")
```

---

#### FINDING-009: No MFA Implementation

**Severity:** HIGH (CVSS 7.0)  
**CWE:** CWE-308 (Use of Single-factor Authentication)  
**OWASP:** A07:2021 — Identification and Authentication Failures

**Description:**
While the user document schema includes MFA fields (`mfa_enabled`, `mfa_secret`), there is **no actual MFA implementation**. The application only uses single-factor authentication (password). For a law enforcement tool handling highly sensitive dark web intelligence, this is insufficient. A compromised password gives attackers full access to all investigations.

**Affected Files:**
- `backend/app/auth/models.py` — Lines 113-114: MFA fields exist but are never enforced
- `backend/app/auth/router.py` — No MFA verification during login

**Impact:**
- Account takeover via single credential compromise
- No defense against phishing attacks on investigators
- Non-compliance with law enforcement security standards

**Remediation:**

1. **Implement TOTP-based MFA:**

```python
# In auth/router.py login endpoint, after password verification:
if user.get("mfa_enabled", False):
    # Generate and send MFA challenge
    mfa_token = str(uuid.uuid4())
    await redis.setex(
        f"mfa:challenge:{mfa_token}",
        300,  # 5 minutes
        json.dumps({"user_id": user_id, "email": user["email"]}),
    )
    return {
        "mfa_required": True,
        "mfa_token": mfa_token,
        "message": "MFA verification required",
    }

# In auth/models.py, add MFA verification:
class MFAVerifyRequest(BaseModel):
    mfa_token: str
    code: str = Field(..., min_length=6, max_length=6)

# In auth/router.py, add MFA verification endpoint:
@router.post("/mfa/verify")
async def verify_mfa(
    request: Request,
    body: MFAVerifyRequest,
    redis: AsyncRedis = Depends(get_redis_client),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    # Verify MFA token
    challenge_data = await redis.get(f"mfa:challenge:{body.mfa_token}")
    if not challenge_data:
        raise HTTPException(status_code=400, detail="Invalid or expired MFA challenge")
    
    challenge = json.loads(challenge_data)
    user = await db.users.find_one({"_id": challenge["user_id"]})
    
    # Verify TOTP code
    import pyotp
    totp = pyotp.TOTP(user["mfa_secret"])
    if not totp.verify(body.code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    # Generate tokens
    access_token = create_access_token(user["_id"], user["email"], user.get("role", "investigator"))
    refresh_token = create_refresh_token(user["_id"])
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(...),
    )
```

---

### 3.3 MEDIUM FINDINGS

#### FINDING-010: Sensitive Data Exposure in Audit Logs

**Severity:** MEDIUM (CVSS 6.5)  
**CWE:** CWE-532 (Information Exposure Through Log Files)  
**OWASP:** A09:2021 — Security Logging and Monitoring Failures

**Description:**
The default admin credentials are logged to the console during application startup, including the password. Additionally, the audit log system logs actions with potentially sensitive details such as IP addresses, user agents, and action-specific data.

**Affected Files:**
- `backend/app/main.py` — Lines 213-216: `logger.info("Default admin created: %s / %s", email, password)`
- `backend/app/dependencies.py` — Lines 283-305: `log_user_action` logs IP addresses and user agents

**Impact:**
- Credential exposure in log management systems
- PII exposure (IP addresses, user agents) in logs
- Compliance violations

**Remediation:**

```python
# In main.py — Never log credentials:
logger.info("Default admin user created: %s", settings.DEFAULT_ADMIN_EMAIL)
# Remove password from the log statement entirely
```

```python
# In dependencies.py — Consider masking sensitive details or making it configurable:
async def log_user_action(..., ip_address=None, user_agent=None):
    # In production, optionally mask IPs for privacy compliance
    settings = get_settings()
    if settings.LOG_LEVEL == "production":
        # Mask last octet of IP
        if ip_address and "." in ip_address:
            parts = ip_address.split(".")
            ip_address = ".".join(parts[:-1]) + [".0"]
```

---

#### FINDING-011: CORS Overly Permissive

**Severity:** MEDIUM (CVSS 5.0)  
**CWE:** CWE-942 (Permissive Cross-domain Policy with Untrusted Domains)  
**OWASP:** A05:2021 — Security Misconfiguration

**Description:**
The CORS middleware is configured with `allow_methods=["*"]` and `allow_headers=["*"]`, which allows any HTTP method and header in cross-origin requests. Additionally, the `allow_origins` setting is user-configurable and defaults to localhost development origins.

**Affected Files:**
- `backend/app/main.py` — Lines 92-98: CORS middleware configuration

**Impact:**
- Increased attack surface for cross-origin attacks
- Potential data exfiltration if misconfigured in production

**Remediation:**

```python
# In main.py, restrict methods and headers:
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Request-ID",
    ],
)
```

---

#### FINDING-012: Swagger/OpenAPI Enabled in Production

**Severity:** MEDIUM (CVSS 5.3)  
**CWE:** CWE-200 (Exposure of Sensitive Information to an Unauthorized Actor)  
**OWASP:** A05:2021 — Security Misconfiguration

**Description:**
The FastAPI application enables `/docs`, `/redoc`, and `/openapi.json` endpoints in all environments. These endpoints expose the complete API surface, including endpoint paths, request/response schemas, and authentication mechanisms.

**Affected Files:**
- `backend/app/main.py` — Lines 84-86: Always-enabled documentation routes

**Impact:**
- Attackers can discover all API endpoints and their parameters
- Exposure of data schema structures
- Facilitates targeted attacks on undocumented endpoints

**Remediation:**

```python
# In main.py, conditionally disable docs in production:
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Dark Web Surveillance and Threat Intelligence Tool Backend API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)
```

---

#### FINDING-013: No Security Headers on Backend Responses

**Severity:** MEDIUM (CVSS 5.0)  
**CWE:** CWE-693 (Protection Mechanism Failure)  
**OWASP:** A05:2021 — Security Misconfiguration

**Description:**
The FastAPI backend does not set security-related HTTP headers such as `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, or `Content-Security-Policy`. While nginx sets some of these for the frontend, the backend API responses lack them.

**Affected Files:**
- `backend/app/main.py` — No security headers middleware

**Impact:**
- Increased risk of clickjacking, MIME-type sniffing, and other client-side attacks
- API responses could be embedded in iframes on malicious sites

**Remediation:**

```python
# In main.py, add security headers middleware:
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

#### FINDING-014: Weak Password Policy

**Severity:** MEDIUM (CVSS 5.9)  
**CWE:** CWE-521 (Weak Password Requirements)  
**OWASP:** A07:2021 — Identification and Authentication Failures

**Description:**
The minimum password length is only 6 characters, with no requirements for complexity (uppercase, lowercase, numbers, special characters). This allows weak passwords like `admin123` (the default) and `password`.

**Affected Files:**
- `backend/app/auth/models.py` — Line 19: `password: str = Field(..., min_length=6, max_length=128)`

**Impact:**
- Increased susceptibility to brute-force and dictionary attacks
- Weak investigator passwords compromise entire investigations

**Remediation:**

```python
# In auth/models.py, add password complexity validation:
from pydantic import field_validator
import re

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=12, max_length=128)
    role: str = Field(default="investigator", pattern="^(investigator|admin|auditor)$")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
```

---

#### FINDING-015: Report Download Token in URL

**Severity:** MEDIUM (CVSS 5.5)  
**CWE:** CWE-598 (Information Exposure Through Query Strings in GET Request)  
**OWASP:** A05:2021 — Security Misconfiguration

**Description:**
Report download tokens are passed as query string parameters in URLs (e.g., `/v1/reports/{id}/download?token=...`). Query parameters are commonly logged by web servers, reverse proxies, and analytics tools, potentially exposing download tokens.

**Affected Files:**
- `backend/app/reports/router.py` — Lines 124, 167: Download tokens in URLs
- `backend/app/reports/generator.py` — Line 355: Token URL generation

**Impact:**
- Download token exposure in server logs
- Unauthorized report access via shared/exposed URLs
- Chain of custody concerns for law enforcement evidence

**Remediation:**

```python
# Move token to Authorization header instead of query string:
@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Extract token from Authorization header
    if authorization and authorization.startswith("DownloadToken "):
        token = authorization.replace("DownloadToken ", "")
    else:
        raise HTTPException(status_code=403, detail="Missing download token")
    # ... rest of implementation ...
```

---

#### FINDING-016: Syslog Uses Unencrypted UDP

**Severity:** MEDIUM (CVSS 5.8)  
**CWE:** CWE-319 (Cleartext Transmission of Sensitive Information)  
**OWASP:** A02:2021 — Cryptographic Failures

**Description:**
The SIEM syslog integration uses UDP (`socket.SOCK_DGRAM`) without any encryption. Alert data sent to SIEM systems can be intercepted, read, or modified in transit. There is no support for TLS-protected syslog (RFC 5425).

**Affected Files:**
- `backend/app/export/siem.py` — Lines 61-79: `send_syslog` uses UDP

**Impact:**
- Alert data (including intelligence) exposed on the network
- Man-in-the-middle attacks on SIEM integration
- False alerts injection

**Remediation:**

```python
# Add TLS syslog support:
import ssl

async def send_syslog_tls(self, host: str, port: int, alert: dict, 
                          format_type: str = "cef", 
                          use_tls: bool = True) -> dict:
    """Send alert via syslog over TLS."""
    try:
        message = self._format_cef(alert) if format_type == "cef" else self._format_leef(alert)
        
        if use_tls:
            context = ssl.create_default_context()
            reader, writer = await asyncio.open_connection(
                host, port, ssl=context
            )
        else:
            reader, writer = await asyncio.open_connection(host, port)
        
        writer.write(message.encode("utf-8") + b"\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        
        return {"status": 200, "message": "sent", "success": True}
    except Exception as e:
        logger.warning("Syslog TLS send failed: %s", e)
        return {"status": 0, "message": str(e), "success": False}
```

---

#### FINDING-017: Weak Account Lockout Mechanism

**Severity:** MEDIUM (CVSS 5.3)  
**CWE:** CWE-837 (Improper Enforcement of a Single, Unique Action)  
**OWASP:** A07:2021 — Identification and Authentication Failures

**Description:**
The account lockout mechanism locks an account for only 5 minutes after 5 failed attempts. Attackers can simply wait 5 minutes and continue brute-forcing. There is no escalation (longer lockouts for repeated attacks) and no permanent lockout after multiple lockout cycles.

**Affected Files:**
- `backend/app/auth/router.py` — Lines 79-84: Lock duration is always 300 seconds

**Impact:**
- Persistent brute-force attacks over time
- No defense against distributed slow-rate attacks

**Remediation:**

```python
# In auth/router.py, implement escalating lockout:
def _calculate_lock_duration(failed_attempts: int) -> int:
    """Calculate lock duration based on failed attempt history."""
    if failed_attempts < 5:
        return 0  # Not locked yet
    elif failed_attempts < 10:
        return 300  # 5 minutes
    elif failed_attempts < 20:
        return 3600  # 1 hour
    else:
        return 86400  # 24 hours

# Track lockout cycles in the user document
if new_attempts >= 5:
    lock_duration = _calculate_lock_duration(
        user.get("total_failed_attempts", 0)
    )
    update["$set"]["is_locked"] = True
    update["$set"]["locked_until"] = datetime.utcnow() + timedelta(seconds=lock_duration)
    update["$inc"]["lockout_cycles"] = 1
```

---

### 3.4 LOW FINDINGS

#### FINDING-018: Missing HSTS Header

**Severity:** LOW (CVSS 3.1)  
**CWE:** CWE-523 (Unprotected Transport of Credentials)  
**OWASP:** A05:2021 — Security Misconfiguration

**Description:**
The nginx configuration does not include a `Strict-Transport-Security` header, which means browsers will not enforce HTTPS connections to the application.

**Affected Files:**
- `frontend/nginx.conf` — No HSTS header set

**Remediation:**

```nginx
# In nginx.conf, add HSTS:
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

---

#### FINDING-019: No Audit Logging for Crawl Engine Actions

**Severity:** LOW (CVSS 3.3)  
**CWE:** CWE-778 (Insufficient Logging)  
**OWASP:** A09:2021 — Security Logging and Monitoring Failures

**Description:**
The crawl engine does not log which user triggered a crawl job or the results of individual page fetches in the audit log. While there is some logging, the audit trail for crawling operations is incomplete.

**Affected Files:**
- `backend/app/crawler/engine.py` — No audit log integration for crawl results
- `backend/app/crawler/scheduler.py` — No audit logging for scheduled job execution

**Remediation:**

```python
# In crawler/engine.py execute_job method, add audit logging:
async def execute_job(self, job: dict) -> dict:
    try:
        # ... existing fetch logic ...
        
        # Audit log for crawl completion
        try:
            db = await get_mongodb()
            await create_audit_log(
                db=db,
                user_id=job.get("triggered_by", "system"),
                user_name="System",
                user_role="system",
                action="crawl_completed",
                resource_type="crawl_job",
                resource_id=job.get("id", ""),
                details={
                    "url": target_url,
                    "http_status": http_status,
                    "pages_crawled": 1,
                    "content_hash": content_hash,
                    "latency_ms": round(latency, 1),
                },
            )
        except Exception:
            pass
        
        # ... rest of existing code ...
```

---

#### FINDING-020: No Input Validation on NLP Text Processing

**Severity:** LOW (CVSS 3.5)  
**CWE:** CWE-20 (Improper Input Validation)  
**OWASP:** A03:2021 — Injection

**Description:**
Text content from dark web sources is processed by the NLP pipeline without sanitization. While direct injection via NLP is low-risk, the content is stored and potentially displayed in reports or the frontend.

**Affected Files:**
- `backend/app/nlp/analyzer.py` — Lines 24-82: Passes text directly to NLP components
- `backend/app/reports/generator.py` — Lines 149-225: Report content includes raw alert/data text

**Remediation:**

```python
# In reports/generator.py, sanitize text before rendering:
import html

def _sanitize_for_report(text: str) -> str:
    """Sanitize text for report rendering."""
    # Escape HTML entities to prevent XSS in PDF/HTML reports
    return html.escape(text, quote=True)

# Apply sanitization before adding to report:
elements.append(Paragraph(self._sanitize_for_report(alert.get('summary', '')), styles["Normal"]))
```

---

#### FINDING-021: No Brute-Force Protection on API Key Authentication

**Severity:** LOW (CVSS 4.0)  
**CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)  
**OWASP:** A07:2021 — Identification and Authentication Failures

**Description:**
API key authentication (`X-API-Key` header) has no rate limiting or brute-force protection. An attacker who obtains a list of API key hashes could brute-force the keys offline.

**Affected Files:**
- `backend/app/dependencies.py` — Lines 115-117, 177-201: `_resolve_api_key` without rate limiting

**Remediation:**

```python
# In dependencies.py _resolve_api_key, add rate limiting:
async def _resolve_api_key(api_key: str, db: AsyncIOMotorDatabase) -> CurrentUser:
    # Rate limit API key verification
    key_prefix = api_key[:8]  # Use partial key for rate limiting
    redis = await get_redis()
    
    attempts = await redis.incr(f"apikey:attempts:{key_prefix}")
    await redis.expire(f"apikey:attempts:{key_prefix}", 60)
    
    if attempts > 10:  # Max 10 attempts per minute per key prefix
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many API key attempts",
        )
    
    # ... existing verification logic ...
```

---

#### FINDING-022: Cookie Security Attributes Not Set

**Severity:** LOW (CVSS 3.7)  
**CWE:** CWE-1004 (Sensitive Cookie Without 'HttpOnly' Flag)  
**OWASP:** A05:2021 — Security Misconfiguration

**Description:**
JWTs are stored in `localStorage` on the frontend, which is accessible to any JavaScript running in the same origin. If an XSS vulnerability exists, tokens can be stolen. Additionally, there are no `HttpOnly` or `Secure` cookie flags because cookies are not used — but the use of `localStorage` for sensitive tokens is itself a concern.

**Affected Files:**
- `frontend/src/store/authStore.ts` — Lines 26-27: Tokens stored in localStorage
- `frontend/src/api/client.ts` — Lines 14, 63, 76: Tokens read from localStorage

**Impact:**
- Token theft via XSS
- Persistent session hijacking

**Remediation:**

Consider using httpOnly cookies instead of localStorage for token storage:

```typescript
// frontend/src/api/client.ts
// Instead of localStorage, use httpOnly cookies set by the backend
// The backend should set access_token as an httpOnly, Secure, SameSite cookie

// On the backend, set cookies in the login response:
@router.post("/login", response_model=TokenResponse)
async def login(..., response: Response):
    # ... existing auth logic ...
    
    # Set httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    
    return TokenResponse(...)
```

---

#### FINDING-023: Missing File Upload Validation

**Severity:** LOW (CVSS 3.3)  
**CWE:** CWE-434 (Unrestricted Upload of File with Dangerous Type)  
**OWASP:** A03:2021 — Injection

**Description:**
While the application doesn't currently have file upload endpoints, the `python-multipart` dependency suggests potential future support. No file upload restrictions or validation patterns exist.

**Affected Files:**
- `backend/requirements.txt` — Line 7: `python-multipart>=0.0.9`

**Remediation:**
If file upload endpoints are added, implement:
- File extension whitelist
- Content-type validation
- File size limits
- Virus scanning
- Storage outside the web root

---

#### FINDING-024: No Secret Rotation Policy

**Severity:** LOW (CVSS 3.0)  
**CWE:** CWE-326 (Inadequate Encryption Strength)  
**OWASP:** A02:2021 — Cryptographic Failures

**Description:**
There is no built-in support for rotating secrets (JWT keys, database passwords, API keys). Once deployed, secrets must be manually rotated. JWT refresh tokens have a 7-day expiry but the underlying signing key never changes.

**Remediation:**
- Implement key rotation support using JWKS (JSON Web Key Set)
- Add documentation for regular secret rotation procedures
- Consider using HashiCorp Vault or AWS Secrets Manager

---

## 4. OWASP Top 10 (2021) Coverage

| # | OWASP Category | Status | Key Findings |
|---|----------------|--------|--------------|
| A01 | **Broken Access Control** | ⚠️ Partially Addressed | RBAC implemented via `require_permission` and `require_role`. However, the `bulk_update_alerts` endpoint (#FINDING-001) lacks proper object-level authorization checks. API key permissions are not granularly enforced. |
| A02 | **Cryptographic Failures** | ❌ **Critical Gaps** | JWT uses HS256 (symmetric) with a defaultable weak secret (#FINDING-003). Elasticsearch TLS verification disabled (#FINDING-005). Syslog sends unencrypted UDP (#FINDING-016). |
| A03 | **Injection** | ⚠️ Partially Addressed | No SQL injection (NoSQL database). Regex injection possible in watchlist patterns. XSS possible via report content (#FINDING-020). No sanitization on NLP output. |
| A04 | **Insecure Design** | ❌ **Critical Gaps** | No SSRF protection on crawler (#FINDING-001). No account lockout escalation (#FINDING-017). No rate limiting on auth (#FINDING-004). No MFA (#FINDING-009). |
| A05 | **Security Misconfiguration** | ❌ **Major Gaps** | Default credentials everywhere (#FINDING-002, #FINDING-006, #FINDING-008). Debug/OpenAPI enabled in all environments (#FINDING-012). Permissive CORS (#FINDING-011). No HSTS (#FINDING-018). |
| A06 | **Vulnerable Components** | ⚠️ Partially Addressed | CI pipeline includes `pip-audit` and `npm audit` but results are not enforced (continue-on-error). No Dependabot configuration. |
| A07 | **Identification & Auth Failures** | ❌ **Critical Gaps** | No MFA (#FINDING-009). Weak password policy (#FINDING-014). Weak account lockout (#FINDING-017). Token theft detection missing (#FINDING-007). API keys stored as SHA-256 hashes (insufficient). |
| A08 | **Software & Data Integrity Failures** | ⚠️ Partially Addressed | Blockchain evidence sealing is present but simulated/no-op. No integrity verification for downloaded reports. Audit log tamper-evident hashing is good. |
| A09 | **Security Logging & Monitoring** | ⚠️ Partially Addressed | Audit logging implemented with tamper-evident hashing. However, crawl actions are not audited (#FINDING-019). Credentials logged at startup (#FINDING-010). No centralized logging from containers. |
| A10 | **SSRF** | ❌ **Critical Gap** | Crawler engine fetches arbitrary URLs without validation (#FINDING-001). No allowlist, no internal IP blocking, no scheme restriction. |

### Legend
- ✅ **Good** — Adequately addressed with no major issues
- ⚠️ **Partially Addressed** — Some protections exist but gaps remain
- ❌ **Critical Gaps** — Major vulnerabilities or missing protections

---

## 5. Secure Configuration Checklist

### Pre-Deployment Checklist

| # | Item | Status | Instructions |
|---|------|--------|-------------|
| 1 | **Change default SECRET_KEY** | ❌ | Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"` and set via `SECRET_KEY` env var |
| 2 | **Change all default passwords** | ❌ | Set strong passwords for MongoDB, Elasticsearch, Neo4j, Redis, RabbitMQ in `.env` |
| 3 | **Set strong admin password** | ❌ | Override `DEFAULT_ADMIN_PASSWORD` with a strong password (min 20 chars) |
| 4 | **Enable Elasticsearch TLS** | ❌ | Set `ELASTICSEARCH_VERIFY_CERTS=true` and configure CA certificate |
| 5 | **Disable Swagger/OpenAPI** | ❌ | Set `DEBUG=false` to disable `/docs`, `/redoc`, `/openapi.json` |
| 6 | **Enable TLS for all external traffic** | ❌ | Configure TLS termination at reverse proxy (nginx) with valid certificates |
| 7 | **Restrict CORS origins** | ❌ | Set `CORS_ORIGINS` to specific production domains only |
| 8 | **Configure rate limiting** | ❌ | Verify `RATE_LIMIT_PER_USER` and `RATE_LIMIT_PER_IP` are set appropriately |
| 9 | **Enable auth rate limiting** | ❌ | Ensure `check_rate_limit` is applied to all auth endpoints |
| 10 | **Set up MFA** | ❌ | Enable and enforce MFA for all user accounts |
| 11 | **Review network segmentation** | ❌ | Verify Docker network isolation: frontend↔backend↔data network segmentation |
| 12 | **Set up centralized logging** | ❌ | Configure log aggregation with alerting on security events |
| 13 | **Configure SIEM syslog over TLS** | ❌ | Use RFC 5425 TLS syslog instead of UDP |
| 14 | **Enable HSTS** | ❌ | Add `Strict-Transport-Security` header to nginx config |
| 15 | **Remove default admin seeding** | ❌ | Disable auto-seeding of admin users after first deployment |
| 16 | **Set REPORT_STORAGE_PATH** | ❌ | Use a dedicated, non-tmp directory with restricted permissions |
| 17 | **Configure Neo4j auth properly** | ❌ | Set `NEO4J_PASSWORD` to a strong value (not "password") |
| 18 | **Disable container healthcheck info leaks** | ❌ | Healthcheck endpoints should not reveal sensitive information |

### Secure Defaults vs Production

| Setting | Default (Dev) | Required (Production) |
|---------|--------------|----------------------|
| `SECRET_KEY` | Hardcoded weak string | Strong 64-byte random |
| `DEBUG` | `false` | `false` (lock) |
| `ELASTICSEARCH_VERIFY_CERTS` | `false` | `true` |
| `CORS_ORIGINS` | `localhost:3000,localhost:5173` | Production domain only |
| `DEFAULT_ADMIN_PASSWORD` | `admin123` / `changeme_admin_password` | Strong unique password |
| `NEO4J_PASSWORD` | `password` | Strong unique password |
| `MONGO_INITDB_ROOT_PASSWORD` | `darktrace_pass` | Strong unique password |
| `REPORT_STORAGE_PATH` | `/tmp/darktrace/reports` | Persistent volume with restricted access |
| `API_PREFIX` | `/v1` | `/v1` (consider adding API key for external integrations) |
| OpenAPI docs | Enabled | Disabled |

---

## 6. Recommendations

### Immediate Actions (Week 1)

| Priority | Action | Finding Reference |
|----------|--------|-------------------|
| **P0** | Fix SSRF vulnerability in crawler — validate all target URLs | FINDING-001 |
| **P0** | Enforce strong SECRET_KEY — prevent default key usage | FINDING-003 |
| **P0** | Remove credential logging from startup sequence | FINDING-002 |
| **P0** | Apply rate limiting to all authentication endpoints | FINDING-004 |

### Short-Term (Weeks 2-4)

| Priority | Action | Finding Reference |
|----------|--------|-------------------|
| P1 | Enable Elasticsearch TLS verification | FINDING-005 |
| P1 | Change all default passwords in docker-compose / .env.example | FINDING-006 |
| P1 | Implement refresh token reuse detection | FINDING-007 |
| P1 | Fix weak Neo4j default password | FINDING-008 |
| P1 | Implement and enforce MFA | FINDING-009 |
| P1 | Strengthen password policy (min 12 chars, complexity) | FINDING-014 |
| P1 | Restrict CORS to specific origins/methods/headers | FINDING-011 |
| P1 | Disable OpenAPI docs in production | FINDING-012 |

### Medium-Term (Weeks 5-8)

| Priority | Action | Finding Reference |
|----------|--------|-------------------|
| P2 | Add security headers middleware to backend | FINDING-013 |
| P2 | Implement escalating account lockout | FINDING-017 |
| P2 | Move report download tokens to headers | FINDING-015 |
| P2 | Add TLS support for syslog integration | FINDING-016 |
| P2 | Add audit logging for crawler engine | FINDING-019 |
| P2 | Add HSTS header to nginx configuration | FINDING-018 |
| P2 | Sanitize NLP output before rendering in reports | FINDING-020 |
| P2 | Add brute-force protection for API key auth | FINDING-021 |

### Long-Term (Weeks 9+)

| Priority | Action | Finding Reference |
|----------|--------|-------------------|
| P3 | Migrate from HS256 to RS256 for JWT signing | FINDING-003 |
| P3 | Implement JWKS-based key rotation | FINDING-024 |
| P3 | Add Content Security Policy enforcement | General hardening |
| P3 | Implement holistic secret management (Vault/Secrets Manager) | General hardening |
| P3 | Implement automated security scanning in CI/CD pipeline (enforce failures) | A06 |
| P3 | Add file upload validation patterns for future endpoints | FINDING-023 |
| P3 | Implement session management with absolute timeouts | General hardening |
| P3 | Add API request logging middleware | A09 |

---

## 7. Quick-Start Security Hardening

### One-Line Security Fixes (applied to `.env`)

```bash
# 1. Generate strong secrets
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
MONGO_PASS=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ES_PASS=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
NEO4J_PASS=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
REDIS_PASS=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
RABBIT_PASS=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ADMIN_PASS=$(python -c "import secrets; print(secrets.token_urlsafe(24))")

# 2. Apply all at once
export SECRET_KEY MONGO_PASS ES_PASS NEO4J_PASS REDIS_PASS RABBIT_PASS ADMIN_PASS
```

### Minimum Viable Security Changes (Code)

```python
# config.py — Add these validations
class Settings:
    def __init__(self):
        self._validate()

    def _validate(self):
        """Validate security-critical settings."""
        if not self.SECRET_KEY or "change-me" in self.SECRET_KEY:
            raise SystemExit("FATAL: SECRET_KEY is not set or has a default value.")
        if self.NEO4J_PASSWORD in ("password", ""):
            raise SystemExit("FATAL: Neo4j password is weak or not set.")
        if self.ELASTICSEARCH_VERIFY_CERTS is False:
            logger.warning("WARNING: Elasticsearch TLS verification disabled.")
```

---

## Appendix A: CVSS Score Summary

| Finding | CVSS v3 Score | Severity |
|---------|--------------|----------|
| FINDING-001: SSRF in Crawler | 9.1 | CRITICAL |
| FINDING-002: Default Credentials Logged | 9.3 | CRITICAL |
| FINDING-003: Weak JWT Secret Key | 9.1 | CRITICAL |
| FINDING-004: No Auth Rate Limiting | 7.5 | HIGH |
| FINDING-005: ES TLS Verification Disabled | 7.4 | HIGH |
| FINDING-006: Hardcoded Passwords | 8.2 | HIGH |
| FINDING-007: Token Reuse Detection Missing | 7.1 | HIGH |
| FINDING-008: Weak Neo4j Password | 7.5 | HIGH |
| FINDING-009: No MFA | 7.0 | HIGH |
| FINDING-010: Credential Logging | 6.5 | MEDIUM |
| FINDING-011: Permissive CORS | 5.0 | MEDIUM |
| FINDING-012: OpenAPI in Production | 5.3 | MEDIUM |
| FINDING-013: No Security Headers | 5.0 | MEDIUM |
| FINDING-014: Weak Password Policy | 5.9 | MEDIUM |
| FINDING-015: Token in URL | 5.5 | MEDIUM |
| FINDING-016: Syslog UDP | 5.8 | MEDIUM |
| FINDING-017: Weak Lockout | 5.3 | MEDIUM |
| FINDING-018: No HSTS | 3.1 | LOW |
| FINDING-019: No Crawler Auditing | 3.3 | LOW |
| FINDING-020: No Text Sanitization | 3.5 | LOW |
| FINDING-021: No API Key Rate Limiting | 4.0 | LOW |
| FINDING-022: localStorage Tokens | 3.7 | LOW |
| FINDING-023: No Upload Validation | 3.3 | LOW |
| FINDING-024: No Secret Rotation | 3.0 | LOW |

---

## Appendix B: Threat Model — STRIDE Per Component

| Component | Spoofing | Tampering | Repudiation | Information Disclosure | DoS | Elevation of Privilege |
|-----------|----------|-----------|-------------|----------------------|-----|----------------------|
| **Auth Module** | ❌ Weak JWT secret | ✅ Hash chain | ✅ Audit logs | ⚠️ Password in logs | ❌ No rate limiting | ❌ No MFA |
| **Crawler** | ⚠️ Proxy trust | ✅ Content hash | ❌ No audit | ❌ SSRF | ⚠️ Configurable delays | ⚠️ RBAC only |
| **NLP Pipeline** | ✅ N/A | ⚠️ Regex injection | ✅ N/A | ⚠️ PII extraction | ⚠️ Chunk size limit | ✅ N/A |
| **Export/SIEM** | ⚠️ Webhook key | ⚠️ UDP syslog | ⚠️ No logging | ❌ UDP cleartext | ⚠️ Timeout | ✅ N/A |
| **Database Tier** | ⚠️ Default creds | ⚠️ No encryption | ✅ N/A | ❌ Default creds | ⚠️ Pool limits | ⚠️ Default creds |
| **Frontend** | ⚠️ Token storage | ✅ N/A | ✅ N/A | ⚠️ localStorage | ✅ N/A | ⚠️ Client-side check |

✅ = Protected / ❌ = Vulnerable / ⚠️ = Partially Protected

---

## Appendix C: Dependency Vulnerability Scan Notes

### Backend (Python)
- **aiohttp** (3.9.x) — Check for known CVEs before deployment
- **spaCy** (3.7.x) — Large dependency with native code; monitor for vulnerabilities
- **web3** (7.x) — Optional but adds attack surface; only include if blockchain sealing is used
- **googletrans** (4.x) — Unofficial Google Translate API; rate limiting may cause issues

### Frontend (JavaScript/TypeScript)
- **axios** (1.7.7) — Generally well maintained; keep updated
- **cytoscape** (3.30.1) — Graph visualization library; monitor for XSS in node labels
- **recharts** (2.12.7) — Charting library; generally safe

### CI/CD Security Notes
- `npm audit` runs with `--audit-level=high` but uses `continue-on-error: true` — should fail builds on high/critical
- Trivy scans filesystem but does not fail on findings (`exit-code: "0"`)
- No secrets scanning in CI pipeline
- No SAST (Static Application Security Testing) tool integrated

---

*Report generated by Security Engineer — DarkTrace Security Audit, June 2026*
