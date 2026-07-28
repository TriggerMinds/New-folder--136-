import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("observed_leak_claims.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash_sha256: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    discovery_method: Mapped[str] = mapped_column(String(50), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    connector_version: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )

    claim: Mapped["ObservedLeakClaim"] = relationship(
        back_populates="observations"
    )
    source: Mapped["Source | None"] = relationship(
        back_populates="observations"
    )
