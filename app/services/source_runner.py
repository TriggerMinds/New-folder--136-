from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.connectors.registry import get_connector
from app.country_packs.loader import load_country_pack
from app.database.models.source import Source
from app.database.models.source_run import SourceRun
from app.repositories.source_runs import SourceRunRepository
from app.repositories.sources import SourceRepository
from app.services.claim_registration import register_observed_leak_claim
from app.services.leak_signal_detection import detect_leak_signal
from app.services.artifact_indicator_extraction import extract_artifacts
from app.services.source_signal import create_source_signal
from app.services.artifact_indicator_extraction import extract_artifacts, extract_file_names


class SourceRunResult:
    def __init__(self):
        self.source_id: UUID | None = None
        self.source_external_id: str | None = None
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.success: bool = False
        self.items_seen: int = 0
        self.items_matched: int = 0
        self.claims_created: int = 0
        self.claims_deduplicated: int = 0
        self.signals_created: int = 0
        self.error: str | None = None


class BatchSourceRunResult:
    def __init__(self):
        self.results: list[SourceRunResult] = []
        self.total_sources: int = 0
        self.successful: int = 0
        self.failed: int = 0


async def run_source(source_id: UUID, db: AsyncSession) -> SourceRunResult:
    result = SourceRunResult()
    repo = SourceRepository(db)
    run_repo = SourceRunRepository(db)

    source = await repo.get_source(source_id)
    if source is None:
        result.error = f"Bron niet gevonden: {source_id}"
        return result

    result.source_id = source.id
    result.source_external_id = source.external_id
    result.started_at = datetime.now(timezone.utc)

    run_record = SourceRun(
        source_id=source.id,
        started_at=result.started_at,
        items_seen=1,
        error="pending",
    )
    run_record = await run_repo.create_run(run_record)

    try:
        source.last_checked_at = datetime.now(timezone.utc)
        await repo.update_source_status(source, last_checked_at=source.last_checked_at)

        connector = get_connector(source.source_type)
        conn_result = await connector.fetch(source)

        if conn_result.error:
            result.error = conn_result.error
            source.last_error_at = datetime.now(timezone.utc)
            source.last_error = str(conn_result.error)[:1000]
            source.consecutive_failures = (source.consecutive_failures or 0) + 1
            await repo.update_source_status(
                source, last_error_at=source.last_error_at, last_error=source.last_error,
                consecutive_failures=source.consecutive_failures,
            )
            run_record.completed_at = datetime.now(timezone.utc)
            run_record.success = False
            run_record.error = str(conn_result.error)[:1000]
            await run_repo.update_run(run_record)
            result.completed_at = run_record.completed_at
            return result

        pack = load_country_pack(source.country_code)
        terms = []
        if pack.leak_terms and pack.leak_terms.terms:
            terms = [t.term for t in pack.leak_terms.terms]

        result.items_seen = len(conn_result.items)
        run_record.items_seen = result.items_seen
        can_create = source.can_create_primary_claim
        role = source.source_role
        cat = source.source_category

        for item in conn_result.items:
            signal = detect_leak_signal(item.title, item.content, terms)
            if not signal.matched:
                continue
            result.items_matched += 1
            artifacts = extract_artifacts(item.content or "")
            artifacts2 = extract_artifacts(item.title or "")
            all_urls = list(set(artifacts.urls + artifacts2.urls))
            all_repo_urls = list(set(artifacts.repository_urls + artifacts2.repository_urls))
            all_dl_urls = list(set(artifacts.download_urls + artifacts2.download_urls))
            all_hashes = list(set(artifacts.sha256_hashes + artifacts.sha1_hashes + artifacts.md5_hashes))
            all_magnets = list(set(artifacts.magnet_links + artifacts2.magnet_links))
            all_cids = list(set(artifacts.ipfs_cids + artifacts2.ipfs_cids))
            all_files = list(set(extract_file_names(item.content) + extract_file_names(item.title)))
            has_origin = bool(all_urls or all_repo_urls or all_dl_urls or all_hashes or all_magnets or all_cids or all_files)

            if can_create:
                try:
                    reg_result = await register_observed_leak_claim(
                        session=db,
                        title_original=item.title or "Untitled",
                        first_observed_url=item.url,
                        source_language=item.language or source.country_code.lower(),
                        summary=item.content_excerpt,
                        claim_text=item.content,
                        countries=[source.country_code],
                        discovery_method="connector",
                        connector_type=source.source_type,
                        connector_version="0.1.0",
                        content_excerpt=item.content_excerpt,
                        observed_at=item.observed_at,
                        source_id=source.id,
                        raw_metadata={**item.raw_metadata, "source_role": role, "source_category": cat},
                    )
                    if reg_result.is_new:
                        result.claims_created += 1
                    else:
                        result.claims_deduplicated += 1
                except Exception:
                    continue
            else:
                if has_origin:
                    try:
                        reg_result = await register_observed_leak_claim(
                            session=db,
                            title_original=item.title or "Untitled",
                            first_observed_url=item.url,
                            source_language=item.language or source.country_code.lower(),
                            summary=item.content_excerpt,
                            claim_text=item.content,
                            countries=[source.country_code],
                            discovery_method="connector",
                            connector_type=source.source_type,
                            connector_version="0.1.0",
                            content_excerpt=item.content_excerpt,
                            observed_at=item.observed_at,
                            source_id=source.id,
                            raw_metadata={**item.raw_metadata, "source_role": role, "source_category": cat},
                        )
                        if reg_result.is_new:
                            result.claims_created += 1
                        else:
                            result.claims_deduplicated += 1
                    except Exception:
                        continue
                else:
                    try:
                        await create_source_signal(
                            session=db,
                            source_id=source.id,
                            title=item.title,
                            url=item.url,
                            content_excerpt=item.content_excerpt,
                            source_role=role,
                            source_category=cat,
                            matched_terms=signal.matched_terms,
                            extracted_urls=all_urls + all_repo_urls + all_dl_urls,
                            extracted_hashes=all_hashes,
                            extracted_magnet_links=all_magnets,
                            extracted_ipfs_cids=all_cids,
                            extracted_file_names=all_files,
                        )
                        result.signals_created += 1
                    except Exception:
                        continue

        source.last_success_at = datetime.now(timezone.utc)
        source.consecutive_failures = 0
        await repo.update_source_status(source, last_success_at=source.last_success_at, consecutive_failures=0)
        result.success = True
        run_record.success = True
        run_record.items_matched = result.items_matched
        run_record.claims_created = result.claims_created
        run_record.claims_deduplicated = result.claims_deduplicated

    except Exception as e:
        result.error = str(e)
        source.last_error_at = datetime.now(timezone.utc)
        source.last_error = str(e)[:1000]
        source.consecutive_failures = (source.consecutive_failures or 0) + 1
        await repo.update_source_status(source, last_error_at=source.last_error_at, last_error=source.last_error, consecutive_failures=source.consecutive_failures)
        run_record.error = str(e)[:1000]
        run_record.success = False

    run_record.completed_at = datetime.now(timezone.utc)
    await run_repo.update_run(run_record)
    result.completed_at = run_record.completed_at
    return result


async def run_enabled_sources(
    db: AsyncSession,
    country_code: str | None = None,
    source_type: str | None = None,
) -> BatchSourceRunResult:
    batch = BatchSourceRunResult()
    stmt = select(Source).where(Source.enabled.is_(True))
    if country_code:
        stmt = stmt.where(Source.country_code == country_code)
    if source_type:
        stmt = stmt.where(Source.source_type == source_type)
    sources = await db.execute(stmt)
    all_sources = list(sources.scalars().all())
    batch.total_sources = len(all_sources)
    for source in all_sources:
        try:
            sr = await run_source(source.id, db)
            batch.results.append(sr)
            if sr.success:
                batch.successful += 1
            else:
                batch.failed += 1
        except Exception:
            batch.failed += 1
    return batch
