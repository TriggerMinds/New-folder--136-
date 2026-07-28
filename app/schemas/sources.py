from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SourceCreate(BaseModel):
    external_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    country_code: str = Field(..., min_length=2, max_length=2)
    languages: list[str] = Field(default_factory=list)
    source_type: str = Field(..., min_length=1)
    base_url: str
    poll_url: str
    enabled: bool = True
    poll_interval_minutes: int = Field(default=30, ge=5)

    @field_validator("country_code", mode="after")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        if len(v) != 2 or v != v.upper():
            raise ValueError("Landcode moet uit twee hoofdletters bestaan")
        return v

    @field_validator("base_url", "poll_url", mode="after")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL moet beginnen met http:// of https://")
        return v


class SourceResponse(BaseModel):
    id: UUID
    external_id: str
    name: str
    country_code: str
    languages: list
    source_type: str
    source_layer: str
    source_role: str
    source_category: str
    discovery_priority: str
    can_create_primary_claim: bool
    can_create_artifact_discovery: bool
    can_create_reference_observation: bool
    lifecycle_status: str
    present_in_country_pack: bool
    disabled_reason: str | None = None
    base_url: str
    poll_url: str
    connector_config: dict
    country_pack_version: str | None = None
    enabled: bool
    poll_interval_minutes: int
    last_checked_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error_at: datetime | None = None
    last_error: str | None = None
    consecutive_failures: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class SourceListResponse(BaseModel):
    items: list[SourceResponse]
    total: int
