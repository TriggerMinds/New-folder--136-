from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation
from app.database.models.reference_observation import ReferenceObservation
from app.database.models.artifact_acquisition import ArtifactAcquisition


class ArtifactDiscoveryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_discovery(self, d: ArtifactDiscovery) -> ArtifactDiscovery:
        self.session.add(d)
        await self.session.flush()
        return d

    async def get_discovery(self, did: UUID) -> ArtifactDiscovery | None:
        r = await self.session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.id == did))
        return r.scalar_one_or_none()

    async def find_by_sha256(self, sha256: str) -> ArtifactDiscovery | None:
        r = await self.session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.sha256 == sha256).limit(1))
        return r.scalar_one_or_none()

    async def find_by_torrent_infohash(self, ih: str) -> ArtifactDiscovery | None:
        r = await self.session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.torrent_infohash == ih).limit(1))
        return r.scalar_one_or_none()

    async def find_by_ipfs_cid(self, cid: str) -> ArtifactDiscovery | None:
        r = await self.session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.ipfs_cid == cid).limit(1))
        return r.scalar_one_or_none()

    async def find_by_repository(self, repo_url: str, ref: str | None = None) -> ArtifactDiscovery | None:
        stmt = select(ArtifactDiscovery).where(ArtifactDiscovery.repository_url == repo_url)
        if ref:
            stmt = stmt.where(ArtifactDiscovery.repository_ref == ref)
        r = await self.session.execute(stmt.limit(1))
        return r.scalar_one_or_none()

    async def find_by_archive_identifier(self, aid: str) -> ArtifactDiscovery | None:
        r = await self.session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.archive_identifier == aid).limit(1))
        return r.scalar_one_or_none()

    async def find_by_canonical_locator(self, loc: str) -> ArtifactDiscovery | None:
        r = await self.session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.canonical_locator == loc).limit(1))
        return r.scalar_one_or_none()

    async def find_by_weak_fingerprint(self, filename: str, host: str) -> ArtifactDiscovery | None:
        r = await self.session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.filename == filename, ArtifactDiscovery.host == host).limit(1))
        return r.scalar_one_or_none()

    async def list_discoveries(self, limit=100, offset=0, artifact_type=None, host=None,
                                q=None, file_extension=None, locator_type=None,
                                access_status=None, acquisition_status=None,
                                include_invalidated=False,
                                date_from=None, date_to=None,
                                sort="first_observed_desc") -> list[ArtifactDiscovery]:
        stmt = select(ArtifactDiscovery)
        if not include_invalidated:
            stmt = stmt.where(ArtifactDiscovery.access_status != "invalidated")
        if artifact_type:
            stmt = stmt.where(ArtifactDiscovery.artifact_type == artifact_type)
        if host:
            stmt = stmt.where(ArtifactDiscovery.host == host)
        if file_extension:
            stmt = stmt.where(ArtifactDiscovery.file_extension == file_extension)
        if locator_type:
            stmt = stmt.where(ArtifactDiscovery.locator_type == locator_type)
        if access_status:
            stmt = stmt.where(ArtifactDiscovery.access_status == access_status)
        if acquisition_status:
            stmt = stmt.where(ArtifactDiscovery.acquisition_status == acquisition_status)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                ArtifactDiscovery.title.ilike(pattern)
                | ArtifactDiscovery.description.ilike(pattern)
                | ArtifactDiscovery.filename.ilike(pattern)
                | ArtifactDiscovery.canonical_locator.ilike(pattern)
                | ArtifactDiscovery.archive_identifier.ilike(pattern)
                | ArtifactDiscovery.repository_url.ilike(pattern)
            )
        if date_from:
            stmt = stmt.where(ArtifactDiscovery.first_observed_at >= date_from)
        if date_to:
            stmt = stmt.where(ArtifactDiscovery.first_observed_at <= date_to)
        order = ArtifactDiscovery.first_observed_at.desc()
        if sort == "first_observed_asc":
            order = ArtifactDiscovery.first_observed_at
        elif sort == "last_observed_desc":
            order = ArtifactDiscovery.last_observed_at.desc()
        elif sort == "title_asc":
            order = ArtifactDiscovery.title
        elif sort == "filename_asc":
            order = ArtifactDiscovery.filename
        stmt = stmt.order_by(order).limit(limit).offset(offset)
        r = await self.session.execute(stmt)
        return list(r.scalars().all())

    async def count_discoveries(self, include_invalidated=False) -> int:
        stmt = select(func.count(ArtifactDiscovery.id))
        if not include_invalidated:
            stmt = stmt.where(ArtifactDiscovery.access_status != "invalidated")
        r = await self.session.execute(stmt)
        return r.scalar() or 0

    async def list_distributions(self, artifact_id: UUID, limit=100, offset=0) -> list[DistributionObservation]:
        r = await self.session.execute(
            select(DistributionObservation).where(DistributionObservation.artifact_discovery_id == artifact_id)
            .order_by(DistributionObservation.observed_at.desc()).limit(limit).offset(offset)
        )
        return list(r.scalars().all())

    async def count_distributions(self, artifact_id: UUID) -> int:
        r = await self.session.execute(select(func.count(DistributionObservation.id)).where(DistributionObservation.artifact_discovery_id == artifact_id))
        return r.scalar() or 0

    async def list_references(self, artifact_id: UUID, limit=100, offset=0) -> list[ReferenceObservation]:
        r = await self.session.execute(
            select(ReferenceObservation).where(ReferenceObservation.artifact_discovery_id == artifact_id)
            .order_by(ReferenceObservation.observed_at.desc()).limit(limit).offset(offset)
        )
        return list(r.scalars().all())

    async def count_references(self, artifact_id: UUID) -> int:
        r = await self.session.execute(select(func.count(ReferenceObservation.id)).where(ReferenceObservation.artifact_discovery_id == artifact_id))
        return r.scalar() or 0

    async def list_acquisitions(self, artifact_id: UUID, limit=100, offset=0) -> list[ArtifactAcquisition]:
        r = await self.session.execute(
            select(ArtifactAcquisition).where(ArtifactAcquisition.artifact_discovery_id == artifact_id)
            .order_by(ArtifactAcquisition.requested_at.desc()).limit(limit).offset(offset)
        )
        return list(r.scalars().all())

    async def count_acquisitions(self, artifact_id: UUID) -> int:
        r = await self.session.execute(select(func.count(ArtifactAcquisition.id)).where(ArtifactAcquisition.artifact_discovery_id == artifact_id))
        return r.scalar() or 0

    async def count_artifacts_for_source(self, source_id: UUID) -> int:
        r = await self.session.execute(select(func.count(ArtifactDiscovery.id)).where(ArtifactDiscovery.source_id == source_id))
        return r.scalar() or 0

    async def count_distributions_for_source(self, source_id: UUID) -> int:
        r = await self.session.execute(select(func.count(DistributionObservation.id)).where(DistributionObservation.source_id == source_id))
        return r.scalar() or 0

    async def get_last_artifact_at(self, source_id: UUID):
        r = await self.session.execute(select(ArtifactDiscovery.first_observed_at).where(ArtifactDiscovery.source_id == source_id).order_by(ArtifactDiscovery.first_observed_at.desc()).limit(1))
        return r.scalar()

    async def update_discovery(self, d: ArtifactDiscovery) -> ArtifactDiscovery:
        self.session.add(d)
        await self.session.flush()
        return d

    async def delete_discovery(self, did: UUID) -> None:
        await self.session.delete(did)
        await self.session.flush()


class DistributionObservationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_observation(self, o: DistributionObservation) -> DistributionObservation:
        self.session.add(o)
        await self.session.flush()
        return o

    async def list_for_artifact(self, aid: UUID) -> list[DistributionObservation]:
        r = await self.session.execute(select(DistributionObservation).where(DistributionObservation.artifact_discovery_id == aid).order_by(DistributionObservation.observed_at.desc()))
        return list(r.scalars().all())

    async def exists(self, artifact_id: UUID, source_id: object, canonical_locator: str) -> bool:
        r = await self.session.execute(select(func.count(DistributionObservation.id)).where(
            DistributionObservation.artifact_discovery_id == artifact_id,
            DistributionObservation.source_id == source_id,
            DistributionObservation.canonical_locator == canonical_locator,
        ))
        return (r.scalar() or 0) > 0

    async def list_all(self, limit=100, offset=0,
                        artifact_id=None, source_id=None,
                        distribution_type=None, host=None,
                        date_from=None, date_to=None) -> list[DistributionObservation]:
        stmt = select(DistributionObservation)
        if artifact_id:
            stmt = stmt.where(DistributionObservation.artifact_discovery_id == artifact_id)
        if source_id:
            stmt = stmt.where(DistributionObservation.source_id == source_id)
        if distribution_type:
            stmt = stmt.where(DistributionObservation.distribution_type == distribution_type)
        if host:
            stmt = stmt.where(DistributionObservation.canonical_locator.ilike(f"%{host}%"))
        if date_from:
            stmt = stmt.where(DistributionObservation.observed_at >= date_from)
        if date_to:
            stmt = stmt.where(DistributionObservation.observed_at <= date_to)
        stmt = stmt.order_by(DistributionObservation.observed_at.desc()).limit(limit).offset(offset)
        r = await self.session.execute(stmt)
        return list(r.scalars().all())

    async def count_all(self, artifact_id=None, source_id=None, distribution_type=None, host=None, date_from=None, date_to=None) -> int:
        stmt = select(func.count(DistributionObservation.id))
        r = await self.session.execute(stmt)
        return r.scalar() or 0
