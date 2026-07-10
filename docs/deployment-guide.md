# DarkTrace — Deployment Guide

> **Version:** 1.0 | **Last Updated:** 2026-06-03

---

## 1. Prerequisites

### Hardware Requirements
| Environment | CPU | RAM | Storage | Network |
|-------------|-----|-----|---------|---------|
| **Development** | 4 cores | 8 GB | 20 GB SSD | Internet |
| **Production (min)** | 8 cores | 16 GB | 100 GB SSD | 100 Mbps |
| **Production (rec)** | 16 cores | 32 GB | 500 GB SSD | 1 Gbps |

### Software Requirements
- Docker Engine 24+ & Docker Compose v2+
- Git 2.40+
- For development: Python 3.11+, Node.js 20+

---

## 2. Environment Configuration

### Quick Start
```bash
cp .env.example .env
# Edit .env with strong passwords and secrets
```

### Key Configuration Variables

| Variable | Description | Default | Required Change |
|----------|-------------|---------|-----------------|
| `SECRET_KEY` | JWT signing secret | `change-me-...` | **YES** — Use 64+ char random |
| `MONGODB_URI` | MongoDB connection string | `mongodb://mongodb:27017` | For external DB |
| `ELASTICSEARCH_HOSTS` | ES connection string | `http://elasticsearch:9200` | For external ES |
| `ELASTICSEARCH_USERNAME` | ES username | `elastic` | **YES** — Change default |
| `ELASTICSEARCH_PASSWORD` | ES password | `changeme` | **YES** — Strong password |
| `NEO4J_URI` | Neo4j bolt URI | `bolt://neo4j:7687` | For external Neo4j |
| `NEO4J_PASSWORD` | Neo4j password | `password` | **YES** — Strong password |
| `REDIS_URI` | Redis connection | `redis://redis:6379` | For external Redis |
| `DEFAULT_ADMIN_EMAIL` | Initial admin email | `admin@darktrace.local` | **YES** — Change email |
| `DEFAULT_ADMIN_PASSWORD` | Initial admin password | `admin123` | **YES** — Strong password |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` | Add your domain |
| `RATE_LIMIT_PER_USER` | Max requests per user/min | `100` | Adjust as needed |

---

## 3. Production Deployment

### 3.1 Basic Deployment (Docker Compose)

```bash
# 1. Clone and configure
git clone <repo-url> darktrace
cd darktrace
cp .env.example .env
# Edit .env with production values

# 2. Start services
docker compose up -d

# 3. Verify all services healthy
docker compose ps
# NAME                 SERVICE              STATUS
# darktrace-backend    backend              healthy
# darktrace-frontend   frontend             healthy
# darktrace-mongodb    mongodb              healthy
# darktrace-elasticsearch elasticsearch     healthy
# darktrace-neo4j      neo4j                healthy
# darktrace-redis      redis                healthy
# darktrace-rabbitmq   rabbitmq             healthy
```

### 3.2 High-Availability Deployment (Kubernetes)

For production-scale deployments, use Kubernetes. Key considerations:

1. **StatefulSets** for MongoDB, Elasticsearch, Neo4j (with persistent volumes)
2. **Deployments** for stateless services (backend, frontend, crawler-worker, nlp-worker)
3. **Horizontal Pod Autoscaler** for backend, crawler, NLP services
4. **Ingress** with TLS termination (Let's Encrypt)
5. **Service Mesh** (Istio/Linkerd) for mTLS and traffic management

### 3.3 External Database Configuration

For production, use managed database services:

```yaml
# docker-compose.override.yml (production)
services:
  backend:
    environment:
      MONGODB_URI: "mongodb+srv://user:pass@cluster.mongodb.net/darktrace"
      ELASTICSEARCH_HOSTS: "https://es-endpoint:9200"
      ELASTICSEARCH_USERNAME: "darktrace"
      ELASTICSEARCH_PASSWORD: "${ES_PASSWORD}"
      NEO4J_URI: "bolt://neo4j-endpoint:7687"
      NEO4J_PASSWORD: "${NEO4J_PASSWORD}"
      REDIS_URI: "rediss://user:pass@redis-endpoint:6379"
