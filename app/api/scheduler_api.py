from fastapi import APIRouter

from app.scheduler.scheduler import get_scheduler_status, start_scheduler

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
async def scheduler_status():
    return get_scheduler_status()
