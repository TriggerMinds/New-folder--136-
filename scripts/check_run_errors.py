import asyncio, platform
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from app.database.session import async_session_factory
from app.database.models.source_run import SourceRun
from sqlalchemy import select

async def main():
    async with async_session_factory() as s:
        r = await s.execute(select(SourceRun).order_by(SourceRun.started_at.desc()).limit(3))
        for x in r.scalars().all():
            print(f"run {x.id}: status={x.run_status} success={x.success} error={repr(x.error)}")

asyncio.run(main())
