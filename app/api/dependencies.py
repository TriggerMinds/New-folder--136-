from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db as _get_db
from app.repositories.claims import ClaimRepository
from app.repositories.observations import ObservationRepository
from app.repositories.sources import SourceRepository
from app.repositories.audit import AuditRepository


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session


async def get_claim_repo(session: AsyncSession = Depends(get_db)) -> ClaimRepository:
    return ClaimRepository(session)


async def get_observation_repo(
    session: AsyncSession = Depends(get_db),
) -> ObservationRepository:
    return ObservationRepository(session)


async def get_source_repo(session: AsyncSession = Depends(get_db)) -> SourceRepository:
    return SourceRepository(session)


async def get_audit_repo(session: AsyncSession = Depends(get_db)) -> AuditRepository:
    return AuditRepository(session)
