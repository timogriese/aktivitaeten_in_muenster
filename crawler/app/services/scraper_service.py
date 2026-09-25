from __future__ import annotations

from datetime import datetime

from app.models.activity import ActivityCreate


class ScraperService:
    """Finds activities on the web and turns them into `ActivityCreate` objects.

    Real pipeline (to be implemented here):
      1. run a search / crawl for `query` (or a query the service comes up with itself)
      2. feed the found pages to a local LLM and have it extract structured data as JSON
      3. validate that JSON into `ActivityCreate` via `_parse_llm_result`

    `scrape()` is mocked for now: it returns two hardcoded results, routed through
    `_parse_llm_result` to show the JSON -> pydantic step that will later sit between
    the LLM output and the rest of the pipeline. `_mock_llm_results` is the seam to
    replace with real search+crawl+LLM calls; `scrape`'s signature and return type
    should stay stable so nothing downstream needs to change.
    """

    def scrape(self, query: str | None = None) -> list[ActivityCreate]:
        raw_results = self._mock_llm_results(query)
        return [self._parse_llm_result(raw) for raw in raw_results]

    def _parse_llm_result(self, raw: dict) -> ActivityCreate:
        """Validates one JSON object (shaped like the LLM's output) into an ActivityCreate.

        Raises `pydantic.ValidationError` if the JSON doesn't match the schema -
        callers/tests should expect and handle that once real LLM output is wired in.
        """
        return ActivityCreate.model_validate(raw)

    def _mock_llm_results(self, query: str | None) -> list[dict]:
        now = datetime.utcnow().isoformat()
        return [
            {
                "title": "Offenes Schachtraining",
                "description": "Wöchentliches offenes Training, Einsteiger willkommen.",
                "category": "sport",
                "tags": ["schach", "verein"],
                "location": {
                    "address": "Schachclub Münster, Warendorfer Str. 1, Münster",
                    "lat": 51.9625,
                    "lon": 7.6256,
                },
                "group_type": "joinable_group",
                "opening_hours": {"date": None, "start": "19:00", "end": "21:00"},
                "price_eur": 0.0,
                "source": {
                    "type": "scraped",
                    "url": "https://example.org/schachclub-muenster",
                    "scraped_at": now,
                    "extraction_confidence": 0.5,
                },
            },
            {
                "title": "Schöner Bach zum Entspannen",
                "description": "Ruhiger Bachlauf, gut für einen spontanen Spaziergang.",
                "category": "nature",
                "tags": ["natur", "spaziergang"],
                "location": {
                    "address": "Aasee-Umgebung, Münster",
                    "lat": 51.9506,
                    "lon": 7.6106,
                },
                "group_type": "self_organized",
                "opening_hours": {"date": None, "start": "08:00", "end": "20:00"},
                "price_eur": 0.0,
                "source": {
                    "type": "ai_suggested",
                    "url": None,
                    "scraped_at": now,
                    "extraction_confidence": 0.3,
                },
            },
        ]
