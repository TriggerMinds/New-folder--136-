from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation


class ArtifactDiscoveryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_discovery(self, discovery: ArtifactDiscovery) -> ArtifactDiscovery:
        self.session.add(discovery)
        await self.session.flush()
        return discovery

    async def get_discovery(self, discovery_id: UUID) -> ArtifactDiscovery | None:
        stmt = select(ArtifactDiscovery).where(ArtifactDiscovery.id == discovery_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_discoveries(
        self,
        limit: int = 100,
        offset: int = 0,
        artifact_type: str | None = None,
        locator_type: str | None = None,
        host: str | None = None,
    ) -> list[ArtifactDiscovery]:
        stmt = select(ArtifactDiscovery)
        if artifact_type:
            stmt = stmt.where(ArtifactDiscovery.artifact_type == artifact_type)
        if locator_type:
            stmt = stmt.where(ArtifactDiscovery.locator_type == locator_type)
        if host:
            stmt = stmt.where(ArtifactDiscovery.host == host)
        stmt = stmt.order_by(ArtifactDiscovery.first_observed_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_discoveries(self) -> int:
        stmt = select(func.count(ArtifactDiscovery.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_discovery(self, discovery: ArtifactDiscovery) -> ArtifactDiscovery:
        self.session.add(discovery)
        await self.session.flush()
        return discovery


class DistributionObservationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_observation(self, obs: DistributionObservation) -> DistributionObservation:
        self.session.add(obs)
        await self.session.flush()
        return obs

    async def list_for_artifact(self, artifact_id: UUID) -> list[DistributionObservation]:
        stmt = select(DistributionObservation).where(DistributionObservation.artifact_discovery_id == artifact_id).order_by(DistributionObservation.observed_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
