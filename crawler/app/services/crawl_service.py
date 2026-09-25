from __future__ import annotations

import logging

from app.services.backend_client import BackendClient
from app.services.scraper_service import ScraperService

logger = logging.getLogger(__name__)


class CrawlService:
    """Orchestrates one crawl cycle: scrape, then push results to the backend.

    Used by both the `/crawl` endpoint and the periodic scheduler job, so a run
    triggered manually and a run triggered by cron behave identically.
    """

    def __init__(
        self,
        scraper_service: ScraperService | None = None,
        backend_client: BackendClient | None = None,
    ) -> None:
        self._scraper_service = scraper_service or ScraperService()
        self._backend_client = backend_client or BackendClient()

    async def run(self, query: str | None = None) -> dict:
        found = self._scraper_service.scrape(query)
        created = await self._backend_client.push_activities(found)
        logger.info(
            "Crawl finished: query=%r found=%d created=%d", query, len(found), len(created)
        )
        return {"query": query, "found": len(found), "created": len(created)}


crawl_service = CrawlService()
