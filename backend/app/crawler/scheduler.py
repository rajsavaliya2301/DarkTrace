"""Crawl job scheduler — manages recurring and one-off crawl jobs."""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)


class CrawlJobScheduler:
    """Schedules crawl jobs based on target frequency and triggers."""

    def __init__(self):
        self._jobs: Dict[str, dict] = {}
        self._background_task: Optional[asyncio.Task] = None
        self._running = False
        self._on_job_callback: Optional[Callable] = None

    def set_job_callback(self, callback: Callable):
        """Set callback function invoked when a job should be executed."""
        self._on_job_callback = callback

    async def start(self):
        """Start the scheduler background loop."""
        self._running = True
        self._background_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Crawl scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        logger.info("Crawl scheduler stopped")

    async def add_recurring_job(
        self,
        target_id: str,
        target_url: str,
        frequency: str,
        source_type: str = "onion",
        proxy_config: Optional[dict] = None,
    ) -> str:
        """Add a recurring crawl job based on frequency string."""
        interval_seconds = self._parse_frequency(frequency)
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "id": job_id,
            "target_id": target_id,
            "target_url": target_url,
            "source_type": source_type,
            "frequency": frequency,
            "interval_seconds": interval_seconds,
            "proxy_config": proxy_config or {},
            "type": "recurring",
            "last_run": None,
            "next_run": time.time(),  # Run immediately
            "is_active": True,
        }
        logger.info("Added recurring job %s for %s (every %s)", job_id, target_url, frequency)
        return job_id

    async def add_one_off_job(
        self,
        target_id: str,
        target_url: str,
        source_type: str = "onion",
        proxy_config: Optional[dict] = None,
    ) -> str:
        """Add a one-off crawl job."""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "id": job_id,
            "target_id": target_id,
            "target_url": target_url,
            "source_type": source_type,
            "frequency": None,
            "interval_seconds": None,
            "proxy_config": proxy_config or {},
            "type": "one_off",
            "last_run": None,
            "next_run": time.time(),
            "is_active": True,
        }
        logger.info("Added one-off job %s for %s", job_id, target_url)
        return job_id

    async def get_due_jobs(self) -> list:
        """Get all jobs that are due for execution."""
        now = time.time()
        due = []
        for job_id, job in list(self._jobs.items()):
            if job["is_active"] and job["next_run"] and job["next_run"] <= now:
                due.append(job)
        return due

    async def mark_completed(self, job_id: str):
        """Mark a recurring job as completed and schedule next run."""
        job = self._jobs.get(job_id)
        if not job:
            return
        job["last_run"] = time.time()
        if job["type"] == "recurring" and job["interval_seconds"]:
            job["next_run"] = time.time() + job["interval_seconds"]
        else:
            # One-off job, deactivate
            job["is_active"] = False
            job["next_run"] = None

    async def remove_job(self, job_id: str):
        """Remove a job from the scheduler."""
        self._jobs.pop(job_id, None)

    async def get_all_jobs(self) -> list:
        """Get all registered jobs."""
        return list(self._jobs.values())

    async def _scheduler_loop(self):
        """Main scheduler loop — checks for due jobs every 10 seconds."""
        while self._running:
            try:
                due_jobs = await self.get_due_jobs()
                for job in due_jobs:
                    if self._on_job_callback:
                        try:
                            await self._on_job_callback(job)
                        except Exception as e:
                            logger.error("Job callback failed for %s: %s", job["id"], e)
                    await self.mark_completed(job["id"])
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler loop error: %s", e)
                await asyncio.sleep(30)

    @staticmethod
    def _parse_frequency(frequency: str) -> int:
        """Parse frequency string to interval in seconds."""
        freq_map = {
            "every_1h": 3600,
            "every_2h": 7200,
            "every_4h": 14400,
            "every_6h": 21600,
            "every_8h": 28800,
            "every_12h": 43200,
            "every_24h": 86400,
            "every_48h": 172800,
            "every_7d": 604800,
            "every_30d": 2592000,
        }
        return freq_map.get(frequency, 21600)  # Default: every 6 hours


# Singleton
_scheduler: Optional[CrawlJobScheduler] = None


async def get_scheduler() -> CrawlJobScheduler:
    """Get or create the singleton scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = CrawlJobScheduler()
    return _scheduler
