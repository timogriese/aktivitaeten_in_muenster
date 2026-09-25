from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.models.activity import Activity, ActivityCreate

logger = logging.getLogger(__name__)


class BackendClient:
    """Thin client for the backend's Aktivität CRUD API."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or settings.backend_url

    async def create_activity(
        self, client: httpx.AsyncClient, activity: ActivityCreate
    ) -> tuple[Activity, bool]:
        """Pushes one activity. Returns (activity, created).

        The backend upserts by title, so `created` is False when this refreshed an
        existing activity instead of adding a new one.
        """
        response = await client.post(
            f"{self._base_url}/activities",
            json=activity.model_dump(mode="json"),
        )
        response.raise_for_status()
        return Activity.model_validate(response.json()), response.status_code == 201

    async def push_activities(self, activities: list[ActivityCreate]) -> list[tuple[Activity, bool]]:
        """Pushes all activities; ones the backend rejects are logged and skipped.

        Connection errors (backend down) still raise - that should fail the crawl loudly.
        """
        # Sequential on purpose: the backend dedups by title against what's already
        # stored, so pushing one at a time also catches duplicates within this same
        # batch (e.g. two search queries surfacing the same activity).
        pushed = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for activity in activities:
                try:
                    pushed.append(await self.create_activity(client, activity))
                except httpx.HTTPStatusError as error:
                    logger.warning(
                        "Backend rejected %r: %s %s",
                        activity.title,
                        error.response.status_code,
                        error.response.text[:300],
                    )
        return pushed
