from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Aktivitäten Crawler", lifespan=lifespan)
app.include_router(router)
