import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ArtifactAcquisition(Base):
    __tablename__ = "artifact_acquisitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_discovery_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("artifact_discoveries.id", ondelete="RESTRICT"), nullable=False, index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(25), nullable=False, default="requested")
    requested_locator: Mapped[str] = mapped_column(Text, nullable=False)
    final_locator: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_content_length: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    downloaded_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    calculated_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now)

    artifact_discovery: Mapped["ArtifactDiscovery"] = relationship(back_populates="acquisitions")
