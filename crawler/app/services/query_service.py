from __future__ import annotations


class QueryService:
    """Comes up with the next search query for a crawl cycle.

    Mocked for now: cycles through a fixed pool of example queries. Replace
    with real query planning later (e.g. a small LLM proposing search
    directions based on what's already in the backend, or which categories/
    areas of Münster are underrepresented so far), so each crawl cycle covers
    new ground instead of repeating itself.
    """

    def __init__(self) -> None:
        self._queries = [
            "offenes Training Sportverein Münster",
            "Meetup Münster kostenlos",
            "Vereinstreffen Münster Anfänger willkommen",
            "offene Chorprobe Münster",
            "Schachverein Münster offenes Training",
        ]
        self._index = 0

    def next_query(self) -> str:
        query = self._queries[self._index % len(self._queries)]
        self._index += 1
        return query
