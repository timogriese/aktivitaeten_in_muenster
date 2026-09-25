from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.services.crawl_service import crawl_service

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    if settings.crawl_interval_minutes <= 0:
        return
    scheduler.add_job(
        crawl_service.run,
        "interval",
        minutes=settings.crawl_interval_minutes,
        id="periodic_crawl",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
