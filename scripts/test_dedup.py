"""Test that register_artifact_discovery deduplicates."""
import asyncio, platform
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from app.database.session import async_session_factory
from app.services.artifact_discovery import register_artifact_discovery
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository
from sqlalchemy import select
from app.database.models.source import Source

async def main():
    async with async_session_factory() as s:
        r = await s.execute(select(Source).where(Source.external_id == "nl_cryptome_archive"))
        src = r.scalar_one_or_none()
        if not src:
            print("Source nl_cryptome_archive not found")
            return
        
        count_before = await ArtifactDiscoveryRepository(s).count_discoveries()
        
        result1 = await register_artifact_discovery(
            session=s, source_id=src.id,
            url="https://cryptome.org/test-duplicate.pdf",
            title="Dedup Test",
        )
        print(f"Run 1: is_new={result1.is_new}, dedup_type={result1.deduplication_type}, id={result1.artifact.id}")
        
        result2 = await register_artifact_discovery(
            session=s, source_id=src.id,
            url="https://cryptome.org/test-duplicate.pdf",
            title="Dedup Test Second",
        )
        print(f"Run 2: is_new={result2.is_new}, dedup_type={result2.deduplication_type}, id={result2.artifact.id}")
        
        count_after = await ArtifactDiscoveryRepository(s).count_discoveries()
        print(f"Count before: {count_before}, after: {count_after}")
        print(f"SAME ID: {result1.artifact.id == result2.artifact.id}")
        
        await s.commit()

asyncio.run(main())
