from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.observed_leak_claim import ObservedLeakClaim


class ClaimRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_claim(self, claim: ObservedLeakClaim) -> ObservedLeakClaim:
        self.session.add(claim)
        await self.session.flush()
        return claim

    async def get_claim(self, claim_id: UUID) -> ObservedLeakClaim | None:
        stmt = select(ObservedLeakClaim).where(ObservedLeakClaim.id == claim_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_claims_chronological(
        self,
        limit: int = 50,
        offset: int = 0,
        country: str | None = None,
        language: str | None = None,
        host: str | None = None,
        dossier: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[ObservedLeakClaim]:
        stmt = select(ObservedLeakClaim)
        conditions = []
        if country:
            conditions.append(ObservedLeakClaim.countries.any(country))
        if language:
            conditions.append(ObservedLeakClaim.source_language == language)
        if host:
            conditions.append(ObservedLeakClaim.first_observed_host == host)
        if dossier:
            conditions.append(ObservedLeakClaim.dossiers.any(dossier))
        if date_from:
            conditions.append(ObservedLeakClaim.first_observed_at >= date_from)
        if date_to:
            conditions.append(ObservedLeakClaim.first_observed_at <= date_to)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(ObservedLeakClaim.first_observed_at.desc(), ObservedLeakClaim.id.desc())
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_claims(
        self,
        country: str | None = None,
        language: str | None = None,
        host: str | None = None,
        dossier: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        stmt = select(func.count(ObservedLeakClaim.id))
        conditions = []
        if country:
            conditions.append(ObservedLeakClaim.countries.any(country))
        if language:
            conditions.append(ObservedLeakClaim.source_language == language)
        if host:
            conditions.append(ObservedLeakClaim.first_observed_host == host)
        if dossier:
            conditions.append(ObservedLeakClaim.dossiers.any(dossier))
        if date_from:
            conditions.append(ObservedLeakClaim.first_observed_at >= date_from)
        if date_to:
            conditions.append(ObservedLeakClaim.first_observed_at <= date_to)
        if conditions:
            stmt = stmt.where(*conditions)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_claim(self, claim: ObservedLeakClaim) -> ObservedLeakClaim:
        self.session.add(claim)
        await self.session.flush()
        return claim
