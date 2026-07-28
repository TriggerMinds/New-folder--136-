from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.source_signal import SourceSignal
from app.repositories.source_signals import SourceSignalRepository
from app.services.url_normalization import normalize_url


async def create_source_signal(
    session: AsyncSession,
    source_id: UUID,
    title: str | None,
    url: str,
    content_excerpt: str | None,
    source_role: str,
    source_category: str,
    matched_terms: list[str] | None = None,
    extracted_urls: list[str] | None = None,
    extracted_hashes: list[str] | None = None,
    extracted_magnet_links: list[str] | None = None,
    extracted_ipfs_cids: list[str] | None = None,
    extracted_file_names: list[str] | None = None,
) -> SourceSignal:
    repo = SourceSignalRepository(session)
    signal = SourceSignal(
        source_id=source_id,
        observed_at=datetime.now(timezone.utc),
        title=title,
        url=url,
        canonical_url=normalize_url(url),
        content_excerpt=content_excerpt,
        source_role=source_role,
        source_category=source_category,
        matched_terms=matched_terms or [],
        extracted_urls=extracted_urls or [],
        extracted_hashes=extracted_hashes or [],
        extracted_magnet_links=extracted_magnet_links or [],
        extracted_ipfs_cids=extracted_ipfs_cids or [],
        extracted_file_names=extracted_file_names or [],
        processing_status="pending_origin_resolution",
    )
    return await repo.create_signal(signal)
