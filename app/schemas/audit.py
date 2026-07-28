from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AuditEventCreate(BaseModel):
    claim_id: UUID | None = None
    event_type: str = Field(..., min_length=1)
    actor: str = Field(default="system", min_length=1)
    reason: str | None = None
    field_name: str | None = None
    old_value: dict | None = None
    new_value: dict | None = None


class AuditEventResponse(BaseModel):
    id: UUID
    claim_id: UUID | None
    timestamp: datetime
    event_type: str
    actor: str
    reason: str | None
    field_name: str | None
    old_value: dict | None
    new_value: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int
