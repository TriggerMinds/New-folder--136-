from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DiscoveredItem(BaseModel):
    source_external_id: str
    observed_at: datetime = Field(default_factory=datetime.now)
    url: str
    title: str | None = None
    content: str | None = None
    content_excerpt: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    raw_metadata: dict = Field(default_factory=dict)


class ConnectorResult(BaseModel):
    source_id: UUID | None = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    items: list[DiscoveredItem] = Field(default_factory=list)
    success: bool = False
    error: str | None = None
    http_status: int | None = None
