from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.source_signal import SourceSignal


class SourceSignalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_signal(self, signal: SourceSignal) -> SourceSignal:
        self.session.add(signal)
        await self.session.flush()
        return signal

    async def get_signal(self, signal_id: UUID) -> SourceSignal | None:
        stmt = select(SourceSignal).where(SourceSignal.id == signal_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_signals(
        self,
        processing_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SourceSignal]:
        stmt = select(SourceSignal)
        if processing_status:
            stmt = stmt.where(SourceSignal.processing_status == processing_status)
        stmt = stmt.order_by(SourceSignal.observed_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_signals(self, processing_status: str | None = None) -> int:
        stmt = select(func.count(SourceSignal.id))
        if processing_status:
            stmt = stmt.where(SourceSignal.processing_status == processing_status)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_signal(self, signal: SourceSignal) -> SourceSignal:
        self.session.add(signal)
        await self.session.flush()
        return signal
