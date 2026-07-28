from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SourceRunResponse(BaseModel):
    id: UUID
    source_id: UUID
    started_at: datetime
    completed_at: datetime | None
    success: bool
    items_seen: int
    items_matched: int
    claims_created: int
    claims_deduplicated: int
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceRunListResponse(BaseModel):
    items: list[SourceRunResponse]
    total: int
