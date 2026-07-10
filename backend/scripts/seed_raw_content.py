"""Copy crawled content from Elasticsearch to MongoDB raw_content,
then trigger the processing pipeline to generate alerts and actors."""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from elasticsearch import AsyncElasticsearch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://darktrace:darktrace_pass@mongodb:27017/darktrace?authSource=admin"
ES_HOST = "http://elasticsearch:9200"
ES_USER = "elastic"
ES_PASS = "darktrace_es_pass"
BATCH_SIZE = 50


async def migrate():
    # Connect to MongoDB
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client["darktrace"]

    # Connect to Elasticsearch
    es = AsyncElasticsearch(
        hosts=[ES_HOST],
        basic_auth=(ES_USER, ES_PASS),
        verify_certs=False,
        request_timeout=60,
    )

    # Check ES connection
    try:
        info = await es.info()
        logger.info("Connected to Elasticsearch %s", info["version"]["number"])
    except Exception as e:
        logger.error("ES connection failed: %s", e)
        return

    # Count existing in MongoDB raw_content
    existing_count = await db.raw_content.count_documents({})
    logger.info("Existing raw_content in MongoDB: %d", existing_count)

    # Scroll through all ES crawled_content docs
    es_count = 0
    migrated = 0
    scroll_timeout = "2m"

    resp = await es.search(
        index="crawled_content",
        scroll=scroll_timeout,
        size=BATCH_SIZE,
        body={"query": {"match_all": {}}},
    )

    scroll_id = resp.get("_scroll_id")
    hits = resp.get("hits", {}).get("hits", [])
    es_count = resp.get("hits", {}).get("total", {}).get("value", 0)
    logger.info("Found %d documents in ES crawled_content", es_count)

    batch = []
    while hits:
        for hit in hits:
            src = hit["_source"]
            doc_id = hit["_id"]

            # Build MongoDB document
            doc = {
                "_id": doc_id,
                "url": src.get("url", ""),
                "title": src.get("title", ""),
                "text_content": src.get("content_text", ""),
                "author": src.get("author"),
                "source_type": src.get("source_type", "onion"),
                "site_name": src.get("site_name", ""),
                "document_type": src.get("document_type", ""),
                "language": src.get("language", "en"),
                "crawl_timestamp": src.get("crawl_timestamp"),
                "fetch_timestamp": datetime.now(tz=timezone.utc),
                "processing_status": "parsed",  # Mark as ready for pipeline
                "scoring": src.get("scoring", {}),
                "entities": src.get("entities", {}),
                "analysis": src.get("analysis", {}),
                "created_at": datetime.now(tz=timezone.utc),
                "updated_at": datetime.now(tz=timezone.utc),
            }
            batch.append(doc)

        if len(batch) >= BATCH_SIZE:
            try:
                for d in batch:
                    await db.raw_content.replace_one(
                        {"_id": d["_id"]}, d, upsert=True
                    )
                migrated += len(batch)
                logger.info("Migrated %d / %d docs...", migrated, es_count)
            except Exception as e:
                logger.error("Batch insert failed: %s", e)
            batch = []

        # Get next batch
        resp = await es.scroll(scroll_id=scroll_id, scroll=scroll_timeout)
        scroll_id = resp.get("_scroll_id")
        hits = resp.get("hits", {}).get("hits", [])

    # Final batch
    if batch:
        try:
            for d in batch:
                await db.raw_content.replace_one(
                    {"_id": d["_id"]}, d, upsert=True
                )
            migrated += len(batch)
        except Exception as e:
            logger.error("Final batch insert failed: %s", e)

    # Clear scroll
    try:
        await es.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass

    final_count = await db.raw_content.count_documents({})
    logger.info("Migration complete: %d docs in MongoDB raw_content", final_count)

    # Close connections
    mongo_client.close()
    await es.close()


if __name__ == "__main__":
    asyncio.run(migrate())
