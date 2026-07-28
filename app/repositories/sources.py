from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.source import Source


class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_source(self, source: Source) -> Source:
        self.session.add(source)
        await self.session.flush()
        return source

    async def get_source(self, source_id: UUID) -> Source | None:
        stmt = select(Source).where(Source.id == source_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sources(
        self, limit: int = 100, offset: int = 0, enabled_only: bool = False
    ) -> list[Source]:
        stmt = select(Source)
        if enabled_only:
            stmt = stmt.where(Source.enabled.is_(True))
        stmt = stmt.order_by(Source.name).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_sources(self, enabled_only: bool = False) -> int:
        stmt = select(func.count(Source.id))
        if enabled_only:
            stmt = stmt.where(Source.enabled.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_source_status(
        self,
        source: Source,
        *,
        last_checked_at: object | None = None,
        last_success_at: object | None = None,
        last_error_at: object | None = None,
        last_error: str | None = None,
        consecutive_failures: int | None = None,
    ) -> Source:
        if last_checked_at is not None:
            source.last_checked_at = last_checked_at
        if last_success_at is not None:
            source.last_success_at = last_success_at
        if last_error_at is not None:
            source.last_error_at = last_error_at
        if last_error is not None:
            source.last_error = last_error
        if consecutive_failures is not None:
            source.consecutive_failures = consecutive_failures
        self.session.add(source)
        await self.session.flush()
        return source
