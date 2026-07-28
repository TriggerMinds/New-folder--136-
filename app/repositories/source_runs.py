from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.source_run import SourceRun


class SourceRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_run(self, run: SourceRun) -> SourceRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_run(self, run_id: UUID) -> SourceRun | None:
        stmt = select(SourceRun).where(SourceRun.id == run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_runs(
        self,
        source_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SourceRun]:
        stmt = select(SourceRun)
        if source_id is not None:
            stmt = stmt.where(SourceRun.source_id == source_id)
        stmt = stmt.order_by(SourceRun.started_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_runs(self, source_id: UUID | None = None) -> int:
        stmt = select(func.count(SourceRun.id))
        if source_id is not None:
            stmt = stmt.where(SourceRun.source_id == source_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_run(self, run: SourceRun) -> SourceRun:
        self.session.add(run)
        await self.session.flush()
        return run
