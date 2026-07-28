import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SAEnum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AuthenticityStatus(str, enum.Enum):
    UNEXAMINED = "unexamined"
    VERIFIED_AUTHENTIC = "verified_authentic"
    LIKELY_AUTHENTIC = "likely_authentic"
    LIKELY_FABRICATED = "likely_fabricated"
    CONFIRMED_FABRICATED = "confirmed_fabricated"
    DISPUTED = "disputed"
    UNVERIFIABLE = "unverifiable"


class ProvenanceStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    TRACED = "traced"
    PARTIALLY_TRACED = "partially_traced"
    ATTRIBUTED = "attributed"
    CONFIRMED_ANONYMOUS = "confirmed_anonymous"
    CONFIRMED_WHISTLEBLOWER = "confirmed_whistleblower"
    CONFIRMED_STATE_ACTOR = "confirmed_state_actor"


class ContentAccessStatus(str, enum.Enum):
    PUBLIC = "public"
    PAYWALLED = "paywalled"
    RESTRICTED = "restricted"
    DELETED = "deleted"
    UNAVAILABLE = "unavailable"


class AIEnrichmentStatus(str, enum.Enum):
    PENDING = "pending"
    ENRICHED = "enriched"
    FAILED = "failed"
    SKIPPED = "skipped"


class ObservedLeakClaim(Base):
    __tablename__ = "observed_leak_claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    record_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="observed_leak_claim", server_default="observed_leak_claim"
    )
    first_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    last_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    title_original: Mapped[str] = mapped_column(Text, nullable=False)
    title_translated: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    claim_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    countries: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    eu_entities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    national_entities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    dossiers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    first_observed_url: Mapped[str] = mapped_column(Text, nullable=False)
    first_observed_host: Mapped[str] = mapped_column(String(255), nullable=False)
    earliest_known_public_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    earliest_known_public_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claimed_origin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_origin_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed_origin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_origin_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    authenticity_status: Mapped[AuthenticityStatus] = mapped_column(
        SAEnum(AuthenticityStatus, values_callable=lambda x: [e.value for e in x], name="authenticity_status", create_type=False),
        nullable=False,
        default=AuthenticityStatus.UNEXAMINED,
        server_default=AuthenticityStatus.UNEXAMINED.value,
    )
    provenance_status: Mapped[ProvenanceStatus] = mapped_column(
        SAEnum(ProvenanceStatus, values_callable=lambda x: [e.value for e in x], name="provenance_status", create_type=False),
        nullable=False,
        default=ProvenanceStatus.UNKNOWN,
        server_default=ProvenanceStatus.UNKNOWN.value,
    )
    content_access_status: Mapped[ContentAccessStatus] = mapped_column(
        SAEnum(ContentAccessStatus, values_callable=lambda x: [e.value for e in x], name="content_access_status", create_type=False),
        nullable=False,
        default=ContentAccessStatus.PUBLIC,
        server_default=ContentAccessStatus.PUBLIC.value,
    )
    ai_enrichment_status: Mapped[AIEnrichmentStatus] = mapped_column(
        SAEnum(AIEnrichmentStatus, values_callable=lambda x: [e.value for e in x], name="ai_enrichment_status", create_type=False),
        nullable=False,
        default=AIEnrichmentStatus.PENDING,
        server_default=AIEnrichmentStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now
    )

    observations: Mapped[list["Observation"]] = relationship(
        back_populates="claim",
        cascade="save-update, merge",
        passive_deletes=True,
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        back_populates="claim",
        cascade="save-update, merge",
        passive_deletes=True,
    )
