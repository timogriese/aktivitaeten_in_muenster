from __future__ import annotations

import httpx

from app.core.config import settings


class LLMClient:
    """Thin async client for the MSHack AI gateway (OpenAI-compatible chat completions).

    Mirrors ``TavilyClient``/``BackendClient``: just the HTTP call, no prompt
    logic - that lives in whatever service uses this (e.g. ``QueryService``).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = (api_key or settings.llm_api_key).strip()
        self._base_url = (base_url or settings.llm_base_url).rstrip("/")
        self._model = model or settings.llm_model

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise RuntimeError(
                "No LLM API key. Set CRAWLER_LLM_API_KEY in crawler/.env "
                "(copy crawler/.env.example)."
            )
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 200,
        response_format: dict | None = None,
    ) -> str:
        """Send a chat completion request, return the assistant message content.

        Pass ``response_format={"type": "json_object"}`` to ask the model to
        return valid JSON (standard OpenAI-compatible parameter).
        """
        payload = {"model": self._model, "messages": messages, "max_tokens": max_tokens}
        if response_format is not None:
            payload["response_format"] = response_format
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions", headers=self._headers(), json=payload
            )
            response.raise_for_status()
            body = response.json()
        return body["choices"][0]["message"]["content"]
