"""Application configuration using environment variables (12-factor app)."""

import os
from functools import lru_cache
from typing import List, Optional


class Settings:
    """Application settings loaded from environment variables with sensible defaults."""

    # FastAPI
    APP_NAME: str = os.getenv("APP_NAME", "DarkTrace API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"
    API_PREFIX: str = os.getenv("API_PREFIX", "/v1")
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    CORS_ALLOW_CREDENTIALS: bool = True

    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "change-me-in-production-use-a-strong-random-secret"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # MongoDB
    MONGODB_URI: str = os.getenv(
        "MONGODB_URI", "mongodb://localhost:27017/darktrace"
    )
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "darktrace")
    MONGODB_MAX_POOL_SIZE: int = int(os.getenv("MONGODB_MAX_POOL_SIZE", "100"))
    MONGODB_MIN_POOL_SIZE: int = int(os.getenv("MONGODB_MIN_POOL_SIZE", "10"))

    # Elasticsearch
    ELASTICSEARCH_HOSTS: str = os.getenv(
        "ELASTICSEARCH_HOSTS", "http://localhost:9200"
    )
    ELASTICSEARCH_USERNAME: Optional[str] = os.getenv("ELASTICSEARCH_USERNAME")
    ELASTICSEARCH_PASSWORD: Optional[str] = os.getenv("ELASTICSEARCH_PASSWORD")
    ELASTICSEARCH_VERIFY_CERTS: bool = (
        os.getenv("ELASTICSEARCH_VERIFY_CERTS", "true").lower() == "true"
    )

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = int(
        os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")
    )

    # Redis
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_SOCKET_TIMEOUT: int = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    REDIS_SOCKET_CONNECT_TIMEOUT: int = int(
        os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5")
    )

    # Rate Limiting
    RATE_LIMIT_PER_USER: int = int(os.getenv("RATE_LIMIT_PER_USER", "100"))
    RATE_LIMIT_PER_IP: int = int(os.getenv("RATE_LIMIT_PER_IP", "1000"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(
        os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    )
    # Stricter rate limiting for login endpoint (brute-force protection)
    LOGIN_RATE_LIMIT_PER_IP: int = int(os.getenv("LOGIN_RATE_LIMIT_PER_IP", "10"))
    LOGIN_RATE_WINDOW_SECONDS: int = int(os.getenv("LOGIN_RATE_WINDOW_SECONDS", "300"))

    # Crawler
    CRAWL_DELAY: float = float(os.getenv("CRAWL_DELAY", "5.0"))
    CONCURRENT_REQUESTS: int = int(os.getenv("CONCURRENT_REQUESTS", "8"))
    PROXY_REFRESH_INTERVAL: int = int(os.getenv("PROXY_REFRESH_INTERVAL", "600"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    CRAWL_TIMEOUT: int = int(os.getenv("CRAWL_TIMEOUT", "60"))
    TOR_PROXY_HOST: str = os.getenv("TOR_PROXY_HOST", "127.0.0.1")
    TOR_PROXY_PORT: int = int(os.getenv("TOR_PROXY_PORT", "9050"))
    I2P_PROXY_HOST: str = os.getenv("I2P_PROXY_HOST", "127.0.0.1")
    I2P_PROXY_PORT: int = int(os.getenv("I2P_PROXY_PORT", "4444"))

    # RabbitMQ (for future event-driven microservices)
    RABBITMQ_URL: Optional[str] = os.getenv("RABBITMQ_URL")

    # NLP
    SPACY_MODEL_EN: str = os.getenv("SPACY_MODEL_EN", "en_core_web_trf")
    TRANSLATION_CACHE_TTL: int = int(
        os.getenv("TRANSLATION_CACHE_TTL", "2592000")
    )  # 30 days

    # Threat Scoring
    THREAT_SCORE_WEIGHTS: str = os.getenv(
        "THREAT_SCORE_WEIGHTS",
        '{"classification": 0.30, "high_value_targets": 0.20, "actor_reputation": 0.15, "freshness": 0.10, "sentiment": 0.10, "keyword_matches": 0.10, "site_reputation": 0.05}',
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    # Report
    REPORT_EXPIRY_HOURS: int = int(os.getenv("REPORT_EXPIRY_HOURS", "1"))
    REPORT_STORAGE_PATH: str = os.getenv(
        "REPORT_STORAGE_PATH", "/tmp/darktrace/reports"
    )

    # SIEM
    SIEM_SYSLOG_HOST: Optional[str] = os.getenv("SIEM_SYSLOG_HOST")
    SIEM_SYSLOG_PORT: int = int(os.getenv("SIEM_SYSLOG_PORT", "514"))

    # Default admin user
    DEFAULT_ADMIN_EMAIL: str = os.getenv(
        "DEFAULT_ADMIN_EMAIL", "admin@darktrace.com"
    )
    DEFAULT_ADMIN_PASSWORD: str = os.getenv(
        "DEFAULT_ADMIN_PASSWORD", "admin123"
    )

    # ML Model settings
    HUGGINGFACE_MODEL: str = os.getenv("HUGGINGFACE_MODEL", "facebook/bart-large-mnli")
    SENTIMENT_MODEL: str = os.getenv("SENTIMENT_MODEL", "distilbert-base-uncased-finetuned-sst-2-english")
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "/app/models")
    MODEL_AUTO_DOWNLOAD: bool = os.getenv("MODEL_AUTO_DOWNLOAD", "true").lower() == "true"

    # ─── External Threat Intelligence API Keys ─────────────────────────
    VIRUSTOTAL_API_KEY: Optional[str] = os.getenv("VIRUSTOTAL_API_KEY")
    SHODAN_API_KEY: Optional[str] = os.getenv("SHODAN_API_KEY")
    OTX_API_KEY: Optional[str] = os.getenv("OTX_API_KEY")


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()
