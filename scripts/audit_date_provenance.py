"""Audit: determine why artifact feed shows mostly 2020-2021 material."""
import asyncio, platform, re
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from sqlalchemy import select, func
from app.database.session import async_session_factory
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.source_run import SourceRun
from app.database.models.source import Source

YEAR_PAT = re.compile(r"/20\d{2}/|20\d{2}[-/]")

async def main():
    async with async_session_factory() as s:
        total = (await s.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.record_status != "invalidated"))).scalar() or 0
        print(f"=== ACTIVE ARTIFACTS: {total} ===\n")
        
        # Year distribution from canonical_locator
        r = await s.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.record_status != "invalidated").order_by(ArtifactDiscovery.first_observed_at))
        all_ad = list(r.scalars().all())
        
        years = {}
        unknown = 0
        for d in all_ad:
            loc = d.canonical_locator or ""
            m = YEAR_PAT.search(loc)
            if m:
                yr = m.group().strip("/")
                if yr.isdigit() and 1900 <= int(yr) <= 2026:
                    years[int(yr)] = years.get(int(yr), 0) + 1
                    continue
            unknown += 1
        print("=== ARTIFACTS PER JAAR (URL-bepaald) ===")
        for y in sorted(years):
            print(f"  {y}: {years[y]}")
        print(f"  onbekend: {unknown}\n")
        
        # Newest/oldest first_observed_at
        newest = await s.execute(select(ArtifactDiscovery.first_observed_at).where(ArtifactDiscovery.record_status != "invalidated").order_by(ArtifactDiscovery.first_observed_at.desc()).limit(1))
        oldest = await s.execute(select(ArtifactDiscovery.first_observed_at).where(ArtifactDiscovery.record_status != "invalidated").order_by(ArtifactDiscovery.first_observed_at).limit(1))
        print(f"=== DATUM PROVENANCE ===")
        print(f"  Nieuwste first_observed_at: {newest.scalar()}")
        print(f"  Oudste first_observed_at:  {oldest.scalar()}")
        
        # Sample: 10 newest, 10 oldest, 10 from 2020 pages, 10 from 2021 pages
        def fmt(d):
            loc = (d.canonical_locator or "")[:80]
            yr_match = YEAR_PAT.search(loc)
            url_yr = yr_match.group().strip("/") if yr_match else "?"
            raw_pub = (d.raw_metadata or {}).get("published_at", "")
            return f"  {d.id}: first_obs={d.first_observed_at} url_yr={url_yr} pub={raw_pub} loc={loc}"
        
        print("\n=== 10 NIEUWSTE ===")
        for d in all_ad[-10:]:
            print(fmt(d))
        
        print("\n=== 10 OUDSTE ===")
        for d in all_ad[:10]:
            print(fmt(d))
        
        # Cryptome runs
        r2 = await s.execute(select(SourceRun).order_by(SourceRun.started_at.desc()).limit(10))
        runs = list(r2.scalars().all())
        print(f"\n=== LAATSTE 10 SOURCE RUNS ===")
        for run in runs:
            print(f"  {run.started_at} success={run.success} items={run.items_seen}")
        
        # Freshness
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        last_24h = sum(1 for d in all_ad if d.first_observed_at >= now - timedelta(hours=24))
        last_7d = sum(1 for d in all_ad if d.first_observed_at >= now - timedelta(days=7))
        print(f"\n=== FRESHNESS ===")
        print(f"  artifacts laatste 24u: {last_24h}")
        print(f"  artifacts laatste 7d:  {last_7d}")
        
        max_first = max(d.first_observed_at for d in all_ad) if all_ad else None
        print(f"  nieuwste first_observed: {max_first}")

asyncio.run(main())
