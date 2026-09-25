from fastapi import APIRouter

from app.services.crawl_service import crawl_service

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.post("/crawl")
async def crawl() -> dict:
    return await crawl_service.run()
