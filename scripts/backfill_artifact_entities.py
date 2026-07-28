"""Backfill entity matching for artifacts missing country/entity data.

Usage:
    python scripts/backfill_artifact_entities.py --dry-run
    python scripts/backfill_artifact_entities.py --apply
"""
import asyncio, platform, sys
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
from app.database.session import async_session_factory
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.services.artifact_entity_matching import match_entities
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository
from app.country_packs.loader import load_country_pack


async def main():
    dry_run = "--dry-run" in sys.argv
    apply = "--apply" in sys.argv
    if not dry_run and not apply:
        print("Usage: python scripts/backfill_artifact_entities.py --dry-run | --apply")
        sys.exit(1)

    async with async_session_factory() as session:
        r = await session.execute(select(ArtifactDiscovery).order_by(ArtifactDiscovery.first_observed_at))
        all_ad = list(r.scalars().all())
        repo = ArtifactDiscoveryRepository(session)

        changed = 0
        country_matched = 0
        eu_matched = 0
        national_matched = 0

        for d in all_ad:
            cc = "NL"
            try:
                pack = load_country_pack(d.host[-2:].upper()) if d.host and len(d.host) >= 2 else None
            except Exception:
                pack = None

            countries, eu, national = match_entities(d.title, d.description, d.filename, d.canonical_locator, cc)

            needs_update = False
            if countries and not d.countries:
                d.countries = countries
                needs_update = True
            if eu and not d.eu_entities:
                d.eu_entities = eu
                needs_update = True
            if national and not d.national_entities:
                d.national_entities = national
                needs_update = True

            if needs_update:
                changed += 1
                if countries: country_matched += 1
                if eu: eu_matched += 1
                if national: national_matched += 1
                if not dry_run:
                    await repo.update_discovery(d)

        print(f"Total artifacts: {len(all_ad)}")
        print(f"Artifacts with entity data needed: {changed}")
        print(f"Country matches: {country_matched}")
        print(f"EU entity matches: {eu_matched}")
        print(f"National entity matches: {national_matched}")

        if not dry_run and changed:
            await session.commit()
            print(f"\nApplied backfill to {changed} artifacts.")
            print("Run --dry-run again to verify zero remaining changes.")

        if dry_run and changed:
            print(f"\nWould modify {changed} artifacts. Run with --apply to execute.")


if __name__ == "__main__":
    asyncio.run(main())
