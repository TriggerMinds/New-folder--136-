from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.database.models.observed_leak_claim import AuthenticityStatus, ProvenanceStatus, ContentAccessStatus, AIEnrichmentStatus

EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


class ClaimCreate(BaseModel):
    title_original: str = Field(..., min_length=1)
    source_language: str | None = Field(None, min_length=2, max_length=10)
    summary: str | None = None
    claim_text: str | None = None
    countries: list[str] = Field(default_factory=list)
    eu_entities: list[str] = Field(default_factory=list)
    national_entities: list[str] = Field(default_factory=list)
    dossiers: list[str] = Field(default_factory=list)
    first_observed_url: str
    earliest_known_public_url: str | None = None
    claimed_origin_url: str | None = None
    confirmed_origin_url: str | None = None
    title_translated: str | None = None
    discovery_method: str = Field(default="manual", min_length=1)
    connector_type: str = Field(default="manual", min_length=1)
    connector_version: str = Field(default="0.1.0", min_length=1)
    http_status: int | None = None
    content_excerpt: str | None = None
    content_hash_sha256: str | None = Field(None, pattern=r"^[a-f0-9]{64}$")
    observed_at: datetime | None = None

    @field_validator("countries", mode="after")
    @classmethod
    def validate_countries(cls, v: list[str]) -> list[str]:
        for c in v:
            if len(c) != 2 or c != c.upper():
                raise ValueError(f"Ongeldige landcode: {c}. Gebruik hoofdletters van twee tekens.")
        return v

    @field_validator("first_observed_url", mode="after")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL moet beginnen met http:// of https://")
        return v


class ClaimResponse(BaseModel):
    id: UUID
    record_type: str
    first_observed_at: datetime
    last_observed_at: datetime
    title_original: str
    title_translated: str | None
    source_language: str | None
    summary: str | None
    claim_text: str | None
    countries: list
    eu_entities: list
    national_entities: list
    dossiers: list
    first_observed_url: str
    first_observed_host: str
    earliest_known_public_url: str | None
    earliest_known_public_host: str | None
    claimed_origin_url: str | None
    claimed_origin_host: str | None
    confirmed_origin_url: str | None
    confirmed_origin_host: str | None
    authenticity_status: AuthenticityStatus
    provenance_status: ProvenanceStatus
    content_access_status: ContentAccessStatus
    ai_enrichment_status: AIEnrichmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClaimListResponse(BaseModel):
    items: list[ClaimResponse]
    total: int
    limit: int
    offset: int


class ClaimUpdate(BaseModel):
    title_translated: str | None = None
    summary: str | None = None
    claim_text: str | None = None
    countries: list[str] | None = None
    eu_entities: list[str] | None = None
    national_entities: list[str] | None = None
    dossiers: list[str] | None = None
    earliest_known_public_url: str | None = None
    claimed_origin_url: str | None = None
    confirmed_origin_url: str | None = None
    authenticity_status: AuthenticityStatus | None = None
    provenance_status: ProvenanceStatus | None = None
    content_access_status: ContentAccessStatus | None = None
    ai_enrichment_status: AIEnrichmentStatus | None = None
