from __future__ import annotations

import asyncio
import logging

import httpx

from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_BASE_PROMPT = """\
You come up with one short web search query to find things to do in Münster, \
Germany. Favor smaller, lesser-known possibilities over big well-known venues. \
Reply with ONLY the search query text, nothing else - no quotes, no explanation.
"""

# One distinct prompt per parallel search, so a single crawl cycle covers different
# kinds of results instead of five near-identical queries.
_MODE_HINTS = [
    (
        "Find an ORGANIZED sport/movement club or group you can join - an open "
        "training, a recurring practice session, a class - something with an "
        "existing group of people you'd show up and join."
    ),
    (
        "Find an ORGANIZED culture/creative group or class you can join - a choir, "
        "a band, a theatre group, an art or craft workshop, a language exchange - "
        "again something with an existing group you'd join."
    ),
    (
        "Find a COOL NATURE OR OUTDOOR SPOT - a scenic place, a viewpoint, a trail, "
        "a lake/canal spot - something you'd go do yourself with your own group of "
        "friends rather than joining an existing one. Look for city guides, blog "
        "posts or \"best spots in Münster\" style pages."
    ),
    (
        "Find a COOL SOCIAL OR SPONTANEOUS ACTIVITY IDEA - something you'd try with "
        "your own group of friends (not joining an existing group), like a fun "
        "cafe, a game spot, an unusual thing to do together."
    ),
    (
        "Find a ONE-OFF COMMUNITY EVENT happening soon - a market, a festival, a "
        "pop-up, a one-time event rather than a recurring group or a fixed place."
    ),
]

# Used if an LLM call fails (missing key, network error, ...) so a crawl cycle can
# still run. One fallback per mode, in the same order as _MODE_HINTS.
_FALLBACK_QUERIES = [
    "offenes Training Sportverein Münster",
    "offene Chorprobe Kunstwerkstatt Münster",
    "schönste Aussichtspunkte Münster",
    "schöne Spots am Kanal Münster Freunde",
    "Wochenmarkt Festival Münster diese Woche",
]


class QueryService:
    """Comes up with the next batch of search queries for a crawl cycle, via the LLM.

    One query per mode in `_MODE_HINTS`, generated in parallel, so each crawl
    covers organized groups, cool self-organized spots, and one-off events alike
    instead of only ever finding one kind of result.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client or LLMClient()

    async def next_queries(self) -> list[str]:
        results = await asyncio.gather(
            *(self._generate_for_hint(hint) for hint in _MODE_HINTS),
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
        return queries

    async def _generate_for_hint(self, hint: str) -> str | None:
        try:
            content = await self._llm_client.chat(
                messages=[
                    {"role": "system", "content": _BASE_PROMPT},
                    {"role": "user", "content": hint},
                ],
                max_tokens=60,
            )
        except (httpx.HTTPError, RuntimeError, KeyError, IndexError):
            return None
        return content.strip().strip('"') or None
