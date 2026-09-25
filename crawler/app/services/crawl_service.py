from __future__ import annotations

import logging

from app.services.backend_client import BackendClient
from app.services.query_service import QueryService
from app.services.scraper_service import ScraperService

logger = logging.getLogger(__name__)


class CrawlService:
    """Orchestrates one crawl cycle: come up with a query, scrape, push to the backend.

    Used by both the `/crawl` endpoint and the periodic scheduler job, so a run
    triggered manually and a run triggered by cron behave identically. Takes no
    input - the query comes from `QueryService`, not from the caller.
    """

    def __init__(
        self,
        scraper_service: ScraperService | None = None,
        backend_client: BackendClient | None = None,
        query_service: QueryService | None = None,
    ) -> None:
        self._scraper_service = scraper_service or ScraperService()
        self._backend_client = backend_client or BackendClient()
        self._query_service = query_service or QueryService()

    async def run(self) -> dict:
        query = await self._query_service.next_query()
        found = await self._scraper_service.scrape(query)
        created = await self._backend_client.push_activities(found)
        logger.info(
            "Crawl finished: query=%r found=%d created=%d", query, len(found), len(created)
        )
        return {"query": query, "found": len(found), "created": len(created)}


crawl_service = CrawlService()
