import asyncio, platform
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from app.database.session import async_session_factory
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository

async def main():
    async with async_session_factory() as s:
        r = ArtifactDiscoveryRepository(s)
        c = await r.count_discoveries()
        print(f"Final artifact count: {c}")
asyncio.run(main())
