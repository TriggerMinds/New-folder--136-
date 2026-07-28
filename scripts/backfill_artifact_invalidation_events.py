"""Backfill AuditEvent records for invalidated artifacts.

Usage:
    python scripts/backfill_artifact_invalidation_events.py --dry-run
    python scripts/backfill_artifact_invalidation_events.py --apply --yes
"""
import argparse, asyncio, platform, sys
from datetime import datetime, timezone
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from sqlalchemy import select
from app.database.session import async_session_factory
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.audit_event import AuditEvent


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.apply:
        print("Specify --dry-run or --apply"); sys.exit(1)
    if args.apply and not args.yes:
        print("Add --yes to confirm"); sys.exit(1)

    async with async_session_factory() as session:
        r = await session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.record_status == "invalidated"))
        invalidated = list(r.scalars().all())
        errors_before = await session.execute(select(AuditEvent).where(AuditEvent.event_type == "artifact_invalidated"))
        existing = {(e.artifact_discovery_id or "") for e in errors_before.scalars().all()}

        missing = [d for d in invalidated if d.id not in existing]
        print(f"Invalidated artifacts: {len(invalidated)}")
        print(f"Existing invalidation events: {len(existing)}")
        print(f"Missing invalidation events: {len(missing)}")

        if args.apply:
            now = datetime.now(timezone.utc)
            for d in missing:
                event = AuditEvent(
                    event_type="artifact_invalidated",
                    actor="classify_non_artifact_locators",
                    reason=d.invalidation_reason or "index or navigation locator incorrectly registered as artifact",
                    field_name="record_status",
                    old_value={"record_status": "active"},
                    new_value={"record_status": "invalidated", "invalidation_reason": d.invalidation_reason},
                    artifact_discovery_id=d.id,
                )
                session.add(event)
            await session.commit()
            print(f"Created {len(missing)} invalidation events.")
        else:
            for d in missing:
                print(f"  {d.id}: {d.canonical_locator[:80]}")


if __name__ == "__main__":
    asyncio.run(main())
