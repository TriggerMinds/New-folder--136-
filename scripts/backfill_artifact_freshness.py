"""Backfill freshness classification for all active artifacts.

Usage:
    python scripts/backfill_artifact_freshness.py --dry-run
    python scripts/backfill_artifact_freshness.py --apply
"""
import asyncio, platform, sys
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from sqlalchemy import select
from app.database.session import async_session_factory
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.services.freshness import classify_freshness

async def main():
    dry_run = "--dry-run" in sys.argv
    apply = "--apply" in sys.argv
    if not dry_run and not apply:
        print("Usage: --dry-run | --apply"); sys.exit(1)

    async with async_session_factory() as s:
        r = await s.execute(select(ArtifactDiscovery))
        all_ad = list(r.scalars().all())
        changed = 0
        counts = {}

        for d in all_ad:
            old = d.freshness_classification
            new = classify_freshness(d.published_at, d.source_uploaded_at, d.source_modified_at, d.first_observed_at)
            if old != new:
                changed += 1
                counts[new] = counts.get(new, 0) + 1
                if not dry_run:
                    d.freshness_classification = new
                    s.add(d)

        print(f"Total artifacts: {len(all_ad)}")
        print(f"Freshness changes: {changed}")
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")

        if changed and not dry_run:
            await s.commit()
            print("\nApplied.")
        if dry_run:
            print("\nUse --apply to write changes.")

if __name__ == "__main__":
    asyncio.run(main())
