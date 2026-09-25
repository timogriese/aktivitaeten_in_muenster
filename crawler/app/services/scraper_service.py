from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.tags import ALLOWED_TAGS, TAG_GROUPS
from app.models.activity import (
    ActivityCreate,
    GroupType,
    Location,
    OpeningHours,
    Source,
)
from app.models.extraction import ExtractedActivity
from app.services.geocoding_client import GeocodingClient, in_muenster
from app.services.llm_client import LLMClient
from app.services.tavily_client import TavilyClient

logger = logging.getLogger(__name__)

_ZONE = ZoneInfo("Europe/Berlin")
_TAG_LIST = "\n".join(f"- {group}: {', '.join(tags)}" for group, tags in TAG_GROUPS.items())

EXTRACT_SYSTEM_PROMPT = f"""\
You extract ONE concrete activity, event or place-to-do-something in Münster, Germany from a
web page (given as markdown) and answer with JSON matching this schema:

{json.dumps(ExtractedActivity.model_json_schema(), ensure_ascii=False)}

Allowed tags - choose ALL that fit (at least one), only from this list, spelled exactly:
{_TAG_LIST}

Rules:
- The page must be ABOUT this one activity: a club's training page, a venue's page, an event
  page. Answer {{}} for "top 10" lists, city or travel guides, directories, news overviews,
  homepages without one concrete offer, contact/registration forms, and anything outside
  Münster.
- Answer {{}} for self-help or support groups, therapy, counselling, crisis services, shops and
  retail, and membership-only offers you can't just try out.
- Write title and description in German. Translate if the page is in another language; keep
  proper names as they are.
- description: 1-3 sentences - what it is, what you do there, what makes it appealing.
- address: street and house number if the page gives them, otherwise the named place; always
  ending in "Münster".
- group_type: "joinable_group" = an existing group, course, club or event you join;
  "self_organized" = a place or idea you do with your own people.
- Times come from the page only (times_stated=true). If the page states no times: for a
  public outdoor place (park, lake, nature spot, viewpoint) set start and end to null and
  times_stated=false; for anything else answer {{}}. Never guess times.
- Recurring session on specific weekdays (e.g. "dienstags 19-21 Uhr"): fill weekdays, start
  and end, leave date null. Several slots: use the main one.
- One-time event: date (YYYY-MM-DD) plus start/end. Answer {{}} if it is already over.
- price_eur: price of one visit if stated, 0 if the page says it's free, otherwise null.
- Use only facts from the page. Reply with ONLY the JSON object.
"""

# Default window for public outdoor places without opening hours (parks, lakes, ...).
_DAYLIGHT = (time(8, 0), time(20, 0))
_JUNK_TITLES = {"not found", "n/a", "na", "404", "error", "unknown", ""}
# Keeps the extraction prompt (and cost) bounded regardless of page length.
_MAX_MARKDOWN_CHARS = 20000
_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_MUENSTER_ADDRESS = re.compile(r"münster|\b481\d\d\b", re.IGNORECASE)
_ENGLISH_WORDS = {"the", "and", "with", "is", "are", "you", "your", "for", "of", "this", "to"}
_GERMAN_WORDS = {"der", "die", "das", "und", "mit", "ist", "sind", "für", "ein", "eine", "im", "zu"}


class Rejected(Exception):
    """The page was read fine but doesn't yield an activity we want to store."""


