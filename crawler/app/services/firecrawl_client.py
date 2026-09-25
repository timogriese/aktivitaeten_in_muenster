from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# apicode.txt lives in the crawler project root (two levels up from app/services/).
_API_KEY_FILE = Path(__file__).resolve().parents[2] / "apicode.txt"


def _resolve_api_key() -> str:
    """Resolve the Firecrawl API key: env/config first, then apicode.txt."""
    key = settings.firecrawl_api_key.strip()
    if key:
        return key
    if _API_KEY_FILE.exists():
        key = _API_KEY_FILE.read_text().strip()
        if key:
            logger.info("Using Firecrawl API key from %s", _API_KEY_FILE.name)
            return key
    raise RuntimeError(
        "No Firecrawl API key. Set CRAWLER_FIRECRAWL_API_KEY or put the key in apicode.txt."
    )


class FirecrawlClient:
    """Thin async client for the Firecrawl REST API.

    Mirrors ``BackendClient``: a small wrapper around the HTTP calls, so
    ``ScraperService`` can orchestrate search + extraction without knowing the
    wire format. Extraction uses ``/v2/scrape`` with a ``json`` format object,
    which performs schema-guided, LLM-based extraction server-side and returns
    the result in ``data.json`` (no local LLM and no files required).
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = (api_key or "").strip()
        self._base_url = (base_url or settings.firecrawl_api_url).rstrip("/")

    def _headers(self) -> dict[str, str]:
        if not self._api_key:  # resolve lazily so a missing key fails at crawl time, not import
            self._api_key = _resolve_api_key()
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        """Web search -> candidate pages. Each returned dict has at least a ``url``."""
        payload = {"query": query, "limit": limit}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/v1/search", headers=self._headers(), json=payload
            )
            response.raise_for_status()
            body = response.json()

        data = body.get("data")
        if isinstance(data, dict):  # some API versions wrap the list under ``web``
            data = data.get("web") or []
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict) and item.get("url")]

    async def extract(self, url: str, schema: dict, prompt: str) -> dict | None:
        """Scrape ``url`` and return one schema-shaped object, or ``None`` if there is none."""
        payload = {"url": url, "formats": [{"type": "json", "prompt": prompt, "schema": schema}]}
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self._base_url}/v2/scrape", headers=self._headers(), json=payload
            )
            response.raise_for_status()
            body = response.json()

        if not body.get("success"):
            return None
        data = body.get("data")
        extracted = data.get("json") if isinstance(data, dict) else None
        return extracted if isinstance(extracted, dict) else None
