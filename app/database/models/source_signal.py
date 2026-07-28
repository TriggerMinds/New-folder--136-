import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SourceSignal(Base):
    __tablename__ = "source_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_role: Mapped[str] = mapped_column(String(30), nullable=False)
    source_category: Mapped[str] = mapped_column(String(30), nullable=False)
    matched_terms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    extracted_urls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    extracted_hashes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    extracted_magnet_links: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    extracted_ipfs_cids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    extracted_file_names: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    processing_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_origin_resolution"
    )
    linked_claim_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now
    )

    source: Mapped["Source"] = relationship(
        back_populates="source_signals"
    )
