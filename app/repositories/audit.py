from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.audit_event import AuditEvent


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append_audit_event(self, event: AuditEvent) -> AuditEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_audit_events(
        self, claim_id: UUID | None = None, limit: int = 100, offset: int = 0
    ) -> list[AuditEvent]:
        stmt = select(AuditEvent)
        if claim_id is not None:
            stmt = stmt.where(AuditEvent.claim_id == claim_id)
        stmt = stmt.order_by(AuditEvent.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_audit_events(self, claim_id: UUID | None = None) -> int:
        stmt = select(func.count(AuditEvent.id))
        if claim_id is not None:
            stmt = stmt.where(AuditEvent.claim_id == claim_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
