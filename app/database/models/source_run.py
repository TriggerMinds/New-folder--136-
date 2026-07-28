import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SourceRun(Base):
    __tablename__ = "source_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    run_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success"
    )
    items_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_matched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    artifact_items_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eu_entity_matches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leak_assertion_matches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    context_only_matches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    primary_claim_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    claims_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    claims_deduplicated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_signals_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    item_errors_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    item_errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )

    source: Mapped["Source"] = relationship(
        back_populates="source_runs"
    )
