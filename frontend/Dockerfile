# =============================================================================
# DarkTrace Frontend Dockerfile
# Multi-stage build with nginx:alpine serving optimized SPA
# =============================================================================

# ─── Stage 1: Build Application ──────────────────────────────────────────────
FROM node:20-alpine AS builder

# Build-time argument for API base URL (defaults to /v1 for dev, /api/v1 in production Docker)
ARG VITE_API_BASE_URL=/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Set working directory
WORKDIR /build

# Copy package files first for layer caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies (including devDependencies for build)
RUN npm ci --no-audit --no-fund

# Copy source code
COPY frontend/ ./

# Build the application
RUN npm run build

# ─── Stage 2: Production Runtime ─────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Security: remove default nginx artifacts
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf && \
    # Create non-root user (nginx already has one, but ensure proper permissions)
    chown -R nginx:nginx /var/cache/nginx && \
    chmod -R 755 /var/cache/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Copy custom nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

# Ensure nginx can read the static files
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Expose port (matches nginx listen)
EXPOSE 80

# Health check (use 127.0.0.1 to force IPv4 — wget resolves localhost to ::1 first)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:80/ || exit 1

# Drop privileges
USER nginx

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
