from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.registry import get_connector
from app.country_packs.loader import load_country_pack
from app.database.models.source import Source
from app.database.models.source_run import SourceRun
from app.repositories.source_runs import SourceRunRepository
from app.repositories.sources import SourceRepository
from app.services.claim_registration import register_observed_leak_claim
from app.services.leak_signal_detection import detect_leak_signal, has_claim_quality
from app.services.artifact_indicator_extraction import extract_artifacts, extract_file_names, has_concrete_origin_indicator
from app.services.source_signal import create_source_signal
from app.services.origin_validation import validate_origin_candidate


class ItemError:
    def __init__(self, url: str, title: str, stage: str, message: str, exc_type: str = ""):
        self.url = url
        self.title = title
        self.stage = stage
        self.message = message
        self.exception_type = exc_type

    def to_dict(self) -> dict:
        return {
            "url": self.url[:500],
            "title": (self.title or "")[:200],
            "stage": self.stage,
            "exception_type": self.exception_type,
            "message": self.message[:500],
        }


class SourceRunResult:
    def __init__(self):
        self.source_id: UUID | None = None
        self.source_external_id: str | None = None
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.success: bool = False
        self.run_status: str = "failed"
        self.items_seen: int = 0
        self.artifact_items_seen: int = 0
        self.items_matched: int = 0
        self.eu_entity_matches: int = 0
        self.leak_assertion_matches: int = 0
        self.context_only_matches: int = 0
        self.primary_claim_candidates: int = 0
        self.claims_created: int = 0
        self.claims_deduplicated: int = 0
        self.signals_created: int = 0
        self.item_errors: list[dict] = []
        self.error: str | None = None


