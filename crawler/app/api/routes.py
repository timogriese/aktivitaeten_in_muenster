from fastapi import APIRouter
from pydantic import BaseModel

from app.services.crawl_service import crawl_service

router = APIRouter()


class CrawlRequest(BaseModel):
    query: str | None = None


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.post("/crawl")
async def crawl(request: CrawlRequest | None = None) -> dict:
    query = request.query if request else None
    return await crawl_service.run(query)
