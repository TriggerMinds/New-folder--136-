"""Audit: verify multi-source distribution in artifact feed."""
import asyncio, platform
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from sqlalchemy import select, func, text
from app.database.session import async_session_factory
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.source import Source

async def main():
    async with async_session_factory() as s:
        # Source totals
        print("=== ARTIFACTS PER SOURCE ===")
        r = await s.execute(text("""
            SELECT s.external_id, s.name, s.source_category, s.lifecycle_status, s.enabled,
                   COUNT(ad.id) AS total,
                   SUM(CASE WHEN ad.record_status = 'active' THEN 1 ELSE 0 END) AS active,
                   SUM(CASE WHEN ad.record_status = 'invalidated' THEN 1 ELSE 0 END) AS invalidated,
                   MAX(ad.first_observed_at) AS newest_first_obs,
                   MIN(ad.first_observed_at) AS oldest_first_obs
            FROM sources s
            LEFT JOIN artifact_discoveries ad ON ad.source_id = s.id
            GROUP BY s.external_id, s.name, s.source_category, s.lifecycle_status, s.enabled
            ORDER BY active DESC
        """))
        for row in r:
            print(f"  {row.external_id:30s} active={row.active:5d} inval={row.invalidated:3d} tot={row.total:5d} newest={str(row.newest_first_obs)[:19] if row.newest_first_obs else 'never'}")
        
        # Totals
        total = (await s.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.record_status == "active"))).scalar() or 0
        print(f"\n=== TOTALS ===")
        print(f"  Active artifacts: {total}")
        
        # Check if source_id changes during dedup
        print(f"\n=== SOURCE_ID STABILITY CHECK ===")
        r2 = await s.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT ad.canonical_locator, COUNT(DISTINCT ad.source_id) as source_count
                FROM artifact_discoveries ad
                WHERE ad.record_status = 'active'
                GROUP BY ad.canonical_locator
                HAVING COUNT(DISTINCT ad.source_id) > 1
            ) dup
        """))
        multi_source = r2.scalar() or 0
        print(f"  Canonical locators with multiple sources: {multi_source}")
        
        # Test records
        print(f"\n=== TEST/EXAMPLE RECORDS ===")
        r3 = await s.execute(text("""
            SELECT ad.id, ad.canonical_locator, ad.record_status, s.external_id
            FROM artifact_discoveries ad
            JOIN sources s ON ad.source_id = s.id
            WHERE ad.canonical_locator LIKE '%example.com%' OR ad.canonical_locator LIKE '%test%'
            ORDER BY ad.first_observed_at
        """))
        for row in r3:
            print(f"  {row.id}: {str(row.canonical_locator)[:60]} status={row.record_status} source={row.external_id}")

asyncio.run(main())
