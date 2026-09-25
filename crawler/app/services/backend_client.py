from __future__ import annotations

import httpx

from app.core.config import settings
from app.models.activity import Activity, ActivityCreate


class BackendClient:
    """Thin client for the backend's Aktivität CRUD API."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or settings.backend_url

    async def create_activity(self, activity: ActivityCreate) -> Activity:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._base_url}/activities",
                json=activity.model_dump(mode="json"),
            )
            response.raise_for_status()
            return Activity.model_validate(response.json())

    async def push_activities(self, activities: list[ActivityCreate]) -> list[Activity]:
        return [await self.create_activity(activity) for activity in activities]
