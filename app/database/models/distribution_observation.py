import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DistributionObservation(Base):
    __tablename__ = "distribution_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_discovery_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("artifact_discoveries.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    locator: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_locator: Mapped[str] = mapped_column(Text, nullable=False)
    distribution_type: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
