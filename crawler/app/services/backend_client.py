from __future__ import annotations

import httpx

from app.core.config import settings
from app.models.activity import Activity, ActivityCreate


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
        # Sequential on purpose: the backend dedups by title against what's already
        # stored, so pushing one at a time also catches duplicates within this same
        # batch (e.g. two search queries surfacing the same activity).
        async with httpx.AsyncClient(timeout=10.0) as client:
            return [await self.create_activity(client, activity) for activity in activities]
