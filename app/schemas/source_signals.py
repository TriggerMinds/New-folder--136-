from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SourceSignalResponse(BaseModel):
    id: UUID
    source_id: UUID
    observed_at: datetime
    title: str | None
    url: str
    canonical_url: str
    content_excerpt: str | None
    source_role: str
    source_category: str
    matched_terms: list
    extracted_urls: list
    extracted_hashes: list
    extracted_magnet_links: list
    extracted_ipfs_cids: list
    extracted_file_names: list
    processing_status: str
    linked_claim_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceSignalListResponse(BaseModel):
    items: list[SourceSignalResponse]
    total: int
