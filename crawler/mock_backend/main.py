from uuid import UUID

from fastapi import FastAPI, HTTPException, Response

from .models import Activity, ActivityCreate, ActivityUpdate
from .storage_service import ActivityStore

app = FastAPI(title="Mock Aktivitäten Backend")
store = ActivityStore()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/activities", response_model=list[Activity])
async def list_activities() -> list[Activity]:
    return store.list()


@app.post("/activities", response_model=Activity)
async def create_activity(activity: ActivityCreate, response: Response) -> Activity:
    """Upserts by title - a matching existing activity is updated (200), not duplicated (201)."""
    result, created = store.create_or_update(activity)
    response.status_code = 201 if created else 200
    return result


@app.get("/activities/{activity_id}", response_model=Activity)
async def get_activity(activity_id: UUID) -> Activity:
    activity = store.get(activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@app.put("/activities/{activity_id}", response_model=Activity)
async def update_activity(activity_id: UUID, activity: ActivityUpdate) -> Activity:
    updated = store.update(activity_id, activity)
    if updated is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return updated


@app.delete("/activities/{activity_id}", status_code=204)
async def delete_activity(activity_id: UUID) -> None:
    deleted = store.delete(activity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Activity not found")
