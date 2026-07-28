from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.audit_event import AuditEvent
from app.repositories.audit import AuditRepository


async def append_audit_event(
    session: AsyncSession,
    event_type: str,
    actor: str = "system",
    claim_id: UUID | None = None,
    reason: str | None = None,
    field_name: str | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
) -> AuditEvent:
    repo = AuditRepository(session)
    event = AuditEvent(
        claim_id=claim_id,
        event_type=event_type,
        actor=actor,
        reason=reason,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
    )
    return await repo.append_audit_event(event)
