from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.source import Source
from app.database.models.source_run import SourceRun
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation
from app.database.models.reference_observation import ReferenceObservation


async def get_dashboard_summary(db: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(hours=24)

    artifacts_total = (await db.execute(select(func.count(ArtifactDiscovery.id)))).scalar() or 0
    artifacts_24h = (await db.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.first_observed_at >= yesterday))).scalar() or 0
    docs = (await db.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.artifact_type == "document"))).scalar() or 0
    datasets = (await db.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.artifact_type == "dataset"))).scalar() or 0
    archives = (await db.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.artifact_type.in_(["archive_file", "email_archive", "database_dump"])))).scalar() or 0
    repos = (await db.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.locator_type == "repository"))).scalar() or 0
    dists = (await db.execute(select(func.count(DistributionObservation.id)))).scalar() or 0
    refs = (await db.execute(select(func.count(ReferenceObservation.id)))).scalar() or 0
    metadata_only = (await db.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.acquisition_status == "metadata_only"))).scalar() or 0
    downloaded = (await db.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.acquisition_status == "downloaded"))).scalar() or 0

    primary_raw_active = (await db.execute(select(func.count(Source.id)).where(Source.source_layer == "primary_raw", Source.lifecycle_status == "active"))).scalar() or 0
    primary_raw_inactive = (await db.execute(select(func.count(Source.id)).where(Source.source_layer == "primary_raw", Source.lifecycle_status == "inactive"))).scalar() or 0
    historical_sources = (await db.execute(select(func.count(Source.id)).where(Source.lifecycle_status == "historical"))).scalar() or 0

    last_run = (await db.execute(select(SourceRun.completed_at).where(SourceRun.success.is_(True)).order_by(SourceRun.completed_at.desc()).limit(1))).scalar()

    return {
        "unique_artifacts": artifacts_total,
        "artifacts_last_24h": artifacts_24h,
        "documents": docs,
        "datasets": datasets,
        "archive_files": archives,
        "repositories": repos,
        "distribution_observations": dists,
        "reference_observations": refs,
        "metadata_only": metadata_only,
        "downloaded": downloaded,
        "active_primary_raw_sources": primary_raw_active,
        "inactive_primary_raw_sources": primary_raw_inactive,
        "historical_sources": historical_sources,
        "last_successful_source_run": str(last_run) if last_run else None,
    }
