from datetime import datetime
from uuid import UUID

from .models import Activity, ActivityCreate, ActivityUpdate


class ActivityStore:
    def __init__(self) -> None:
        self._activities: dict[UUID, Activity] = {}

    def list(self) -> list[Activity]:
        return list(self._activities.values())

    def get(self, activity_id: UUID) -> Activity | None:
        return self._activities.get(activity_id)

    def create(self, data: ActivityCreate) -> Activity:
        activity = Activity(**data.model_dump())
        self._activities[activity.id] = activity
        return activity

    def find_by_title(self, title: str) -> Activity | None:
        normalized = title.strip().lower()
        return next(
            (a for a in self._activities.values() if a.title.strip().lower() == normalized),
            None,
        )

    def create_or_update(self, data: ActivityCreate) -> tuple[Activity, bool]:
        """Upserts by title: same title -> refresh the existing entry instead of duplicating it.

        Returns (activity, created) - created is False when an existing activity was updated.
        """
        existing = self.find_by_title(data.title)
        if existing is None:
            return self.create(data), True

        updated = existing.model_copy(update={**data.model_dump(), "updated_at": datetime.utcnow()})
        self._activities[existing.id] = updated
        return updated, False

    def update(self, activity_id: UUID, data: ActivityUpdate) -> Activity | None:
        existing = self._activities.get(activity_id)
        if existing is None:
            return None
        updated = existing.model_copy(
            update={**data.model_dump(exclude_unset=True), "updated_at": datetime.utcnow()}
        )
        self._activities[activity_id] = updated
        return updated

    def delete(self, activity_id: UUID) -> bool:
        return self._activities.pop(activity_id, None) is not None
