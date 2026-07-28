import asyncio, platform
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from app.database.session import async_session_factory
from sqlalchemy import select
from app.database.models.source import Source

async def main():
    async with async_session_factory() as s:
        r = await s.execute(select(Source))
        srcs = r.scalars().all()
        print(f"Total sources: {len(srcs)}")
        print(f"Active: {sum(1 for x in srcs if x.lifecycle_status == 'active')}")
        print(f"Inactive: {sum(1 for x in srcs if x.lifecycle_status == 'inactive')}")
        print(f"Historical: {sum(1 for x in srcs if x.lifecycle_status == 'historical')}")
        for x in srcs:
            if x.lifecycle_status in ("active", "inactive"):
                print(f"  {x.external_id:30s} lifecycle={x.lifecycle_status:10s} enabled={str(x.enabled):5s} disabled_reason={x.disabled_reason or ''}")

asyncio.run(main())
