# =============================================================================
# DarkTrace Backend — Multi-stage Dockerfile
# =============================================================================
# Stage 1: Build dependencies (heavy pip installs, system compilation)
# Stage 2: Slim runtime (no compilers, no build tools)
# =============================================================================

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages into /install (isolated from runtime)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Download spaCy models into /install
RUN pip install --no-cache-dir --prefix=/install spacy
RUN /install/bin/python -m spacy download en_core_web_trf
RUN /install/bin/python -m spacy download en_core_web_lg

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd -r darktrace && useradd -r -g darktrace -d /app -s /sbin/nologin darktrace

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create directories with proper ownership
RUN mkdir -p /app/models /tmp/darktrace/reports \
    && chown -R darktrace:darktrace /app \
    && chown -R darktrace:darktrace /tmp/darktrace/reports

# Switch to non-root user
USER darktrace

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with startup script (seeds database then starts uvicorn)
CMD ["bash", "scripts/startup.sh"]
