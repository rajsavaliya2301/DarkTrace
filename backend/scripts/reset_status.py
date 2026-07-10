"""Reset processing_status to 'parsed' so reprocess picks them up."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://darktrace:darktrace_pass@mongodb:27017/darktrace?authSource=admin"

async def reset():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["darktrace"]
    r = await db.raw_content.update_many(
        {"processing_status": "scored"},
        {"$set": {"processing_status": "parsed"}}
    )
    count = await db.raw_content.count_documents({"processing_status": "parsed"})
    total = await db.raw_content.count_documents({})
    print(f"Modified: {r.modified_count}, Total parsed: {count}, Total docs: {total}")
    client.close()

asyncio.run(reset())
