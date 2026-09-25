from __future__ import annotations

import logging

from app.services.backend_client import BackendClient
from app.services.query_service import QueryService
from app.services.scraper_service import ScraperService

logger = logging.getLogger(__name__)


class CrawlService:
    """Orchestrates one crawl cycle: come up with queries, scrape them in parallel,
    push results to the backend.

    Used by both the `/crawl` endpoint and the periodic scheduler job, so a run
    triggered manually and a run triggered by cron behave identically. Takes no
    input - the queries come from `QueryService`, not from the caller.
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
        queries = await self._query_service.next_queries()
        found = await self._scraper_service.scrape_many(queries)
        pushed = await self._backend_client.push_activities(found)

        created = sum(1 for _, is_new in pushed if is_new)
        updated = len(pushed) - created
        logger.info(
            "Crawl finished: queries=%r found=%d created=%d updated=%d",
            queries,
            len(found),
            created,
            updated,
        )
        return {"queries": queries, "found": len(found), "created": created, "updated": updated}


crawl_service = CrawlService()