class ScraperService:
    """Finds activities on the web and turns them into in-memory `ActivityCreate` objects.

    Pipeline per query:
      1. Tavily `search` -> candidate pages incl. their content as markdown (one call).
      2. Our own LLM extracts one `ExtractedActivity` per page (German text, tags from
         shared/tags.json, times only if the page states them).
      3. `_to_activity` checks and completes it: geocodes the address (must be in Münster),
         derives the next date for weekly sessions, filters tags, rejects past events,
         English text and guessed times.

    Nothing is written to disk; rejected pages are logged with the reason and skipped.
    """

    def __init__(
        self,
        tavily_client: TavilyClient | None = None,
        llm_client: LLMClient | None = None,
        geocoding_client: GeocodingClient | None = None,
    ) -> None:
        self._tavily_client = tavily_client or TavilyClient()
        self._llm_client = llm_client or LLMClient()
        self._geocoding_client = geocoding_client or GeocodingClient()
        self._semaphore = asyncio.Semaphore(settings.extraction_concurrency)

    async def scrape_many(self, queries: list[str]) -> list[ActivityCreate]:
        """Runs `scrape()` for each query in parallel and combines the results.

        Extraction across all of them still shares one `_semaphore`, so total LLM
        concurrency stays bounded regardless of how many queries are run at once.
        """
        results = await asyncio.gather(*(self.scrape(query) for query in queries))
        return [activity for batch in results for activity in batch]

    async def scrape(self, query: str | None = None) -> list[ActivityCreate]:
        query = query or settings.default_query
        candidates = await self._tavily_client.search(query, limit=settings.tavily_search_limit)
        if not candidates:
            logger.info("Search for %r returned no candidate pages", query)
            return []

        logger.info("Search for %r returned %d candidate page(s)", query, len(candidates))
        today = datetime.now(_ZONE).date()
        scraped_at = datetime.now(UTC).isoformat()

        results = await asyncio.gather(
            *(self._extract_one(candidate, today, scraped_at) for candidate in candidates),
            return_exceptions=True,
        )

        activities: list[ActivityCreate] = []
        for candidate, result in zip(candidates, results):
            url = candidate.get("url")
            if isinstance(result, Rejected):
                logger.info("Skipping %s (%s)", url, result)
            elif isinstance(result, Exception):
                logger.warning("Skipping %s (extraction failed): %s", url, result)
            else:
                activities.append(result)

        logger.info(
            "Crawl for %r: %d valid activit(ies) from %d page(s)",
            query,
            len(activities),
            len(candidates),
        )
        return activities

    async def _extract_one(self, candidate: dict, today: date, scraped_at: str) -> ActivityCreate:
        url = candidate["url"]
        markdown = candidate.get("raw_content") or candidate.get("content")
        if not markdown:
            raise Rejected("no page content")

        async with self._semaphore:
            raw = await self._extract_via_llm(url, markdown, today)
        if not raw:
            raise Rejected("no concrete activity on the page")
        extracted = ExtractedActivity.model_validate(raw)
        return await self._to_activity(extracted, url, today, scraped_at)

    async def _extract_via_llm(self, url: str, markdown: str, today: date) -> dict:
        content = await self._llm_client.chat(
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Today is {today.isoformat()}.\nURL: {url}\n\n"
                    + markdown[:_MAX_MARKDOWN_CHARS],
                },
            ],
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            data = json.loads(text) if text else {}
        except json.JSONDecodeError as error:
            raise Rejected("LLM did not return valid JSON") from error
        if not isinstance(data, dict):
            raise Rejected("LLM did not return a JSON object")
        return data

    async def _to_activity(
        self, extracted: ExtractedActivity, url: str, today: date, scraped_at: str
    ) -> ActivityCreate:
        title = extracted.title.strip()
        if title.lower() in _JUNK_TITLES:
            raise Rejected(f"junk title {title!r}")
        if _looks_english(f"{title} {extracted.description}"):
            raise Rejected(f"text not in German: {title!r}")

        tags = _allowed_tags(extracted.tags)
        if not tags:
            raise Rejected(f"no valid tags in {extracted.tags!r}")
        # "kostenlos" only when the page says so, never as a guess.
        if extracted.price_eur == 0 and "kostenlos" not in tags:
            tags.append("kostenlos")
        elif extracted.price_eur != 0 and "kostenlos" in tags:
            tags.remove("kostenlos")

        start, end = extracted.start, extracted.end
        if not extracted.times_stated or start is None or end is None:
            if extracted.group_type is GroupType.self_organized and "draußen" in tags:
                start, end = _DAYLIGHT
                if "tagsüber" not in tags:
                    tags.append("tagsüber")
            else:
                raise Rejected(f"no times stated on the page for {title!r}")

        event_date = extracted.date
        if event_date is not None and event_date < today:
            raise Rejected(f"event already over ({event_date}): {title!r}")
        if event_date is None and extracted.weekdays:
            event_date = _next_weekday(today, extracted.weekdays)

        address = extracted.address.strip()
        # Photon only searches inside Münster, so it would "find" any foreign address there too.
        if not _MUENSTER_ADDRESS.search(address):
            raise Rejected(f"address not in Münster: {address!r}")
        coordinates = await self._geocoding_client.geocode(address)
        if coordinates is None or not in_muenster(*coordinates):
            raise Rejected(f"address not found in Münster: {address!r}")

        return ActivityCreate(
            title=title,
            description=extracted.description.strip(),
            category=extracted.category,
            tags=tags,
            location=Location(address=address, lat=coordinates[0], lon=coordinates[1]),
            group_type=extracted.group_type,
            opening_hours=OpeningHours(date=event_date, start=start, end=end),
            # The backend requires a price; an unknown one is stored as 0 but not tagged "kostenlos".
            price_eur=extracted.price_eur if extracted.price_eur is not None else 0.0,
            source=Source(type="scraped", url=url, scraped_at=scraped_at),
        )


def _allowed_tags(raw_tags: list[str]) -> list[str]:
    tags = []
    for tag in raw_tags:
        normalized = tag.strip().lower()
        if normalized in ALLOWED_TAGS and normalized not in tags:
            tags.append(normalized)
    return tags


def _next_weekday(today: date, weekdays: list[str]) -> date:
    offsets = [(_WEEKDAYS.index(day) - today.weekday()) % 7 for day in weekdays]
    return today + timedelta(days=min(offsets))


def _looks_english(text: str) -> bool:
    words = re.findall(r"[a-zäöüß]+", text.lower())
    english = sum(word in _ENGLISH_WORDS for word in words)
    german = sum(word in _GERMAN_WORDS for word in words)
    return english > german
