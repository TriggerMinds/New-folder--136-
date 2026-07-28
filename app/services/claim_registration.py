from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.observed_leak_claim import ObservedLeakClaim
from app.database.models.observation import Observation
from app.repositories.claims import ClaimRepository
from app.repositories.observations import ObservationRepository
from app.services.audit import append_audit_event
from app.services.content_hashing import sha256_text
from app.services.url_normalization import normalize_url


class ClaimRegistrationResult:
    def __init__(
        self,
        claim: ObservedLeakClaim,
        observation: Observation,
        is_new: bool,
        dedup_type: str | None = None,
    ):
        self.claim = claim
        self.observation = observation
        self.is_new = is_new
        self.dedup_type = dedup_type


async def register_observed_leak_claim(
    session: AsyncSession,
    title_original: str,
    first_observed_url: str,
    *,
    source_language: str | None = None,
    summary: str | None = None,
    claim_text: str | None = None,
    countries: list[str] | None = None,
    eu_entities: list[str] | None = None,
    national_entities: list[str] | None = None,
    dossiers: list[str] | None = None,
    earliest_known_public_url: str | None = None,
    claimed_origin_url: str | None = None,
    confirmed_origin_url: str | None = None,
    title_translated: str | None = None,
    discovery_method: str = "manual",
    connector_type: str = "manual",
    connector_version: str = "0.1.0",
    http_status: int | None = None,
    content_excerpt: str | None = None,
    content_hash_sha256: str | None = None,
    observed_at: datetime | None = None,
    source_id: object | None = None,
    raw_metadata: dict | None = None,
) -> ClaimRegistrationResult:
    canonical_url = normalize_url(first_observed_url)
    host = urlparse(canonical_url).hostname or "unknown"

    if content_hash_sha256 is None and content_excerpt:
        content_hash_sha256 = sha256_text(content_excerpt)

    obs_repo = ObservationRepository(session)
    claim_repo = ClaimRepository(session)

    existing = await obs_repo.find_by_canonical_url(canonical_url)
    dedup_type = None
    if existing is not None:
        dedup_type = "canonical_url"
    else:
        if content_hash_sha256:
            existing = await obs_repo.find_by_content_hash(content_hash_sha256)
            if existing is not None:
                dedup_type = "content_hash"

    if existing is not None:
        claim = await claim_repo.get_claim(existing.claim_id)
        if claim is not None:
            claim.last_observed_at = observed_at or datetime.now()
            await claim_repo.update_claim(claim)
            return ClaimRegistrationResult(
                claim=claim,
                observation=existing,
                is_new=False,
                dedup_type=dedup_type,
            )

    claim = ObservedLeakClaim(
        title_original=title_original,
        title_translated=title_translated,
        source_language=source_language,
        summary=summary,
        claim_text=claim_text,
        countries=countries or [],
        eu_entities=eu_entities or [],
        national_entities=national_entities or [],
        dossiers=dossiers or [],
        first_observed_url=first_observed_url,
        first_observed_host=host,
        earliest_known_public_url=earliest_known_public_url,
        earliest_known_public_host=urlparse(earliest_known_public_url).hostname if earliest_known_public_url else None,
        claimed_origin_url=claimed_origin_url,
        claimed_origin_host=urlparse(claimed_origin_url).hostname if claimed_origin_url else None,
        confirmed_origin_url=confirmed_origin_url,
        confirmed_origin_host=urlparse(confirmed_origin_url).hostname if confirmed_origin_url else None,
        first_observed_at=observed_at or datetime.now(),
        last_observed_at=observed_at or datetime.now(),
    )
    await claim_repo.create_claim(claim)

    observation = Observation(
        claim_id=claim.id,
        source_id=source_id,
        observed_at=observed_at or datetime.now(),
        url=first_observed_url,
        canonical_url=canonical_url,
        host=host,
        http_status=http_status,
        title=title_original,
        content_excerpt=content_excerpt,
        content_hash_sha256=content_hash_sha256,
        discovery_method=discovery_method,
        connector_type=connector_type,
        connector_version=connector_version,
        raw_metadata=raw_metadata or {},
    )
    await obs_repo.create_observation(observation)

    await append_audit_event(
        session=session,
        event_type="claim_registered",
        actor="system",
        claim_id=claim.id,
        reason="Nieuwe observed_leak_claim geregistreerd via handmatige invoer",
    )

    return ClaimRegistrationResult(
        claim=claim,
        observation=observation,
        is_new=True,
    )
