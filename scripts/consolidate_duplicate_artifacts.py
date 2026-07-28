"""Consolidate duplicate ArtifactDiscovery records based on strong identifiers.

Usage:
    python scripts/consolidate_duplicate_artifacts.py --dry-run
    python scripts/consolidate_duplicate_artifacts.py --apply
"""
import argparse, asyncio, platform, sys
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select, func
from app.database.session import async_session_factory
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation


def find_groups(discoveries):
    groups = []
    used = set()
    for d1 in discoveries:
        if d1.id in used:
            continue
        group = [d1]
        used.add(d1.id)
        for d2 in discoveries:
            if d2.id in used:
                continue
            if _matches(d1, d2):
                group.append(d2)
                used.add(d2.id)
        if len(group) > 1:
            groups.append(group)
    return groups


def _matches(a, b):
    if a.sha256 and b.sha256 and a.sha256 == b.sha256:
        return True
    if a.torrent_infohash and b.torrent_infohash and a.torrent_infohash == b.torrent_infohash:
        return True
    if a.ipfs_cid and b.ipfs_cid and a.ipfs_cid == b.ipfs_cid:
        return True
    if a.canonical_locator and b.canonical_locator and a.canonical_locator == b.canonical_locator:
        return True
    return False


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Only report, don't modify")
    parser.add_argument("--apply", action="store_true", help="Apply consolidation")
    args = parser.parse_args()
    if not args.dry_run and not args.apply:
        print("Specify --dry-run or --apply")
        sys.exit(1)

    async with async_session_factory() as session:
        r = await session.execute(select(ArtifactDiscovery).order_by(ArtifactDiscovery.first_observed_at))
        all_ad = list(r.scalars().all())
        print(f"Total ArtifactDiscovery records: {len(all_ad)}")

        groups = find_groups(all_ad)
        print(f"Duplicate groups found: {len(groups)}")
        total_duplicates = sum(len(g) - 1 for g in groups)
        print(f"Duplicate records to consolidate: {total_duplicates}")

        for i, group in enumerate(groups):
            canonical = group[0]
            dups = group[1:]
            print(f"\n  Group {i+1}: canonical={canonical.id} ({canonical.filename or canonical.canonical_locator[:50]})")
            for dup in dups:
                print(f"    Duplicate: {dup.id} ({dup.filename or dup.canonical_locator[:50]})")

            if args.apply:
                for dup in dups:
                    dobs = await session.execute(
                        select(DistributionObservation).where(DistributionObservation.artifact_discovery_id == dup.id)
                    )
                    for dob in dobs.scalars().all():
                        dob.artifact_discovery_id = canonical.id
                        session.add(dob)
                    await session.delete(dup)
                print(f"    -> Consolidated {len(dups)} duplicates into {canonical.id}")

        if args.apply:
            await session.commit()
            print(f"\nConsolidation applied. Removed {total_duplicates} duplicate records.")

        ref_count = await session.execute(select(func.count(DistributionObservation.id)))
        print(f"\nTotal DistributionObservations: {ref_count.scalar() or 0}")


if __name__ == "__main__":
    asyncio.run(main())
