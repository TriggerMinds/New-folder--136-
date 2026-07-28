import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SourceRole(str, enum.Enum):
    ORIGIN_CANDIDATE = "origin_candidate"
    DISTRIBUTION = "distribution"
    ARCHIVE = "archive"
    MIRROR = "mirror"
    SIGNAL = "signal"
    CONFIRMATION = "confirmation"
    OFFICIAL_RESPONSE = "official_response"


class SourceCategory(str, enum.Enum):
    LEAK_ARCHIVE = "leak_archive"
    DOCUMENT_ARCHIVE = "document_archive"
    DATASET_INDEX = "dataset_index"
    GIT_HOST = "git_host"
    FILE_HOST = "file_host"
    TORRENT_INDEX = "torrent_index"
    IPFS_INDEX = "ipfs_index"
    PUBLIC_CHANNEL = "public_channel"
    PASTE_SITE = "paste_site"
    WEB_ARCHIVE = "web_archive"
    WHISTLEBLOWER_PLATFORM = "whistleblower_platform"
    SPECIALIST_BLOG = "specialist_blog"
    MAINSTREAM_MEDIA = "mainstream_media"
    GOVERNMENT = "government"
    PARLIAMENT = "parliament"


class DiscoveryPriority(str, enum.Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    LOW = "low"


_PRIMARY_ROLES = {SourceRole.ORIGIN_CANDIDATE, SourceRole.DISTRIBUTION, SourceRole.ARCHIVE, SourceRole.MIRROR}
_SIGNAL_ROLES = {SourceRole.SIGNAL}
_NON_PRIMARY_CATEGORIES = {SourceCategory.MAINSTREAM_MEDIA, SourceCategory.GOVERNMENT, SourceCategory.PARLIAMENT}


def default_can_create_primary_claim(role: SourceRole | None, category: SourceCategory | None) -> bool:
    if role in _PRIMARY_ROLES:
        return True
    if role in _SIGNAL_ROLES:
        return True
    if role == SourceRole.CONFIRMATION:
        return False
    if role == SourceRole.OFFICIAL_RESPONSE:
        return False
    if category in _NON_PRIMARY_CATEGORIES:
        return False
    return True


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str] = mapped_column(
        String(2), nullable=False, index=True
    )
    languages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_role: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SourceRole.SIGNAL.value
    )
    source_category: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SourceCategory.SPECIALIST_BLOG.value
    )
    can_create_primary_claim: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    discovery_priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default=DiscoveryPriority.SECONDARY.value
    )
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    poll_url: Mapped[str] = mapped_column(Text, nullable=False)
    connector_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    country_pack_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    poll_interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now
    )

    observations: Mapped[list["Observation"]] = relationship(
        back_populates="source"
    )
    source_runs: Mapped[list["SourceRun"]] = relationship(
        back_populates="source"
    )
    source_signals: Mapped[list["SourceSignal"]] = relationship(
        back_populates="source"
    )
