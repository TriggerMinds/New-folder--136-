"""Classify root/index locators that were incorrectly registered as artifacts.

Usage:
    python scripts/classify_non_artifact_locators.py --dry-run
    python scripts/classify_non_artifact_locators.py --apply --yes
"""
import argparse, asyncio, platform, sys, re
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from sqlalchemy import select
from app.database.session import async_session_factory
from app.database.models.artifact_discovery import ArtifactDiscovery


INDEX_PATTERNS = [
    re.compile(r"^https?://[^/]+/?$", re.I),
    re.compile(r"/index\.html?$", re.I),
    re.compile(r"/default\.html?$", re.I),
    re.compile(r"/index\.php$", re.I),
]


def is_non_artifact(url: str) -> bool:
    for p in INDEX_PATTERNS:
        if p.search(url):
            return True
    return False


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.apply:
        print("Specify --dry-run or --apply")
        sys.exit(1)
    if args.apply and not args.yes:
        print("Add --yes to confirm apply")
        sys.exit(1)

    async with async_session_factory() as session:
        r = await session.execute(select(ArtifactDiscovery).order_by(ArtifactDiscovery.first_observed_at))
        all_ad = list(r.scalars().all())
        to_invalidate = []
        for d in all_ad:
            if is_non_artifact(d.canonical_locator):
                to_invalidate.append(d)

        print(f"Total artifacts: {len(all_ad)}")
        print(f"Index/root locators to invalidate: {len(to_invalidate)}")
        for d in to_invalidate:
            print(f"  {d.id}: {d.canonical_locator[:80]}")

        if args.apply:
            for d in to_invalidate:
                d.access_status = "invalidated"
                session.add(d)
            await session.commit()
            print(f"\nInvalidated {len(to_invalidate)} artifacts.")

        active = sum(1 for d in all_ad if d.access_status != "invalidated")
        print(f"Active artifacts after: {active}")


if __name__ == "__main__":
    asyncio.run(main())
