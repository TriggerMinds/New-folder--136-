from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ObservationCreate(BaseModel):
    claim_id: UUID
    source_id: UUID | None = None
    observed_at: datetime | None = None
    url: str
    canonical_url: str
    host: str
    http_status: int | None = None
    title: str | None = None
    content_excerpt: str | None = None
    content_hash_sha256: str | None = Field(None, pattern=r"^[a-f0-9]{64}$")
    discovery_method: str = Field(default="manual", min_length=1)
    connector_type: str = Field(default="manual", min_length=1)
    connector_version: str = Field(default="0.1.0", min_length=1)
    raw_metadata: dict = Field(default_factory=dict)

    @field_validator("url", "canonical_url", mode="after")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL moet beginnen met http:// of https://")
        return v


class ObservationResponse(BaseModel):
    id: UUID
    claim_id: UUID
    source_id: UUID | None
    observed_at: datetime
    url: str
    canonical_url: str
    host: str
    http_status: int | None
    title: str | None
    content_excerpt: str | None
    content_hash_sha256: str | None
    discovery_method: str
    connector_type: str
    connector_version: str
    raw_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ObservationListResponse(BaseModel):
    items: list[ObservationResponse]
    total: int
