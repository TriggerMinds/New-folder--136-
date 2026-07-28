import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ArtifactDiscovery(Base):
    __tablename__ = "artifact_discoveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    parent_claim_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    artifact_type: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    locator_type: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    original_locator: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_locator: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    final_locator: Mapped[str | None] = mapped_column(Text, nullable=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_extension: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    sha1: Mapped[str | None] = mapped_column(String(40), nullable=True)
    md5: Mapped[str | None] = mapped_column(String(32), nullable=True)
    magnet_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    torrent_infohash: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ipfs_cid: Mapped[str | None] = mapped_column(String(60), nullable=True)
    repository_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    repository_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    archive_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_date_precision: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    source_date_confidence: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    source_date_method: Mapped[str] = mapped_column(String(30), nullable=False, default="unavailable")
    source_date_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    freshness_classification: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    source_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    upload_date_method: Mapped[str] = mapped_column(String(30), nullable=False, default="unavailable")
    upload_date_confidence: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    upload_date_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    countries: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    eu_entities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    national_entities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    matched_terms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    raw_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    record_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalidation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_status: Mapped[str] = mapped_column(String(20), nullable=False, default="observed")
    acquisition_status: Mapped[str] = mapped_column(String(20), nullable=False, default="metadata_only")
    analysis_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now)

    acquisitions: Mapped[list["ArtifactAcquisition"]] = relationship(back_populates="artifact_discovery", cascade="all, delete-orphan")
