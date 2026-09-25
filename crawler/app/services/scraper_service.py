from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.models.activity import ActivityCreate
from app.services.firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)

# Schema handed to Firecrawl for extraction. Generated from the Pydantic model so the
# extraction target and the validation target can never drift apart.
ACTIVITY_SCHEMA = ActivityCreate.model_json_schema()

EXTRACT_PROMPT = """\
Extract exactly ONE activity or event taking place in Münster, Germany from this page.

Field rules:
- title: the concrete name of the activity/event.
- description: 1-3 sentences describing what it is and what makes it appealing.
- category: a short category such as "festival", "sport", "culture", "market", "nature", "music".
- tags: 2-6 short lowercase tags.
- location: the venue. address = place/street + city; lat/lon = decimal coordinates of that place.
- group_type: "joinable_group" if it is a club, association or recurring meetup you can join; otherwise "self_organized".
- opening_hours.date: a single ISO date "YYYY-MM-DD" only for a one-time event, else null.
- opening_hours.start / end: opening/closing time as "HH:MM" (24h). If unknown, use a sensible daytime window.
- price_eur: entry price in EUR; 0.0 if free / no admission fee.
- source: set to {"type": "scraped"}; the pipeline fills url and scraped_at.

If the page is a generic listing or overview rather than a single activity, pick the single
most prominent, concrete activity described on it. Use only facts present on the page.
"""


class ScraperService:
    """Finds activities on the web and turns them into in-memory `ActivityCreate` objects.

    Real pipeline:
      1. Firecrawl `search` for `query` -> candidate page URLs.
      2. Firecrawl `scrape` (v2, `json` format) per URL -> one structured object per page
         (this is the "LLM" step, now done server-side by Firecrawl against `ACTIVITY_SCHEMA`).
      3. validate that JSON into `ActivityCreate` via `_parse_llm_result`.

    `scrape()` returns `list[ActivityCreate]` and never writes JSON to disk; the objects are
    in memory and are pushed to the backend only once they validate. A broken extraction
    raises `pydantic.ValidationError`, which the caller logs and skips - so only "not broken"
    activities reach the database and one bad page does not abort the rest of the batch.
    """

    def __init__(self, firecrawl_client: FirecrawlClient | None = None) -> None:
        self._firecrawl_client = firecrawl_client or FirecrawlClient()
        self._semaphore = asyncio.Semaphore(settings.firecrawl_concurrency)

    async def scrape(self, query: str | None = None) -> list[ActivityCreate]:
        query = query or settings.default_query
        candidates = await self._firecrawl_client.search(query, limit=settings.firecrawl_search_limit)
        if not candidates:
            logger.info("Search for %r returned no candidate pages", query)
            return []

        logger.info("Search for %r returned %d candidate page(s)", query, len(candidates))
        scraped_at = datetime.now(timezone.utc).isoformat()

        results = await asyncio.gather(
            *(self._extract_one(candidate, scraped_at) for candidate in candidates),
            return_exceptions=True,
        )

        activities: list[ActivityCreate] = []
        for candidate, result in zip(candidates, results):
            url = candidate.get("url")
            if isinstance(result, Exception):
                logger.warning("Skipping %s (extraction failed): %s", url, result)
            elif result is None:
                logger.warning("Skipping %s (no extractable activity)", url)
            else:
                activities.append(result)

        logger.info(
            "Crawl for %r: %d valid activit(ies) from %d page(s)",
            query,
            len(activities),
            len(candidates),
        )
        return activities

    async def _extract_one(self, candidate: dict, scraped_at: str) -> ActivityCreate | None:
        async with self._semaphore:
            url = candidate["url"]
            raw = await self._firecrawl_client.extract(url, schema=ACTIVITY_SCHEMA, prompt=EXTRACT_PROMPT)
            if not isinstance(raw, dict) or not raw:
                return None
            self._stamp_source(raw, url, scraped_at)
            return self._parse_llm_result(raw)

    def _stamp_source(self, raw: dict, url: str, scraped_at: str) -> None:
        """Force the source block to accurate pipeline values, independent of the model output."""
        source = raw.get("source")
        if not isinstance(source, dict):
            source = {}
        source["type"] = "scraped"
        source["url"] = url
        source["scraped_at"] = scraped_at
        raw["source"] = source

    def _parse_llm_result(self, raw: dict) -> ActivityCreate:
        """Validates one extracted JSON object into an ActivityCreate.

        Raises `pydantic.ValidationError` if it does not match the schema, so broken
        extractions are skipped by the caller instead of being stored.
        """
        return ActivityCreate.model_validate(raw)

