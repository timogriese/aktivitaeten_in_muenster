from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.models.activity import Activity, ActivityCreate
from app.services.dedup import align_to_existing

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

    async def list_activities(self) -> list[Activity]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self._base_url}/activities")
            response.raise_for_status()
            return [Activity.model_validate(item) for item in response.json()]

    async def push_activities(self, activities: list[ActivityCreate]) -> list[tuple[Activity, bool]]:
        """Pushes all activities; ones the backend rejects are logged and skipped.

        Connection errors (backend down) still raise - that should fail the crawl loudly.
        """
        existing = await self.list_activities()
        known = [(activity.title, activity.location) for activity in existing]
        # Same page as an existing entry is the same offer: reuse its title so the push becomes an
        # update instead of a second row (the LLM sometimes names the same page differently each crawl).
        url_to_title = {a.source.url.rstrip("/"): a.title for a in existing if a.source.url}
        # Sequential on purpose: the backend dedups by title against what's already
        # stored, so pushing one at a time also catches duplicates within this same
        # batch (e.g. two search queries surfacing the same activity).
        pushed = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for activity in activities:
                existing_title = url_to_title.get(activity.source.url.rstrip("/"))
                if existing_title and existing_title != activity.title:
                    activity = activity.model_copy(update={"title": existing_title})
                activity = align_to_existing(activity, known)
                try:
                    pushed.append(await self.create_activity(client, activity))
                    known.append((activity.title, activity.location))
                except httpx.HTTPStatusError as error:
                    logger.warning(
                        "Backend rejected %r: %s %s",
                        activity.title,
                        error.response.status_code,
                        error.response.text[:300],
                    )
        return pushed