```

---

## 4. Security Hardening Checklist

- [ ] Change ALL default passwords in `.env`
- [ ] Generate strong `SECRET_KEY` (64+ random characters)
- [ ] Enable TLS/HTTPS (use reverse proxy like nginx + Let's Encrypt)
- [ ] Restrict CORS origins to your domain only
- [ ] Configure rate limiting (adjust thresholds)
- [ ] Enable audit logging
- [ ] Set up WAF (Cloudflare, AWS WAF, or ModSecurity)
- [ ] Configure network segmentation (frontend/backend/data VLANs)
- [ ] Enable MongoDB/Elasticsearch/Neo4j authentication
- [ ] Use Redis with password authentication
- [ ] Implement backup strategy for all databases
- [ ] Set up log monitoring and alerting (fail2ban, SIEM)
- [ ] Regular security updates (Docker images, dependencies)

---

## 5. Scaling Considerations

### Horizontal Scaling
| Service | Scaling Strategy | Notes |
|---------|-----------------|-------|
| **Backend API** | Multiple replicas behind load balancer | Stateless, scales linearly |
| **Crawler Worker** | Increase worker count | Each worker uses different proxy |
| **NLP Worker** | GPU-enabled instances | For production NLP throughput |
| **Frontend** | CDN (Cloudflare, AWS CloudFront) | Static assets, edge caching |

### Vertical Scaling
| Service | Bottleneck | Upgrade Path |
|---------|------------|-------------|
| **MongoDB** | I/O, memory | SSD, more RAM |
| **Elasticsearch** | Memory, CPU | Increase heap, more shards |
| **Neo4j** | Memory | Increase heap for graph workloads |
| **Redis** | Memory | More RAM, cluster mode |

---

## 6. Backup & Restore

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh — Run daily via cron
BACKUP_DIR="/backups/darktrace"
DATE=$(date +%Y%m%d)

# MongoDB
docker exec darktrace-mongodb mongodump \
  --uri="mongodb://localhost:27017" \
  --out="$BACKUP_DIR/mongodb/$DATE"

# Elasticsearch
docker exec darktrace-elasticsearch elasticdump \
  --input=http://localhost:9200 \
  --output=$BACKUP_DIR/es/$DATE/index.json

# Neo4j
docker exec darktrace-neo4j neo4j-admin dump \
  --database=neo4j \
  --to="$BACKUP_DIR/neo4j/$DATE.dump"
```

### Restore
```bash
# MongoDB
docker exec -i darktrace-mongodb mongorestore \
  --uri="mongodb://localhost:27017" \
  /backup/path

# Elasticsearch (recreate indices from dump)
curl -X POST "localhost:9200/_bulk" \
  -H "Content-Type: application/x-ndjson" \
  --data-binary @backup.ndjson
```

---

## 7. Monitoring Setup

### Prometheus + Grafana
Pre-configured dashboards are in `monitoring/`:
- `prometheus.yml` — Scrape configuration for all services
- `grafana-datasources.yml` — Auto-provisioned datasources
- `grafana-dashboards/darktrace-overview.json` — 9-panel overview dashboard

### Key Metrics to Monitor
| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| CPU usage > 80% | Warning | Scale horizontally |
| Memory usage > 85% | Critical | Increase resources |
| Crawl job failure rate > 5% | Warning | Check proxy pool |
| Alert processing latency > 30s | Critical | Scale NLP workers |
| Queue depth > 1000 | Warning | Increase consumer count |
| API error rate > 1% | Critical | Check backend logs |

### Logging
- All services log in JSON format
- Logs collected via Fluentd → Elasticsearch → Kibana
- Application logs include request IDs for tracing

---

## 8. Troubleshooting

### Common Issues

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| Backend won't start | MongoDB not ready | Check `depends_on` health checks |
| Crawler fails to connect | Tor proxy not running | Check `docker logs darktrace-crawler` |
| Elasticsearch crashes | Insufficient memory | Increase `ES_JAVA_OPTS` |
| Frontend shows blank page | API unavailable | Check backend health `/health` |
| Alerts not firing | RabbitMQ not connected | Check `docker logs darktrace-rabbitmq` |
| Slow search queries | ES index not optimized | Run force merge on indices |

### Diagnostic Commands
```bash
# Check service logs
docker compose logs -f backend
docker compose logs -f crawler-worker
docker compose logs -f nlp-worker

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/v1/admin/health

# Check database connectivity
docker exec darktrace-mongodb mongosh --eval "db.runCommand({ping:1})"
docker exec darktrace-elasticsearch curl -s localhost:9200
docker exec darktrace-redis redis-cli ping

# Check queue status
docker exec darktrace-rabbitmq rabbitmqctl list_queues
```

---

## 9. CI/CD Pipeline

### GitHub Actions
Two workflows are pre-configured:

**CI Pipeline** (`.github/workflows/ci.yml`):
- Trigger: Push to main, Pull Requests
- Jobs: Lint → Test → Build → Security Scan

**Deploy Pipeline** (`.github/workflows/deploy.yml`):
- Trigger: Push to main (after CI)
- Stages: Build & Push → Staging → Smoke Tests → Production (manual approval)

### Required Secrets
| Secret Name | Description |
|-------------|-------------|
| `DOCKER_REGISTRY` | Container registry URL |
| `DOCKER_USERNAME` | Registry username |
| `DOCKER_PASSWORD` | Registry password/token |
| `STAGING_SSH_KEY` | SSH key for staging server |
| `PRODUCTION_SSH_KEY` | SSH key for production server |

---

## 10. Maintenance

### Daily
- Check service health (`docker compose ps`)
- Review new alerts in dashboard
- Check crawl job success rates

### Weekly
- Review audit logs for suspicious activity
- Update watchlists with new threat intelligence
- Check disk usage on data volumes

### Monthly
- Apply security patches to host OS
- Update Docker images (`docker compose pull`)
- Review and rotate secrets/passwords
- Test backup restoration
- Performance review and capacity planning
