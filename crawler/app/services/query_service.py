from __future__ import annotations

import asyncio
import logging
import random
from collections import deque
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_BASE_PROMPT = """\
You write one web search query to find concrete things to do in Münster, Germany.
Rules:
- Write the query in German and include the word "Münster".
- 3 to 8 words, aimed at a page about ONE specific offer (a club's training page, a
  venue's page, an event page) - not at "top 10" lists or city guides.
- Favor smaller, lesser-known possibilities over big well-known venues.
- Don't repeat or rephrase any of the already used queries.
Reply with ONLY the search query text - no quotes, no explanation.
"""

# One mode per parallel search, each with sub-topics that rotate between crawl cycles,
# so a bulk import keeps covering new ground instead of re-finding the same pages.
_MODES = [
    (
        "An ORGANIZED sport/movement group you can join (open training, trial session).",
        ["Laufen", "Bouldern", "Klettern", "Tanzen", "Yoga", "Kampfsport", "Volleyball",
         "Tischtennis", "Schwimmen", "Rudern", "Kanu", "Skaten", "Radfahren", "Ultimate Frisbee",
         "Fußball", "Badminton", "Tennis", "Turnen", "Nordic Walking"],
    ),
    (
        "An ORGANIZED culture/creative group or class you can join.",
        ["Chor", "Theater", "Improtheater", "Töpfern", "Malen", "Fotografie", "Nähen",
         "Sprachcafé", "Schach", "Brettspiele", "Jam-Session", "Lesekreis", "Zeichnen",
         "Siebdruck", "Repair Café"],
    ),
    (
        "A NATURE OR OUTDOOR SPOT in Münster you'd visit with your own friends (no group).",
        ["Aasee", "Rieselfelder", "Dortmund-Ems-Kanal", "Werse", "Wienburgpark",
         "Botanischer Garten", "Aussichtspunkt", "Picknickwiese", "Naturschutzgebiet",
         "Wald", "Badestelle", "Schlossgarten", "Südpark"],
    ),
    (
        "A SOCIAL OR SPONTANEOUS ACTIVITY you'd do with your own friends at a venue.",
        ["Escape Room", "Minigolf", "Bowling", "Pubquiz", "Karaoke", "Billard",
         "Brettspielcafé", "Programmkino", "Kletterhalle", "Tretboot", "Lasertag"],
    ),
    (
        "A ONE-OFF EVENT happening soon (give the month in the query).",
        ["Konzert", "Festival", "Flohmarkt", "Lesung", "Vortrag", "Ausstellung", "Stadtfest",
         "Kunstmarkt", "Poetry Slam", "Führung", "Workshop"],
    ),
]

# Used if an LLM call fails (missing key, network error, ...) so a crawl cycle can
# still run. One fallback per mode, in the same order as _MODES.
_FALLBACK_QUERIES = [
    "Münster Sportverein offenes Training Anfänger",
    "Münster Chor offene Probe mitsingen",
    "Münster Rieselfelder Naturschutzgebiet Besuch",
    "Münster Escape Room Gruppe",
    "Münster Flohmarkt Termine",
]


class QueryService:
    """Comes up with the next batch of search queries for a crawl cycle, via the LLM.

    One query per mode, generated in parallel, each seeded with a random sub-topic and
    the recently used queries so repeated cycles keep finding new pages.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client or LLMClient()
        self._history: deque[str] = deque(maxlen=60)

    async def next_queries(self) -> list[str]:
        today = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y")
        history = list(self._history)
        results = await asyncio.gather(
            *(
                self._generate(mode, random.choice(topics), today, history)
                for mode, topics in _MODES
            ),
            return_exceptions=True,
        )
        queries = []
        for index, result in enumerate(results):
            if isinstance(result, BaseException) or not result:
                if isinstance(result, BaseException):
                    logger.warning("Query generation failed for mode %d: %s", index, result)
                queries.append(_FALLBACK_QUERIES[index])
            else:
                queries.append(result)
        self._history.extend(queries)
        return queries

    async def _generate(self, mode: str, topic: str, today: str, history: list[str]) -> str | None:
        used = "\n".join(f"- {query}" for query in history) or "(none yet)"
        user = f"Today is {today}.\nLook for: {mode}\nSub-topic: {topic}\nAlready used queries:\n{used}"
        try:
            content = await self._llm_client.chat(
                messages=[
                    {"role": "system", "content": _BASE_PROMPT},
                    {"role": "user", "content": user},
                ],
                max_tokens=60,
            )
        except (httpx.HTTPError, RuntimeError, KeyError, IndexError):
            return None
        return content.strip().strip('"') or None
