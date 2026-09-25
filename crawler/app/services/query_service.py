from __future__ import annotations

import logging

import httpx

from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_BASE_PROMPT = """\
You come up with one short web search query to find things to do in Münster, \
Germany. Favor smaller, lesser-known possibilities over big well-known venues. \
Reply with ONLY the search query text, nothing else - no quotes, no explanation.
"""

# Alternates every call so both kinds of activity get found over time, not just
# whichever the model defaults to.
_MODE_HINTS = [
    (
        "This time: find an ORGANIZED group or club you can join - an open training, "
        "a recurring meetup, a rehearsal, a class - something with an existing group "
        "of people you'd show up and join."
    ),
    (
        "This time: find a COOL PLACE or self-organized activity idea - a scenic spot, "
        "a viewpoint, a trail, a lake/canal spot, something you'd do with your own "
        "group of friends rather than joining an existing one. Look for city guides, "
        "blog posts or \"best spots in Münster\" style pages."
    ),
]

# Used if the LLM call fails (missing key, network error, ...) so a crawl cycle
# can still run. Alternates between the two modes too.
_FALLBACK_QUERIES = [
    "offenes Training Sportverein Münster",
    "schönste Aussichtspunkte Münster",
    "Meetup Münster kostenlos",
    "versteckte Orte Münster Ausflug",
    "Vereinstreffen Münster Anfänger willkommen",
    "schöne Spots am Kanal Münster",
    "offene Chorprobe Münster",
    "geheimtipps Münster Freizeit",
]


class QueryService:
    """Comes up with the next search query for a crawl cycle, via the LLM.

    Alternates between two modes across calls - organized/joinable groups, and
    cool self-organized places/activities - so the crawl doesn't only ever find
    one kind of result.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client or LLMClient()
        self._call_count = 0
        self._fallback_index = 0

    async def next_query(self) -> str:
        mode_hint = _MODE_HINTS[self._call_count % len(_MODE_HINTS)]
        self._call_count += 1

        try:
            content = await self._llm_client.chat(
                messages=[
                    {"role": "system", "content": _BASE_PROMPT},
                    {"role": "user", "content": mode_hint},
                ],
                max_tokens=60,
            )
        except (httpx.HTTPError, RuntimeError, KeyError, IndexError):
            logger.exception("LLM query generation failed, falling back to a fixed query")
            return self._next_fallback_query()

        query = content.strip().strip('"')
        return query or self._next_fallback_query()

    def _next_fallback_query(self) -> str:
        query = _FALLBACK_QUERIES[self._fallback_index % len(_FALLBACK_QUERIES)]
        self._fallback_index += 1
        return query
