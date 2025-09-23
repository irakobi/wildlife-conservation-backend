"""Health check endpoints"""
from fastapi import APIRouter
from app.database import get_db_info
from app.services.kobo_service import check_kobo_health

router = APIRouter()

@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "wildlife-conservation-api"}

@router.get("/database")
async def database_health():
    return get_db_info()

@router.get("/kobo")
async def kobo_health():
    return await check_kobo_health()
