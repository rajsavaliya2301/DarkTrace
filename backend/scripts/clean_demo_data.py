"""Clean all demo/seed data from MongoDB — preserves only configuration (rules, watchlists, users)."""
import asyncio
import logging
from app.database import get_mongodb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clean():
    db = await get_mongodb()

    # 1. Remove demo raw_content (72 seed documents from ES migration)
    count = await db.raw_content.count_documents({})
    if count > 0:
        result = await db.raw_content.delete_many({})
        logger.info("Deleted %d raw_content documents (demo seed data)", result.deleted_count)
    else:
        logger.info("No raw_content documents to clean")

    # 2. Remove demo crawl targets (example .onion sites)
    count = await db.crawl_targets.count_documents({})
    if count > 0:
        result = await db.crawl_targets.delete_many({})
        logger.info("Deleted %d crawl targets (demo example targets)", result.deleted_count)
    else:
        logger.info("No crawl targets to clean")

    # 3. Remove demo actor profiles
    count = await db.actor_profiles.count_documents({})
    if count > 0:
        result = await db.actor_profiles.delete_many({})
        logger.info("Deleted %d actor profiles (demo data)", result.deleted_count)
    else:
        logger.info("No actor profiles to clean")

    # 4. Remove demo alerts
    count = await db.alerts.count_documents({})
    if count > 0:
        result = await db.alerts.delete_many({})
        logger.info("Deleted %d alerts (demo data)", result.deleted_count)
    else:
        logger.info("No alerts to clean")

    # 5. KEEP: alert_rules (configuration defaults)
    rules_count = await db.alert_rules.count_documents({})
    logger.info("Preserved %d alert rules (configuration)", rules_count)

    # 6. KEEP: watchlists (configuration defaults)
    wl_count = await db.watchlists.count_documents({})
    logger.info("Preserved %d watchlists (configuration)", wl_count)

    # 7. KEEP: users (admin account)
    users_count = await db.users.count_documents({})
    logger.info("Preserved %d users (admin account)", users_count)

    logger.info("Demo data cleanup complete!")


if __name__ == "__main__":
    asyncio.run(clean())