def _resolve_language(source: Source, pack, item_lang: str | None) -> str | None:
    if item_lang:
        return item_lang
    if source.languages:
        return source.languages[0]
    if pack and pack.languages:
        for lang in pack.languages.languages:
            if lang.primary:
                return lang.code
    return None


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

    run_record = SourceRun(source_id=source.id, started_at=result.started_at, items_seen=1, error="pending")
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
            await repo.update_source_status(source, last_error_at=source.last_error_at, last_error=source.last_error, consecutive_failures=source.consecutive_failures)
            run_record.completed_at = datetime.now(timezone.utc)
            run_record.success = False
            run_record.run_status = "failed"
            run_record.error = str(conn_result.error)[:1000]
            await run_repo.update_run(run_record)
            result.completed_at = run_record.completed_at
            return result

        pack = load_country_pack(source.country_code)
        context_terms = [t.term for t in (pack.context_terms.context_terms if pack.context_terms else [])]
        assertion_terms = [t.term for t in (pack.leak_assertion_terms.leak_assertion_terms if pack.leak_assertion_terms else [])]

        result.items_seen = len(conn_result.items)
        run_record.items_seen = result.items_seen

        for item in conn_result.items:
            item_errors_before = len(result.item_errors)
            try:
                signal = detect_leak_signal(item.title, item.content, context_terms, assertion_terms)
                if not signal.matched:
                    continue
                result.items_matched += 1

                if signal.assertion_matched_terms:
                    result.leak_assertion_matches += 1
                if signal.context_matched_terms and not signal.assertion_matched_terms:
                    result.context_only_matches += 1

                artifacts = extract_artifacts(item.content, source.poll_url)
                artifacts2 = extract_artifacts(item.title, source.poll_url)
                all_artifact_urls = list(set(
                    artifacts.repository_urls + artifacts.direct_download_urls
                    + artifacts.archive_urls + artifacts.mirror_urls
                    + artifacts2.repository_urls + artifacts2.direct_download_urls
                    + artifacts2.archive_urls + artifacts2.mirror_urls
                ))
                all_external_urls = list(set(
                    artifacts.external_urls + artifacts2.external_urls
                ))
                all_self_urls = list(set(
                    artifacts.source_self_urls + artifacts2.source_self_urls
                ))
                all_hashes = list(set(
                    artifacts.cryptographic_hashes + artifacts2.cryptographic_hashes
                ))
                all_magnets = list(set(artifacts.magnet_links + artifacts2.magnet_links))
                all_cids = list(set(artifacts.ipfs_cids + artifacts2.ipfs_cids))
                all_files = list(set(extract_file_names(item.content) + extract_file_names(item.title)))

                has_origin = artifacts.has_concrete() or artifacts2.has_concrete()

                if has_origin:
                    result.artifact_items_seen += 1

                role = source.source_role
                cat = source.source_category
                can_create = source.can_create_primary_claim

                claim_quality, quality_reason = has_claim_quality(signal, has_origin, can_create, role)

                if claim_quality:
                    result.primary_claim_candidates += 1
                    origin_url = item.url

                    if can_create and role in ("origin_candidate", "distribution", "archive", "mirror"):
                        pass
                    elif all_artifact_urls:
                        origin_url = all_artifact_urls[0]
                    elif not can_create and has_origin and all_artifact_urls:
                        origin_url = all_artifact_urls[0]

                    lang = _resolve_language(source, pack, item.language)

                    try:
                        reg_result = await register_observed_leak_claim(
                            session=db,
                            title_original=item.title or "Untitled",
                            first_observed_url=origin_url,
                            earliest_known_public_url=origin_url if origin_url != item.url else None,
                            source_language=lang,
                            summary=item.content_excerpt,
                            claim_text=item.content,
                            countries=[source.country_code],
                            discovery_method="connector",
                            connector_type=source.source_type,
                            connector_version="0.1.0",
                            content_excerpt=item.content_excerpt,
                            observed_at=item.observed_at,
                            source_id=source.id,
                            raw_metadata={
                                **item.raw_metadata,
                                "source_role": role, "source_category": cat,
                                "assertion_terms": signal.assertion_matched_terms,
                                "context_terms": signal.context_matched_terms,
                                "has_origin": has_origin, "quality_reason": quality_reason,
                            },
                        )
                        if reg_result.is_new:
                            result.claims_created += 1
                        else:
                            result.claims_deduplicated += 1

                        if not can_create and origin_url != item.url:
                            from app.database.models.observation import Observation
                            obs = Observation(
                                claim_id=reg_result.claim.id,
                                source_id=source.id,
                                observed_at=item.observed_at,
                                url=item.url,
                                canonical_url=__import__("app.services.url_normalization", fromlist=["normalize_url"]).normalize_url(item.url),
                                host=__import__("urllib.parse", fromlist=["urlparse"]).urlparse(item.url).hostname or "unknown",
                                title=item.title,
                                content_excerpt=item.content_excerpt,
                                discovery_method="connector",
                                connector_type=source.source_type,
                                connector_version="0.1.0",
                                raw_metadata={"relation_type": "confirmation_reference"},
                            )
                            db.add(obs)
                    except Exception as e:
                        result.item_errors.append(ItemError(item.url, item.title, "claim_registration", str(e), type(e).__name__).to_dict())

                elif has_origin and not can_create:
                    result.primary_claim_candidates += 1
                    origin_url = all_artifact_urls[0] if all_artifact_urls else item.url
                    ov = await validate_origin_candidate(origin_url)
                    if ov.reachable:
                        try:
                            reg_result = await register_observed_leak_claim(
                                session=db,
                                title_original=item.title or "Untitled",
                                first_observed_url=origin_url,
                                source_language=_resolve_language(source, pack, item.language),
                                summary=item.content_excerpt,
                                claim_text=item.content,
                                countries=[source.country_code],
                                discovery_method="connector",
                                connector_type=source.source_type,
                                connector_version="0.1.0",
                                content_excerpt=item.content_excerpt,
                                observed_at=item.observed_at,
                                source_id=source.id,
                                raw_metadata={**item.raw_metadata, "source_role": role, "source_category": cat, "origin_validation": ov.validation_error},
                            )
                            if reg_result.is_new:
                                result.claims_created += 1
                            else:
                                result.claims_deduplicated += 1
                        except Exception as e:
                            result.item_errors.append(ItemError(item.url, item.title, "origin_claim", str(e), type(e).__name__).to_dict())
                    else:
                        try:
                            await create_source_signal(
                                session=db, source_id=source.id,
                                title=item.title, url=item.url, content_excerpt=item.content_excerpt,
                                source_role=role, source_category=cat,
                                matched_terms=signal.assertion_matched_terms + signal.context_matched_terms,
                                extracted_urls=all_artifact_urls + all_external_urls,
                                extracted_hashes=all_hashes,
                                extracted_magnet_links=all_magnets,
                                extracted_ipfs_cids=all_cids,
                                extracted_file_names=all_files,
                            )
                            result.signals_created += 1
                        except Exception as e:
                            result.item_errors.append(ItemError(item.url, item.title, "signal_create", str(e), type(e).__name__).to_dict())
                else:
                    try:
                        await create_source_signal(
                            session=db, source_id=source.id,
                            title=item.title, url=item.url, content_excerpt=item.content_excerpt,
                            source_role=role, source_category=cat,
                            matched_terms=signal.context_matched_terms,
                            extracted_urls=all_external_urls,
                            extracted_hashes=all_hashes,
                        )
                        result.signals_created += 1
                    except Exception as e:
                        result.item_errors.append(ItemError(item.url, item.title, "signal_create_context", str(e), type(e).__name__).to_dict())

                if len(result.item_errors) > item_errors_before:
                    pass

            except Exception as e:
                result.item_errors.append(ItemError(
                    getattr(item, "url", "unknown"), getattr(item, "title", "unknown"),
                    "item_processing", str(e), type(e).__name__
                ).to_dict())

        source.last_success_at = datetime.now(timezone.utc)
        source.consecutive_failures = 0
        await repo.update_source_status(source, last_success_at=source.last_success_at, consecutive_failures=0)
        result.success = True
        result.run_status = "partial_success" if result.item_errors else "success"
        run_record.success = True
        run_record.run_status = result.run_status
        run_record.items_matched = result.items_matched
        run_record.claims_created = result.claims_created
        run_record.claims_deduplicated = result.claims_deduplicated
        run_record.artifact_items_seen = result.artifact_items_seen
        run_record.eu_entity_matches = result.eu_entity_matches
        run_record.leak_assertion_matches = result.leak_assertion_matches
        run_record.context_only_matches = result.context_only_matches
        run_record.primary_claim_candidates = result.primary_claim_candidates
        run_record.source_signals_created = result.signals_created
        run_record.item_errors_count = len(result.item_errors)
        run_record.item_errors = result.item_errors[:100]

    except Exception as e:
        result.error = str(e)
        source.last_error_at = datetime.now(timezone.utc)
        source.last_error = str(e)[:1000]
        source.consecutive_failures = (source.consecutive_failures or 0) + 1
        await repo.update_source_status(source, last_error_at=source.last_error_at, last_error=source.last_error, consecutive_failures=source.consecutive_failures)
        run_record.error = str(e)[:1000]
        run_record.success = False
        run_record.run_status = "failed"

    run_record.completed_at = datetime.now(timezone.utc)
    await run_repo.update_run(run_record)
    result.completed_at = run_record.completed_at
    return result


async def run_enabled_sources(db: AsyncSession, country_code: str | None = None, source_type: str | None = None) -> "BatchSourceRunResult":
    from dataclasses import dataclass
    @dataclass
    class B:
        results: list = None
        total_sources: int = 0
        successful: int = 0
        failed: int = 0
        def __init__(self):
            self.results = []
    batch = B()
    stmt = select(Source).where(Source.enabled.is_(True))
    if country_code:
        stmt = stmt.where(Source.country_code == country_code)
    if source_type:
        stmt = stmt.where(Source.source_type == source_type)
    sources = await db.execute(stmt)
    all_sources = list(sources.scalars().all())
    batch.total_sources = len(all_sources)
    for src in all_sources:
        try:
            sr = await run_source(src.id, db)
            batch.results.append(sr)
            if sr.success:
                batch.successful += 1
            else:
                batch.failed += 1
        except Exception:
            batch.failed += 1
    return batch
