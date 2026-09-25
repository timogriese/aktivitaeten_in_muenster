from __future__ import annotations

import httpx

from app.core.config import settings


class TavilyClient:
    """Thin async client for the Tavily Search API.

    One call returns both candidate URLs and their page content (as markdown),
    so no separate scrape step is needed.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = (api_key or settings.tavily_api_key).strip()
        self._base_url = (base_url or settings.tavily_api_url).rstrip("/")

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise RuntimeError(
                "No Tavily API key. Set CRAWLER_TAVILY_API_KEY in crawler/.env "
                "(copy crawler/.env.example)."
            )
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        """Web search -> candidate pages, each with its markdown content included."""
        payload = {"query": query, "max_results": limit, "include_raw_content": "markdown"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/search", headers=self._headers(), json=payload
            )
            response.raise_for_status()
            body = response.json()

        results = body.get("results")
        if not isinstance(results, list):
            return []
        return [r for r in results if isinstance(r, dict) and r.get("url")]
