from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.models.activity import ActivityCreate
from app.services.llm_client import LLMClient
from app.services.tavily_client import TavilyClient

logger = logging.getLogger(__name__)

# Schema handed to the LLM for extraction. Generated from the Pydantic model so the
# extraction target and the validation target can never drift apart.
_ACTIVITY_SCHEMA_JSON = json.dumps(ActivityCreate.model_json_schema())

EXTRACT_SYSTEM_PROMPT = f"""\
You extract structured data about ONE activity, event, or cool place-to-do-something-at in
Münster, Germany from a web page's content (given as markdown), and output it as JSON
matching this schema:

{_ACTIVITY_SCHEMA_JSON}

Rules:
- Only extract if the page describes one genuine, concrete activity/event/place actually
  located in or near Münster, Germany. If it's located somewhere else entirely, or the page
  has no real single concrete thing to extract (generic homepage, contact/registration form,
  a listing with no clear single standout, 404/error page), respond with exactly: {{}}
- Never invent a title like "Not Found", "N/A" or similar placeholder text.
- Do NOT extract self-help groups, support groups, therapy or crisis services (e.g. for
  illness, addiction, grief) - only hobby, sport, culture, nature, social or community
  activities people would do for fun/leisure.
- title: the concrete, specific name - never a placeholder.
- description: 1-3 sentences, what it is and what makes it appealing.
- category: a short category such as "festival", "sport", "culture", "market", "nature", "music".
- tags: 2-6 short lowercase tags.
- location: the venue. address = place/street + city; lat/lon = decimal coordinates.
- group_type: "joinable_group" for a club/association/recurring meetup you can join;
  "self_organized" for a place/activity idea you'd do with your own group instead.
- opening_hours.date: ISO date "YYYY-MM-DD" only for a one-time event, else null.
- opening_hours.start / end: "HH:MM" (24h); for self_organized, the general daily window
  it's worth doing (e.g. daylight hours). If unknown, use a sensible daytime window.
- price_eur: entry price in EUR; 0.0 if free.
- source: set to {{"type": "scraped"}}.

Use only facts present in the page content. Respond with ONLY the JSON object, nothing else -
no markdown code fences, no explanation.
"""

# Defense in depth: reject obviously junk titles even if the model ignores the prompt above.
_JUNK_TITLES = {"not found", "n/a", "na", "404", "error", "unknown", ""}

# Keeps the extraction prompt (and cost) bounded regardless of page length.
_MAX_MARKDOWN_CHARS = 12000


class ScraperService:
    """Finds activities on the web and turns them into in-memory `ActivityCreate` objects.

    Pipeline:
      1. Tavily `search` for `query` -> candidate pages, each already including its
         page content as markdown (one call, no separate scrape step/cost).
      2. Our own LLM (`LLMClient`, the free gateway model) extracts one structured
         object per page from that markdown, guided by `ACTIVITY_SCHEMA`.
      3. validate that JSON into `ActivityCreate` via `_parse_llm_result`.

    `scrape()` returns `list[ActivityCreate]` and never writes JSON to disk; the objects are
    in memory and are pushed to the backend only once they validate. A broken extraction is
    logged and skipped - one bad page does not abort the rest of the batch.
    """

    def __init__(
        self,
        tavily_client: TavilyClient | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self._tavily_client = tavily_client or TavilyClient()
        self._llm_client = llm_client or LLMClient()
        self._semaphore = asyncio.Semaphore(settings.extraction_concurrency)

    async def scrape(self, query: str | None = None) -> list[ActivityCreate]:
        query = query or settings.default_query
        candidates = await self._tavily_client.search(query, limit=settings.tavily_search_limit)
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
            markdown = candidate.get("raw_content") or candidate.get("content")
            if not markdown:
                return None

            raw = await self._extract_via_llm(markdown)
            if not raw:
                return None

            title = str(raw.get("title", "")).strip()
            if title.lower() in _JUNK_TITLES:
                logger.info("Skipping %s (junk title %r)", url, title)
                return None

            self._stamp_source(raw, url, scraped_at)
            return self._parse_llm_result(raw)

    async def _extract_via_llm(self, markdown: str) -> dict | None:
        content = await self._llm_client.chat(
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                {"role": "user", "content": markdown[:_MAX_MARKDOWN_CHARS]},
            ],
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> dict | None:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        if not text:
            return None
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("LLM extraction did not return valid JSON, skipping")
            return None
        return data if isinstance(data, dict) and data else None

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
