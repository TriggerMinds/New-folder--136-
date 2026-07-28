from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.database.session import async_session_factory
from app.database.models.source import Source
from app.services.source_runner import run_source

scheduler: AsyncIOScheduler | None = None
_scheduler_started = False


async def run_source_job(source_id: str) -> None:
    async with async_session_factory() as session:
        from uuid import UUID
        try:
            uid = UUID(source_id)
            await run_source(uid, session)
            await session.commit()
        except Exception:
            await session.rollback()


def get_or_create_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    return scheduler


async def start_scheduler() -> None:
    global _scheduler_started
    if not settings.scheduler_enabled:
        return
    if _scheduler_started:
        return
    _scheduler_started = True

    sched = get_or_create_scheduler()
    async with async_session_factory() as session:
        result = await session.execute(
            select(Source).where(Source.enabled.is_(True))
        )
        sources = result.scalars().all()
        for src in sources:
            sched.add_job(
                run_source_job,
                "interval",
                args=[str(src.id)],
                minutes=src.poll_interval_minutes,
                id=f"source_{src.id}",
                replace_existing=True,
                misfire_grace_time=60,
            )

    if not sched.running:
        sched.start()


async def stop_scheduler() -> None:
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    scheduler = None


def get_scheduler_status() -> dict:
    if not settings.scheduler_enabled:
        return {"enabled": False, "running": False, "jobs": 0}
    if scheduler is None:
        return {"enabled": True, "running": False, "jobs": 0}
    jobs = scheduler.get_jobs()
    return {
        "enabled": True,
        "running": scheduler.running,
        "jobs": len(jobs),
        "job_ids": [j.id for j in jobs],
    }
