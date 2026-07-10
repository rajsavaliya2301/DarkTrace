"""Database connection management for MongoDB, Elasticsearch, Neo4j, and Redis."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch
from neo4j import AsyncGraphDatabase, AsyncDriver
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.connection import ConnectionPool as RedisConnectionPool

from app.config import get_settings

logger = logging.getLogger(__name__)

# Global instances
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None
_es_client: Optional[AsyncElasticsearch] = None
_neo4j_driver: Optional[AsyncDriver] = None
_redis_pool: Optional[RedisConnectionPool] = None
_redis_client: Optional[AsyncRedis] = None


# ─── MongoDB ──────────────────────────────────────────────────────────────────


async def init_mongodb() -> AsyncIOMotorDatabase:
    """Initialize MongoDB connection and return database instance."""
    global _mongo_client, _mongo_db
    settings = get_settings()
    if _mongo_client is None:
        logger.info("Connecting to MongoDB at %s", settings.MONGODB_URI)
        _mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        # Verify connection
        try:
            await _mongo_client.admin.command("ping")
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.warning("MongoDB ping failed: %s. Continuing anyway.", e)
        _mongo_db = _mongo_client[settings.MONGODB_DATABASE]
    return _mongo_db


async def get_mongodb() -> AsyncIOMotorDatabase:
    """Get the MongoDB database instance."""
    global _mongo_db
    if _mongo_db is None:
        return await init_mongodb()
    return _mongo_db


async def close_mongodb() -> None:
    """Close MongoDB connection."""
    global _mongo_client, _mongo_db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("MongoDB connection closed")


# ─── Elasticsearch ────────────────────────────────────────────────────────────


async def init_elasticsearch() -> AsyncElasticsearch:
    """Initialize Elasticsearch client."""
    global _es_client
    settings = get_settings()
    if _es_client is None:
        hosts = settings.ELASTICSEARCH_HOSTS.split(",")
        http_auth = None
        if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
            http_auth = (settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD)
        logger.info("Connecting to Elasticsearch at %s", hosts)
        _es_client = AsyncElasticsearch(
            hosts=hosts,
            http_auth=http_auth,
            verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS,
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )
        # Verify connection
        try:
            info = await _es_client.info()
            logger.info("Elasticsearch connected: %s", info.get("version", {}).get("number", "unknown"))
        except Exception as e:
            logger.warning("Elasticsearch ping failed: %s. Continuing anyway.", e)
    return _es_client


async def get_elasticsearch() -> AsyncElasticsearch:
    """Get the Elasticsearch client."""
    global _es_client
    if _es_client is None:
        return await init_elasticsearch()
    return _es_client


async def close_elasticsearch() -> None:
    """Close Elasticsearch connection."""
    global _es_client
    if _es_client:
        await _es_client.close()
        _es_client = None
        logger.info("Elasticsearch connection closed")


# ─── Neo4j ────────────────────────────────────────────────────────────────────


async def init_neo4j() -> AsyncDriver:
    """Initialize Neo4j driver."""
    global _neo4j_driver
    settings = get_settings()
    if _neo4j_driver is None:
        logger.info("Connecting to Neo4j at %s", settings.NEO4J_URI)
        _neo4j_driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
            max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
            connection_acquisition_timeout=10,
        )
        # Verify connection
        try:
            async with _neo4j_driver.session(database="neo4j") as session:
                result = await session.run("RETURN 1 as val")
                await result.single()
                logger.info("Neo4j connected successfully")
        except Exception as e:
            logger.warning("Neo4j ping failed: %s. Continuing anyway.", e)
    return _neo4j_driver


async def get_neo4j() -> AsyncDriver:
    """Get the Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is None:
        return await init_neo4j()
    return _neo4j_driver


async def close_neo4j() -> None:
    """Close Neo4j connection."""
    global _neo4j_driver
    if _neo4j_driver:
        await _neo4j_driver.close()
        _neo4j_driver = None
        logger.info("Neo4j connection closed")


# ─── Redis ────────────────────────────────────────────────────────────────────


async def init_redis() -> AsyncRedis:
    """Initialize Redis connection pool and client."""
    global _redis_pool, _redis_client
    settings = get_settings()
    if _redis_client is None:
        logger.info("Connecting to Redis at %s", settings.REDIS_URI)
        kwargs = {
            "socket_timeout": settings.REDIS_SOCKET_TIMEOUT,
            "socket_connect_timeout": settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            "decode_responses": True,
        }
        if settings.REDIS_PASSWORD:
            kwargs["password"] = settings.REDIS_PASSWORD
        _redis_pool = RedisConnectionPool.from_url(settings.REDIS_URI, **kwargs)
        _redis_client = AsyncRedis(connection_pool=_redis_pool)
        # Verify connection
        try:
            await _redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning("Redis ping failed: %s. Continuing anyway.", e)
    return _redis_client


async def get_redis() -> AsyncRedis:
    """Get the Redis client."""
    global _redis_client
    if _redis_client is None:
        return await init_redis()
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_pool, _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection closed")


# ─── Global init / shutdown ───────────────────────────────────────────────────


async def init_databases():
    """Initialize all database connections on startup."""
    await init_mongodb()
    await init_elasticsearch()
    await init_neo4j()
    await init_redis()


async def close_databases():
    """Close all database connections on shutdown."""
    await close_mongodb()
    await close_elasticsearch()
    await close_neo4j()
    await close_redis()
