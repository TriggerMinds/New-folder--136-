from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.observation import Observation


class ObservationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_observation(self, observation: Observation) -> Observation:
        self.session.add(observation)
        await self.session.flush()
        return observation

    async def get_observation(self, observation_id: UUID) -> Observation | None:
        stmt = select(Observation).where(Observation.id == observation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_observations_for_claim(
        self, claim_id: UUID
    ) -> list[Observation]:
        stmt = (
            select(Observation)
            .where(Observation.claim_id == claim_id)
            .order_by(Observation.observed_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_observations_for_claim(self, claim_id: UUID) -> int:
        stmt = select(func.count(Observation.id)).where(
            Observation.claim_id == claim_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def find_by_canonical_url(self, canonical_url: str) -> Observation | None:
        stmt = select(Observation).where(
            Observation.canonical_url == canonical_url
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_content_hash(
        self, content_hash: str
    ) -> Observation | None:
        stmt = select(Observation).where(
            Observation.content_hash_sha256 == content_hash
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
