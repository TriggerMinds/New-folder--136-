from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation


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
        r = await self.session.execute(
            select(ArtifactDiscovery).where(
                ArtifactDiscovery.filename == filename,
                ArtifactDiscovery.host == host,
            ).limit(1)
        )
        return r.scalar_one_or_none()

    async def list_discoveries(self, limit: int = 100, offset: int = 0,
                                artifact_type: str | None = None, host: str | None = None) -> list[ArtifactDiscovery]:
        stmt = select(ArtifactDiscovery)
        if artifact_type:
            stmt = stmt.where(ArtifactDiscovery.artifact_type == artifact_type)
        if host:
            stmt = stmt.where(ArtifactDiscovery.host == host)
        stmt = stmt.order_by(ArtifactDiscovery.first_observed_at.desc()).limit(limit).offset(offset)
        r = await self.session.execute(stmt)
        return list(r.scalars().all())

    async def count_discoveries(self) -> int:
        r = await self.session.execute(select(func.count(ArtifactDiscovery.id)))
        return r.scalar() or 0

    async def update_discovery(self, d: ArtifactDiscovery) -> ArtifactDiscovery:
        self.session.add(d)
        await self.session.flush()
        return d

    async def delete_discovery(self, did: UUID) -> None:
        await self.session.execute(select(ArtifactDiscovery).where(ArtifactDiscovery.id == did))
        await self.session.flush()


class DistributionObservationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_observation(self, o: DistributionObservation) -> DistributionObservation:
        self.session.add(o)
        await self.session.flush()
        return o

    async def list_for_artifact(self, aid: UUID) -> list[DistributionObservation]:
        r = await self.session.execute(
            select(DistributionObservation).where(DistributionObservation.artifact_discovery_id == aid).order_by(DistributionObservation.observed_at.desc())
        )
        return list(r.scalars().all())

    async def exists(self, artifact_id: UUID, source_id: object, canonical_locator: str) -> bool:
        r = await self.session.execute(
            select(func.count(DistributionObservation.id)).where(
                DistributionObservation.artifact_discovery_id == artifact_id,
                DistributionObservation.source_id == source_id,
                DistributionObservation.canonical_locator == canonical_locator,
            )
        )
        return (r.scalar() or 0) > 0
