import asyncio, platform
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from app.database.session import async_session_factory
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository

async def main():
    async with async_session_factory() as s:
        r = ArtifactDiscoveryRepository(s)
        total = await r.count_discoveries()
        discoveries = await r.list_discoveries(limit=999, offset=0)
        docs = [d for d in discoveries if d.artifact_type == "document"]
        pdfs = [d for d in discoveries if ".pdf" in (d.file_extension or "")]
        unknowns = [d for d in discoveries if d.artifact_type == "unknown"]
        print(f"Total artifacts: {total}")
        print(f"Documents: {len(docs)} (PDFs: {len(pdfs)})")
        print(f"Unknown type: {len(unknowns)}")
        for d in discoveries[:10]:
            print(f"  [{d.artifact_type}/{d.locator_type}] {d.filename or d.title}")

asyncio.run(main())
