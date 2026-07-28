"""Backfill DocumentCloud artifact classification metadata."""
import asyncio, platform, sys
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
from sqlalchemy import select
from app.database.session import async_session_factory
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.source import Source
from app.services.documentcloud_artifact_validation import classify_document

async def main():
    dry_run = "--dry-run" in sys.argv
    apply = "--apply" in sys.argv
    if not dry_run and not apply:
        print("Usage: --dry-run | --apply"); sys.exit(1)

    async with async_session_factory() as s:
        r = await s.execute(select(Source).where(Source.external_id == "nl_documentcloud_api"))
        src = r.scalar_one_or_none()
        if not src:
            print("DocumentCloud source not found"); return

        r2 = await s.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.source_id == src.id))
        ads = list(r2.scalars().all())
        counts = {}
        changes = 0

        for ad in ads:
            title = ad.title or ""
            desc = ad.description or ""
            org = (ad.raw_metadata or {}).get("organization", "") or ""
            access = (ad.raw_metadata or {}).get("access", "public")
            result = classify_document(title, desc, org, access)
            counts[result.classification] = counts.get(result.classification, 0) + 1

            rm = ad.raw_metadata or {}
            if rm.get("document_classification") != result.classification:
                changes += 1
                if not dry_run:
                    rm["document_classification"] = result.classification
                    rm["classification_confidence"] = result.confidence
                    rm["matched_signals"] = result.matched_signals
                    rm["review_required"] = result.review_required
                    ad.raw_metadata = rm
                    if not result.accepted and result.classification == "irrelevant":
                        ad.record_status = "invalidated"
                    elif result.classification == "reference_only":
                        ad.record_status = "review_required"
                    elif result.classification == "sensitive_review_required":
                        ad.record_status = "review_required"
                    s.add(ad)

        print(f"Total DocumentCloud artifacts: {len(ads)}")
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")
        print(f"Changes needed: {changes}")

        if changes and not dry_run:
            await s.commit()
            print("Applied.")
        if dry_run:
            print("\nUse --apply to write.")

if __name__ == "__main__":
    asyncio.run(main())
